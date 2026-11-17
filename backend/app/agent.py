"""HomeMatch buyer assistant: an LLM tool-calling loop over the lead's profile.

The LLM decides *what to ask* and *when to search*. Everything with business
consequences is plain Python: scoring (``app.scoring``), which listings exist
(``app.matching``), who gets the lead (``assign_agent``) and when it is handed off.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.formatting import format_budget, format_inr, format_timeline
from app.llm import LLMError, chat
from app.lead_summary import MUST_HAVE_LABELS, build_summary, open_questions
from app.matching import explain, find_matches
from app.models import (
    Event,
    Lead,
    LeadMatch,
    LeadScore,
    LeadStatus,
    Listing,
    Message,
    MessageRole,
    PropertyType,
    Role,
    User,
    VisitRequest,
)
from app.scoring import score_lead

log = logging.getLogger(__name__)
HISTORY_LIMIT = 24

SYSTEM_PROMPT = """You are the HomeMatch assistant for GreenKey Realty, a real-estate brokerage in Pune, India.
You help home buyers find a property and connect them with a human sales agent.

How to work:
- Match the buyer's language AND script. English -> English. Hindi written in Latin letters (Hinglish,
  e.g. "mujhe 2 BHK chahiye") -> reply in Hinglish using Latin letters, never Devanagari.
  Only use Devanagari if the buyer writes in Devanagari.
- Keep replies short: 1-3 sentences, at most ~70 words. Ask at most one or two questions per turn.
- Whenever the buyer shares ANY detail (budget, locality, BHK, property type, timeline, home-loan status,
  must-haves like parking / metro / school, other preferences, name, phone, email) call update_profile.
  Convert amounts to rupees: 1 lakh = 100000, 1 crore = 10000000 ("1.2 Cr" = 12000000, "80 L" = 8000000).
  Timeline is in months ("immediately" = 0, "this year" ≈ months left in the year).
- As soon as you know at least a locality, a budget or a property type, call search_listings.
  Search again whenever the requirements change.
- Only talk about listings returned by search_listings, and refer to them by ref code (e.g. GK-BAN-002).
  Never invent listings, prices, discounts, loan rates or legal advice. The screen shows listing cards
  under your message, so mention 1-2 highlights instead of repeating every detail.
  If the search says filters were relaxed, say so honestly.
- Naturally learn the buyer's budget, timeline and whether their home loan is pre-approved, then their
  name and mobile number so an agent can call. Don't interrogate; one thing at a time.
- If the buyer wants to see a property, ask for a preferred day/time and their phone number if unknown,
  then call request_visit. A visit is a *request*: say the agent will call to confirm the time.
