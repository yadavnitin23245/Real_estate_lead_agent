from app.formatting import format_budget, format_inr


def test_format_inr() -> None:
    assert format_inr(1_45_00_000) == "₹1.45 Cr"
    assert format_inr(1_00_00_000) == "₹1 Cr"
    assert format_inr(85_00_000) == "₹85 L"
    assert format_inr(62_50_000) == "₹62.5 L"
    assert format_inr(95_000) == "₹95,000"


def test_format_budget() -> None:
    assert format_budget(50_00_000, 80_00_000) == "₹50 L - ₹80 L"
    assert format_budget(None, 1_20_00_000) == "up to ₹1.2 Cr"
    assert format_budget(None, None) == "not shared yet"
