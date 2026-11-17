"""Pure-Python parts of the buyer assistant (no DB, no LLM)."""

from app.agent import apply_profile, language_hint, profile_dict
from app.matching import RELAX_ORDER, _was_active, explain, profile_text
from app.models import Lead, LeadScore, Listing, ListingStatus, PropertyType


def _lead(**kw) -> Lead:
    base = dict(preferred_localities=[], must_haves={}, score=LeadScore.cold)
    base.update(kw)
    return Lead(**base)


def test_language_hint() -> None:
    assert "Hinglish" in language_hint("Baner mein 3 BHK chahiye")
    assert "Devanagari" in language_hint("मुझे घर चाहिए")
    assert "English" in language_hint("Looking for a villa in Bavdhan")
    assert "English" in language_hint("Saturday 11 am works")


def test_apply_profile_merges_and_scores() -> None:
    lead = _lead()
    apply_profile(lead, {"localities": ["baner", " aundh "], "bedrooms": 3, "property_type": "apartment"})
    assert lead.preferred_localities == ["Baner", "Aundh"]
    assert lead.score == LeadScore.cold  # no budget / timeline yet

    apply_profile(lead, {"budget_min": 16_000_000, "budget_max": 12_000_000,
                         "timeline_months": 2, "loan_preapproved": True})
    assert (lead.budget_min, lead.budget_max) == (12_000_000, 16_000_000)  # swapped
    assert lead.score == LeadScore.hot

    apply_profile(lead, {"must_haves": {"near_school": True, "bogus": True}})
    apply_profile(lead, {"must_haves": {"has_parking": True}})
    assert lead.must_haves == {"near_school": True, "has_parking": True}


def test_apply_profile_ignores_bad_values() -> None:
    lead = _lead(bedrooms=2)
    apply_profile(lead, {"bedrooms": -1, "property_type": "castle", "name": "  ", "localities": []})
    assert lead.bedrooms == 2 and lead.property_type is None and lead.name is None
    assert lead.preferred_localities == []


def test_profile_dict_lists_open_questions() -> None:
    d = profile_dict(_lead())
    assert "Budget range" in d["still_unknown"]
    assert d["budget"] == "not shared yet"


def test_explain_flags_budget_and_must_haves() -> None:
    lead = _lead(budget_max=10_000_000, bedrooms=2, preferred_localities=["Wakad"], must_haves={"near_metro": True})
    listing = Listing(ref_code="GK-WAK-001", title="t", city="Pune", locality="Wakad",
                      property_type=PropertyType.apartment, bedrooms=2, price_inr=11_000_000,
                      near_metro=False, has_parking=True, near_school=False, status=ListingStatus.available)
    text, checks = explain(lead, listing)
    assert checks == {"locality": True, "budget": False, "bedrooms": True, "near_metro": False}
    assert "10% over budget" in text and "doesn't meet" in text


def test_relaxations_only_reported_when_set() -> None:
    lead = _lead(budget_max=5_000_000)
    assert [s for s in RELAX_ORDER if _was_active(lead, s)] == ["budget"]
    assert "2 BHK" in profile_text(_lead(bedrooms=2, property_type=PropertyType.apartment))
