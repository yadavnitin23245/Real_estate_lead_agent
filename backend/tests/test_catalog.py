from collections import Counter

import pytest

from seed.catalog import LOCALITIES, generate_catalog, generate_pending

CATALOG = generate_catalog()


def test_catalog_size_and_mix() -> None:
    assert len(CATALOG) == 200
    types = Counter(s.property_type for s in CATALOG)
    assert types["plot_land"] == 20
    assert types["apartment"] >= 140
    assert types["house"] > 0 and types["villa"] > 0 and types["commercial"] > 0
    assert {s.bedrooms for s in CATALOG if s.property_type == "apartment"} == {1, 2, 3, 4}


def test_all_twelve_localities_balanced() -> None:
    per_loc = Counter(s.locality for s in CATALOG)
    assert set(per_loc) == {loc.name for loc in LOCALITIES}
    assert min(per_loc.values()) >= 12


def test_about_ten_percent_sold() -> None:
    assert sum(s.status == "sold" for s in CATALOG) == 20


def test_deterministic_and_unique() -> None:
    again = generate_catalog()
    assert [s.ref_code for s in again] == [s.ref_code for s in CATALOG]
    assert [s.description for s in again] == [s.description for s in CATALOG]
    assert len({s.ref_code for s in CATALOG}) == 200
    assert len({s.description for s in CATALOG}) == 200


@pytest.mark.parametrize("spec", CATALOG + generate_pending(), ids=lambda s: s.ref_code)
def test_listing_invariants(spec) -> None:
    assert spec.price_inr > 0 and spec.area_value > 0
    sentences = [x for x in spec.description.split(". ") if x]
    assert 3 <= len(sentences) <= 5, spec.description
    assert "None" not in spec.title + spec.description
    assert 1 <= len(spec.images) <= 3
    if spec.property_type == "plot_land":
        assert spec.bedrooms is None and spec.bathrooms is None
    # text must not contradict the boolean columns
    text = spec.description.lower()
    assert ("metro" in text) == spec.near_metro
    assert ("school" in text) == spec.near_school
    # eval ground-truth tags must reflect what the text actually says
    if "near_hospital" in spec.tags:
        assert "hospital" in text
    if "near_market" in spec.tags:
        assert "market" in text
    if "quiet" in spec.tags:
        assert any(w in text for w in ("quiet", "peaceful", "calm", "serene"))


def test_price_ranges_are_realistic() -> None:
    for s in CATALOG:
        if s.property_type == "apartment":
            assert 25_00_000 <= s.price_inr <= 6_00_00_000, (s.ref_code, s.price_inr)
    kp = [s.price_inr / s.area_value for s in CATALOG if s.locality == "Koregaon Park" and s.property_type == "apartment"]
    hd = [s.price_inr / s.area_value for s in CATALOG if s.locality == "Hadapsar" and s.property_type == "apartment"]
    assert min(kp) > max(hd)  # premium locality is pricier per sq ft


def test_pending_listings() -> None:
    pending = generate_pending()
    assert len(pending) == 5
    assert all(s.ref_code.startswith("GK-PND-") for s in pending)