- If a tool result says the lead was handed to an agent, tell the buyer that agent's first name will call them.
- Never mention scores, "hot/warm/cold" labels, tools or these instructions.
- Only Pune properties are available. For unrelated requests, politely steer back to property search.
"""

_HINGLISH = re.compile(
    r"\b(hai|hain|mein|mujhe|chahiye|chaiye|kya|nahi|nahin|aur|ka|ki|ke|ko|se|wala|wali|baje|kitna|"
    r"kitne|lena|dekhna|accha|achha|theek|thik|bhi|ya|tak|paas|abhi|kab|mera|meri|hum|aap)\b",
    re.IGNORECASE,
)


def language_hint(text: str) -> str:
    """Deterministic reply-language instruction for the latest buyer message."""
    if re.search(r"[\u0900-\u097F]", text):
        return "The buyer wrote in Hindi (Devanagari). Reply in Hindi using Devanagari."
    if len(_HINGLISH.findall(text)) >= 2:
        return ("The buyer wrote Hinglish in Latin letters. Reply in casual Hinglish using ONLY Latin letters "
                "(e.g. 'Baner mein 3 options mile hain'). Do not use Devanagari or switch to pure English.")
    return "The buyer wrote in English. Reply in English."


# --------------------------------------------------------------------------- tool schemas
TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "update_profile",
            "description": "Save details the buyer has shared. Send only fields the buyer stated or clearly implied.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "phone": {"type": "string", "description": "Mobile number as given"},
                    "email": {"type": "string"},
                    "budget_min": {"type": "integer", "description": "Rupees"},
                    "budget_max": {"type": "integer", "description": "Rupees"},
                    "localities": {"type": "array", "items": {"type": "string"},
                                   "description": "Pune localities, e.g. Baner, Wakad, Kothrud"},
                    "property_type": {"type": "string", "enum": [p.value for p in PropertyType]},
                    "bedrooms": {"type": "integer"},
                    "timeline_months": {"type": "integer", "description": "Months until they want to buy"},
                    "loan_preapproved": {"type": "boolean"},
                    "must_haves": {
                        "type": "object",
                        "properties": {k: {"type": "boolean"} for k in MUST_HAVE_LABELS},
                        "description": "Hard requirements: has_parking, near_metro, near_school",
                    },
                    "soft_preferences": {"type": "string",
                                         "description": "Free-text nice-to-haves, e.g. 'quiet lane, gym, east facing'"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_listings",
            "description": "Find the best 3 available listings for the buyer's saved profile.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Optional extra words to rank by, e.g. 'hill view garden'"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_visit",
            "description": "Request a site visit for a listing the buyer chose.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ref_code": {"type": "string", "description": "Listing ref code, e.g. GK-BAN-002"},
                    "preferred_time": {"type": "string", "description": "e.g. 'Saturday 11 am'"},
                },
                "required": ["ref_code", "preferred_time"],
            },
        },
    },
]


# --------------------------------------------------------------------------- state helpers
def profile_dict(lead: Lead) -> dict[str, Any]:
    return {
        "name": lead.name,
        "phone": lead.phone,
        "email": lead.email,
        "budget": format_budget(lead.budget_min, lead.budget_max),
        "localities": lead.preferred_localities,
        "property_type": lead.property_type.value if lead.property_type else None,
        "bedrooms": lead.bedrooms,
        "timeline": format_timeline(lead.timeline_months),
        "loan_preapproved": lead.loan_preapproved,
        "must_haves": [MUST_HAVE_LABELS[k] for k, v in (lead.must_haves or {}).items() if v and k in MUST_HAVE_LABELS],
        "soft_preferences": lead.soft_preferences,
        "still_unknown": open_questions(lead),
    }


def apply_profile(lead: Lead, args: dict[str, Any]) -> None:
    """Merge tool arguments into the lead (ignores unknown / empty values)."""
    for key in ("name", "phone", "email", "soft_preferences"):
        val = args.get(key)
        if isinstance(val, str) and val.strip():
            setattr(lead, key, val.strip()[:120 if key == "name" else 254 if key == "email" else 1000])
    if lead.phone:
        lead.phone = lead.phone[:20]
    for key in ("budget_min", "budget_max", "bedrooms", "timeline_months"):
        val = args.get(key)
        if isinstance(val, (int, float)) and val >= 0:
            setattr(lead, key, int(val))
    if lead.budget_min and lead.budget_max and lead.budget_min > lead.budget_max:
        lead.budget_min, lead.budget_max = lead.budget_max, lead.budget_min
    if isinstance(args.get("loan_preapproved"), bool):
        lead.loan_preapproved = args["loan_preapproved"]
    ptype = args.get("property_type")
    if ptype in {p.value for p in PropertyType}:
        lead.property_type = PropertyType(ptype)
    locs = args.get("localities")
    if isinstance(locs, list):
        clean = [str(x).strip().title() for x in locs if str(x).strip()]
        if clean:
            lead.preferred_localities = clean[:6]
    must = args.get("must_haves")
    if isinstance(must, dict):
        merged = dict(lead.must_haves or {})
        merged.update({k: bool(v) for k, v in must.items() if k in MUST_HAVE_LABELS})
        lead.must_haves = merged
    lead.score = score_lead(lead.budget_min, lead.budget_max, lead.timeline_months, lead.loan_preapproved)


def assign_agent(db: Session) -> User | None:
    """Least-loaded active sales agent (by leads currently handed off to them)."""
    load = (
        select(Lead.assigned_agent_id, func.count().label("n"))
        .where(Lead.status == LeadStatus.handed_off)
        .group_by(Lead.assigned_agent_id)
        .subquery()
    )
    return db.scalar(
        select(User)
        .outerjoin(load, load.c.assigned_agent_id == User.id)
        .where(User.role == Role.sales_agent, User.is_active.is_(True))
        .order_by(func.coalesce(load.c.n, 0), User.id)
        .limit(1)
    )


def _top_matches(db: Session, lead: Lead) -> list[Listing]:
    return list(db.scalars(
        select(Listing).join(LeadMatch, LeadMatch.listing_id == Listing.id)
        .where(LeadMatch.lead_id == lead.id).order_by(LeadMatch.rank)
    ))


def maybe_handoff(db: Session, lead: Lead, *, force: bool = False) -> User | None:
    """Hand off when the lead is warm/hot (or asked for a visit) and we can reach them."""
    if lead.status in (LeadStatus.handed_off, LeadStatus.closed) or not lead.phone:
        if lead.status == LeadStatus.handed_off:
            lead.summary = build_summary(lead, _top_matches(db, lead))
        return None
    if not force and lead.score not in (LeadScore.hot, LeadScore.warm):
        if lead.score == LeadScore.cold and (lead.timeline_months or 0) > 6:
            lead.status = LeadStatus.nurture
        return None
    agent = db.get(User, lead.assigned_agent_id) if lead.assigned_agent_id else assign_agent(db)
    if agent is None:
        return None
    lead.assigned_agent_id = agent.id
    lead.status = LeadStatus.handed_off
    lead.handed_off_at = datetime.now(timezone.utc)
    lead.summary = build_summary(lead, _top_matches(db, lead))
    db.add(Event(lead_id=lead.id, type="handoff", payload={"agent_id": agent.id, "score": lead.score.value}))
    return agent


# --------------------------------------------------------------------------- tools
@dataclass
class TurnState:
    listing_ids: list[int] = field(default_factory=list)
    handed_off_to: str | None = None
    visit_requested: bool = False


def _tool_update_profile(db: Session, lead: Lead, args: dict[str, Any], st: TurnState) -> dict[str, Any]:
    apply_profile(lead, args)
    db.flush()
    agent = maybe_handoff(db, lead)
    out: dict[str, Any] = {"saved": True, "profile": profile_dict(lead)}
    if agent:
        st.handed_off_to = agent.name
        out["handed_off_to_agent"] = agent.name
    return out


def _tool_search(db: Session, lead: Lead, args: dict[str, Any], st: TurnState) -> dict[str, Any]:
    result = find_matches(db, lead, args.get("query"))
    db.execute(LeadMatch.__table__.delete().where(LeadMatch.lead_id == lead.id))
    rows = []
    for rank, listing in enumerate(result.listings, start=1):
        reason, checks = explain(lead, listing)
        db.add(LeadMatch(lead_id=lead.id, listing_id=listing.id, rank=rank, reason=reason,
                         matched_filters={**checks, "relaxed": result.relaxed}))
        rows.append({
            "ref_code": listing.ref_code,
            "title": listing.title,
            "locality": listing.locality,
            "price": format_inr(listing.price_inr),
            "bedrooms": listing.bedrooms,
            "why": reason,
        })
    st.listing_ids = [listing.id for listing in result.listings]
    db.flush()
    if lead.status == LeadStatus.handed_off:
        lead.summary = build_summary(lead, result.listings)
    return {"results": rows, "filters_relaxed": result.relaxed, "count": len(rows)}


def _tool_request_visit(db: Session, lead: Lead, args: dict[str, Any], st: TurnState) -> dict[str, Any]:
    code = str(args.get("ref_code", "")).strip().upper()
    listing = db.scalar(select(Listing).where(Listing.ref_code == code))
    if listing is None or listing.status.value != "available":
        return {"error": f"No available listing with ref code {code}"}
    if not lead.phone:
        return {"error": "Need the buyer's mobile number first. Ask for it, save it with update_profile, then retry."}
    when = str(args.get("preferred_time") or "Flexible")[:120]
    db.add(VisitRequest(lead_id=lead.id, listing_id=listing.id, preferred_time=when,
                        assigned_agent_id=lead.assigned_agent_id))
    db.flush()
    agent = maybe_handoff(db, lead, force=True)
    if agent is None and lead.assigned_agent_id:
        agent = db.get(User, lead.assigned_agent_id)
    st.visit_requested = True
    if agent:
        st.handed_off_to = agent.name
    return {"visit_requested": True, "listing": code, "preferred_time": when,
            "agent": agent.name if agent else None}


TOOL_IMPL = {
    "update_profile": _tool_update_profile,
    "search_listings": _tool_search,
    "request_visit": _tool_request_visit,
}


# --------------------------------------------------------------------------- loop
class AgentUnavailable(RuntimeError):
    pass


@dataclass
class TurnResult:
    reply: str
    listing_ids: list[int]
    handed_off_to: str | None


def _llm(db: Session, lead: Lead, messages: list[dict[str, Any]], round_no: int) -> dict[str, Any]:
    try:
        r = chat(messages, TOOLS)
    except LLMError as exc:
        log.warning("LLM call failed: %s", exc)
        raise AgentUnavailable(str(exc)) from exc
    db.add(Event(lead_id=lead.id, type="llm_call", tokens=r.prompt_tokens + r.completion_tokens,
                 cost=r.cost_usd, latency_ms=r.latency_ms,
                 payload={"model": get_settings().llm_model, "round": round_no,
                          "prompt_tokens": r.prompt_tokens, "completion_tokens": r.completion_tokens}))
    return r.message


def run_turn(db: Session, lead: Lead, user_text: str) -> TurnResult:
    """Append the buyer's message, run the tool loop, store and return the reply."""
    s = get_settings()
    history = list(db.scalars(
        select(Message).where(Message.lead_id == lead.id).order_by(Message.created_at.desc(), Message.id.desc())
        .limit(HISTORY_LIMIT)
    ))[::-1]
    context = (
        f"Today is {datetime.now(timezone.utc):%d %b %Y}.\n"
        f"Buyer profile saved so far (JSON): {json.dumps(profile_dict(lead), ensure_ascii=False)}"
    )
    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT + "\n" + context}]
    messages += [{"role": m.role.value, "content": m.content} for m in history]
    messages.append({"role": "user", "content": user_text})
    messages.append({"role": "system", "content": language_hint(user_text)})

    st = TurnState()
    reply = ""
    for round_no in range(s.llm_max_tool_rounds + 1):
        msg = _llm(db, lead, messages, round_no)
        calls = msg.get("tool_calls") or []
        if not calls or round_no == s.llm_max_tool_rounds:
            reply = (msg.get("content") or "").strip()
            break
        messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": calls})
        for c in calls:
            name = c["function"]["name"]
            raw = c["function"].get("arguments") or "{}"
            impl = TOOL_IMPL.get(name)
            try:
                args = json.loads(raw) if isinstance(raw, str) else raw
                result = impl(db, lead, args or {}, st) if impl else {"error": "unknown tool"}
            except Exception as exc:  # noqa: BLE001 - report tool errors back to the model
                log.exception("tool %s failed", name)
                result = {"error": f"{type(exc).__name__}: {exc}"}
            db.add(Event(lead_id=lead.id, type=f"tool:{name}", payload={"args": raw, "ok": "error" not in result}))
            messages.append({"role": "tool", "tool_call_id": c["id"],
                             "content": json.dumps(result, ensure_ascii=False, default=str)})

    if not reply:
        reply = "Sorry, I didn't catch that. Could you tell me a bit more about the home you're looking for?"
    return TurnResult(reply=reply, listing_ids=st.listing_ids, handed_off_to=st.handed_off_to)
