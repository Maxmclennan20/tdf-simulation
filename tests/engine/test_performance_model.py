import pytest
from engine.models import RiderState, Rider, StageType
from engine.performance_model import compute_stage_weights, apply_odds_calibration


def make_rider(rid: int, sprint=50, climbing=50, tt=50, gc=50) -> RiderState:
    r = Rider(rid, f"Rider{rid}", "Team", "GBR", 1998, 10, False)
    return RiderState(rider=r, sprint=sprint, climbing=climbing, tt=tt, gc=gc)


def test_weights_sum_to_one():
    riders = {i: make_rider(i) for i in range(1, 6)}
    weights = compute_stage_weights(riders, StageType.MOUNTAIN)
    assert abs(sum(weights.values()) - 1.0) < 1e-9


def test_better_climber_higher_weight_on_mountain():
    riders = {
        1: make_rider(1, climbing=90, gc=85),
        2: make_rider(2, climbing=40, gc=40),
    }
    weights = compute_stage_weights(riders, StageType.MOUNTAIN)
    assert weights[1] > weights[2]


def test_dns_rider_excluded():
    riders = {
        1: make_rider(1, climbing=90),
        2: make_rider(2, climbing=50),
    }
    riders[2].dns = True
    weights = compute_stage_weights(riders, StageType.MOUNTAIN)
    assert 2 not in weights
    assert abs(sum(weights.values()) - 1.0) < 1e-9


def test_form_multiplier_applied():
    riders = {
        1: make_rider(1, climbing=80),
        2: make_rider(2, climbing=80),
    }
    riders[1].form = 1.5
    riders[2].form = 0.5
    weights = compute_stage_weights(riders, StageType.MOUNTAIN)
    assert weights[1] > weights[2]


def test_calibration_shifts_probabilities():
    riders = {i: make_rider(i, climbing=80, gc=75) for i in range(1, 6)}
    # Rider 1 gets odds implying 60% win probability
    odds = {1: {"gc_win": 1.667}}
    apply_odds_calibration(riders, odds, market="gc_win",
                           stage_type=StageType.MOUNTAIN)
    weights_after = compute_stage_weights(riders, StageType.MOUNTAIN)
    # Rider 1 should now dominate
    assert weights_after[1] > 0.5


def test_no_odds_calibration_factor_is_one():
    riders = {1: make_rider(1)}
    apply_odds_calibration(riders, {}, market="gc_win",
                           stage_type=StageType.MOUNTAIN)
    assert riders[1].calibration_factor == pytest.approx(1.0)
