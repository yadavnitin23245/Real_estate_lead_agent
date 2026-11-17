"""Small display helpers shared by the agent, summaries and seed."""

from __future__ import annotations


def format_inr(amount: int | float | None) -> str:
    """1_45_00_000 -> '₹1.45 Cr', 85_00_000 -> '₹85 L', 95_000 -> '₹95,000'."""
    if amount is None:
        return "-"
    a = float(amount)
    if a >= 1e7:
        return f"₹{a / 1e7:.2f}".rstrip("0").rstrip(".") + " Cr"
    if a >= 1e5:
        return f"₹{a / 1e5:.1f}".rstrip("0").rstrip(".") + " L"
    return f"₹{int(a):,}"


def format_budget(budget_min: int | None, budget_max: int | None) -> str:
    if budget_min and budget_max:
        return f"{format_inr(budget_min)} - {format_inr(budget_max)}"
    if budget_max:
        return f"up to {format_inr(budget_max)}"
    if budget_min:
        return f"from {format_inr(budget_min)}"
    return "not shared yet"


def format_timeline(months: int | None) -> str:
    if months is None:
        return "not shared yet"
    if months <= 0:
        return "immediately"
    return f"within {months} month{'s' if months != 1 else ''}"


def format_bhk(property_type: str | None, bedrooms: int | None) -> str:
    label = {
        "apartment": "apartment",
        "house": "independent house",
        "villa": "villa",
        "plot_land": "plot",
        "commercial": "commercial space",
    }.get(property_type or "", "property")
    if bedrooms and property_type not in {"plot_land", "commercial"}:
        return f"{bedrooms} BHK {label}"
    return label
