import pytest
from pathlib import Path
from engine.data_loader import load_all_data
from engine.performance_model import apply_odds_calibration
from engine.monte_carlo import run_simulation
from engine.aggregator import aggregate_results
from engine.models import StageType

DATA_DIR = Path("data")

@pytest.fixture
def sim_results():
    riders, stages, odds, _, _ = load_all_data(DATA_DIR)
    apply_odds_calibration(riders, odds, "gc_win", StageType.MOUNTAIN)
    iterations = run_simulation(riders, stages, n_iterations=200, seed=42)
    return riders, stages, iterations

def test_gc_win_pct_sums_to_one(sim_results):
    riders, stages, iterations = sim_results
    results = aggregate_results(riders, stages, iterations)
    total = sum(r.win_pct for r in results.gc)
    assert abs(total - 1.0) < 0.01

def test_all_active_riders_in_gc(sim_results):
    riders, stages, iterations = sim_results
    results = aggregate_results(riders, stages, iterations)
    active_ids = {rid for rid, rs in riders.items() if rs.is_active()}
    result_ids = {r.rider_id for r in results.gc}
    assert active_ids == result_ids

def test_gc_decimal_odds_reflect_probability(sim_results):
    riders, stages, iterations = sim_results
    results = aggregate_results(riders, stages, iterations)
    for r in results.gc:
        if r.win_pct > 0:
            expected = round(1.0 / r.win_pct, 2)
            assert r.decimal_odds == pytest.approx(expected, rel=0.01)

def test_stage_wins_has_correct_stage_count(sim_results):
    riders, stages, iterations = sim_results
    results = aggregate_results(riders, stages, iterations)
    assert len(results.stages) == len(stages)

def test_young_rider_only_eligible_riders(sim_results):
    riders, stages, iterations = sim_results
    # Ensure at least one rider is eligible
    riders[1].rider.young_rider_eligible = True
    results = aggregate_results(riders, stages, iterations)
    eligible_ids = {rid for rid, rs in riders.items() if rs.rider.young_rider_eligible}
    result_ids = {r.rider_id for r in results.young_rider}
    assert result_ids == eligible_ids
    assert all(r.rider_id in eligible_ids for r in results.young_rider)
    winner = max(results.young_rider, key=lambda r: r.win_pct)
    assert winner.rider_id in eligible_ids
