import pytest
import numpy as np
from engine.models import RiderState, Rider, StageType
from engine.time_gaps import generate_time_gaps


def make_rider(rid, climbing=50, tt=50):
    r = Rider(rid, f"R{rid}", "T", "X", 1998, 10, False)
    return RiderState(rider=r, sprint=50, climbing=climbing, tt=tt, gc=50)


def test_flat_stage_gaps_are_zero():
    riders = {i: make_rider(i) for i in range(1, 6)}
    rng = np.random.default_rng(42)
    gaps = generate_time_gaps(riders, StageType.FLAT, winner_id=1, rng=rng)
    assert all(v == 0.0 for v in gaps.values())


def test_mountain_gaps_are_positive():
    riders = {i: make_rider(i, climbing=70) for i in range(1, 6)}
    rng = np.random.default_rng(42)
    gaps = generate_time_gaps(riders, StageType.MOUNTAIN, winner_id=1, rng=rng)
    assert gaps[1] == 0.0
    assert all(v >= 0.0 for v in gaps.values())


def test_higher_climber_gets_smaller_gap_on_average():
    n_trials = 500
    rng = np.random.default_rng(0)
    good_gaps, poor_gaps = [], []
    for _ in range(n_trials):
        riders = {
            1: make_rider(1, climbing=95),
            2: make_rider(2, climbing=40),
        }
        gaps = generate_time_gaps(riders, StageType.MOUNTAIN, winner_id=1, rng=rng)
        good_gaps.append(gaps[1])
        poor_gaps.append(gaps[2])
    assert np.mean(poor_gaps) > np.mean(good_gaps)


def test_tt_gaps_positive_for_non_winner():
    riders = {i: make_rider(i, tt=70) for i in range(1, 4)}
    rng = np.random.default_rng(1)
    gaps = generate_time_gaps(riders, StageType.TT, winner_id=1, rng=rng)
    assert gaps[1] == 0.0
    assert gaps[2] > 0.0
