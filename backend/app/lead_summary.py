"""Hand-off summary for sales agents. Built from stored facts only (no LLM)."""

from __future__ import annotations

from app.formatting import format_bhk, format_budget, format_inr, format_timeline
from app.models import Lead, Listing

MUST_HAVE_LABELS = {
    "has_parking": "car parking",
    "near_school": "near a school",
    "near_metro": "near metro",
}


def open_questions(lead: Lead) -> list[str]:
    qs: list[str] = []
    if lead.budget_min is None and lead.budget_max is None:
        qs.append("Budget range")
    if lead.timeline_months is None:
        qs.append("Purchase timeline")
    if lead.loan_preapproved is None:
        qs.append("Home-loan status")
    if not lead.preferred_localities:
        qs.append("Preferred localities")
    if lead.property_type in (None, "apartment", "house", "villa") and lead.bedrooms is None:
        qs.append("Number of bedrooms")
    if not lead.phone:
        qs.append("Best phone number / time to call")
    return qs


def build_summary(lead: Lead, top_matches: list[Listing]) -> str:
    ptype = lead.property_type.value if lead.property_type else None
    where = ", ".join(lead.preferred_localities) or (lead.city or "Pune")
    needs = f"{format_bhk(ptype, lead.bedrooms)} in {where}"
    must = [MUST_HAVE_LABELS[k] for k, v in (lead.must_haves or {}).items() if v and k in MUST_HAVE_LABELS]
    if must:
        needs += f"; must have {', '.join(must)}"
    if lead.soft_preferences:
        needs += f"; prefers {lead.soft_preferences}"

    loan = {True: "pre-approved", False: "not pre-approved"}.get(lead.loan_preapproved, "unknown")  # type: ignore[arg-type]
    lines = [
        f"Needs: {needs}.",
        f"Budget: {format_budget(lead.budget_min, lead.budget_max)}. "
        f"Timeline: {format_timeline(lead.timeline_months)}. Loan: {loan}.",
    ]
    if top_matches:
        lines.append("Top matches:")
        lines += [
            f"  {i}. {m.ref_code} - {m.title}, {format_inr(m.price_inr)}"
            for i, m in enumerate(top_matches[:3], start=1)
        ]
    else:
        lines.append("Top matches: none found yet.")
    qs = open_questions(lead)
    lines.append(f"Open questions: {', '.join(qs) if qs else 'none'}.")
    return "\n".join(lines)
