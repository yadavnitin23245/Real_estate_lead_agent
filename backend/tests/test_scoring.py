import pytest

from app.models import LeadScore
from app.scoring import score_lead

L = 100_000


@pytest.mark.parametrize(
    ("bmin", "bmax", "timeline", "loan", "expected"),
    [
        (50 * L, 80 * L, 3, True, LeadScore.hot),
        (None, 80 * L, 1, True, LeadScore.hot),
        (50 * L, None, 0, True, LeadScore.hot),
        (50 * L, 80 * L, 3, False, LeadScore.warm),
        (50 * L, 80 * L, 3, None, LeadScore.warm),
        (50 * L, 80 * L, 4, True, LeadScore.warm),
        (50 * L, 80 * L, 6, False, LeadScore.warm),
        (50 * L, 80 * L, 7, True, LeadScore.cold),
        (50 * L, 80 * L, None, True, LeadScore.cold),
        (None, None, 1, True, LeadScore.cold),
        (None, None, None, None, LeadScore.cold),
    ],
)
def test_score_rules(bmin, bmax, timeline, loan, expected) -> None:
    assert score_lead(bmin, bmax, timeline, loan) == expected
