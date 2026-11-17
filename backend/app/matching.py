"""Listing matching for a lead: hard filters from the profile, ranked by vector similarity.

If too few listings pass every filter, filters are relaxed one at a time in a fixed,
explainable order, and the relaxed ones are reported so the agent (and the
"why this?" view) can say so honestly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.embeddings import embed
from app.formatting import format_bhk, format_inr
from app.lead_summary import MUST_HAVE_LABELS
from app.models import ApprovalStatus, Lead, Listing, ListingStatus, PropertyType

# Relaxation order: least important first.
RELAX_ORDER = ("must_haves", "budget", "localities", "bedrooms", "property_type")
BUDGET_SLACK = 1.10  # allow 10% over the stated max before relaxing
BUDGET_RELAXED = 1.25


@dataclass
class MatchResult:
    listings: list[Listing]
    relaxed: list[str] = field(default_factory=list)


def profile_text(lead: Lead, query: str | None = None) -> str:
    """Text to embed for similarity: what the buyer asked for, in words."""
    ptype = lead.property_type.value if lead.property_type else None
    parts = [format_bhk(ptype, lead.bedrooms)]
    if lead.preferred_localities:
        parts.append("in " + ", ".join(lead.preferred_localities))
    if lead.soft_preferences:
        parts.append(lead.soft_preferences)
    if query:
        parts.append(query)
    return ". ".join(parts)


def _conditions(lead: Lead, relaxed: set[str]) -> list[Any]:
    conds: list[Any] = [
        Listing.approval_status == ApprovalStatus.approved,
        Listing.status == ListingStatus.available,
    ]
    if lead.property_type and "property_type" not in relaxed:
        conds.append(Listing.property_type == lead.property_type)
    if (
        lead.bedrooms
        and "bedrooms" not in relaxed
        and lead.property_type not in (PropertyType.plot_land, PropertyType.commercial)
    ):
        conds.append(Listing.bedrooms >= 4 if lead.bedrooms >= 4 else Listing.bedrooms == lead.bedrooms)
    if lead.budget_max:
        slack = BUDGET_RELAXED if "budget" in relaxed else BUDGET_SLACK
        conds.append(Listing.price_inr <= int(lead.budget_max * slack))
    if lead.budget_min and "budget" not in relaxed:
        conds.append(Listing.price_inr >= int(lead.budget_min * 0.8))
    if lead.preferred_localities and "localities" not in relaxed:
        conds.append(Listing.locality.in_(lead.preferred_localities))
    if "must_haves" not in relaxed:
        for key, wanted in (lead.must_haves or {}).items():
            if wanted and key in MUST_HAVE_LABELS:
                conds.append(getattr(Listing, key).is_(True))
    return conds


def find_matches(db: Session, lead: Lead, query: str | None = None, limit: int = 3) -> MatchResult:
    try:
        vec: list[float] | None = embed(profile_text(lead, query))
    except Exception:  # noqa: BLE001 - fall back to price ordering if the model is unavailable
        vec = None

    def run(relaxed: set[str]) -> list[Listing]:
        stmt = select(Listing).where(*_conditions(lead, relaxed)).options(selectinload(Listing.images))
        if vec is not None:
            stmt = stmt.order_by(Listing.embedding.cosine_distance(vec).nulls_last())
        else:
            stmt = stmt.order_by(Listing.price_inr.desc())
        return list(db.scalars(stmt.limit(limit)))

    relaxed: list[str] = []
    found = run(set())
    for step in RELAX_ORDER:
        if len(found) >= limit:
            break
        relaxed.append(step)
        more = run(set(relaxed))
        seen = {r.id for r in found}
        found += [r for r in more if r.id not in seen][: limit - len(found)]
    return MatchResult(listings=found[:limit], relaxed=[r for r in relaxed if _was_active(lead, r)])


def _was_active(lead: Lead, step: str) -> bool:
    """Only report a relaxation if the buyer had actually set that filter."""
    return {
        "must_haves": any((lead.must_haves or {}).values()),
        "budget": bool(lead.budget_max or lead.budget_min),
        "localities": bool(lead.preferred_localities),
        "bedrooms": bool(lead.bedrooms),
        "property_type": lead.property_type is not None,
    }[step]


def explain(lead: Lead, listing: Listing) -> tuple[str, dict[str, Any]]:
    """Short human reason + which of the buyer's filters this listing meets."""
    checks: dict[str, Any] = {}
    reasons: list[str] = []
    if lead.preferred_localities:
        checks["locality"] = listing.locality in lead.preferred_localities
    if lead.budget_max:
        checks["budget"] = listing.price_inr <= lead.budget_max
        if checks["budget"]:
            reasons.append(f"{format_inr(listing.price_inr)}, within budget")
        else:
            over = (listing.price_inr / lead.budget_max - 1) * 100
            reasons.append(f"{format_inr(listing.price_inr)}, about {over:.0f}% over budget")
    if lead.bedrooms and listing.bedrooms is not None:
        checks["bedrooms"] = listing.bedrooms == lead.bedrooms or (lead.bedrooms >= 4 and listing.bedrooms >= 4)
    for key, wanted in (lead.must_haves or {}).items():
        if wanted and key in MUST_HAVE_LABELS:
            checks[key] = bool(getattr(listing, key))
            if checks[key]:
                reasons.append(MUST_HAVE_LABELS[key])
    ptype = listing.property_type.value
    head = f"{format_bhk(ptype, listing.bedrooms)} in {listing.locality}"
    missed = [k for k, v in checks.items() if v is False]
    text = head + (": " + "; ".join(reasons) if reasons else "")
    if missed:
        text += f" (doesn't meet: {', '.join(m.replace('_', ' ') for m in missed)})"
    return text, checks
