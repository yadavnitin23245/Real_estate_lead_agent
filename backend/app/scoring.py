"""Lead scoring: plain, auditable Python rules (never the LLM).

hot  = budget known + timeline <= 3 months + loan pre-approved
warm = budget known + timeline <= 6 months
cold = everything else
"""

from app.models import LeadScore


def score_lead(
    budget_min: int | None,
    budget_max: int | None,
    timeline_months: int | None,
    loan_preapproved: bool | None,
) -> LeadScore:
    budget_known = budget_min is not None or budget_max is not None
    if not budget_known or timeline_months is None:
        return LeadScore.cold
    if timeline_months <= 3 and loan_preapproved is True:
        return LeadScore.hot
    if timeline_months <= 6:
        return LeadScore.warm
    return LeadScore.cold
