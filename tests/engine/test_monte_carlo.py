"""Tests for engine/monte_carlo.py — written TDD-first."""
from __future__ import annotations
import copy
from pathlib import Path

import pytest

from engine.data_loader import load_all_data
from engine.monte_carlo import run_simulation


@pytest.fixture(scope="module")
def sim_data():
    riders, stages, odds, hist, cf = load_all_data(Path("data"))
    return riders, stages


def test_run_simulation_returns_correct_iteration_count(sim_data):
    riders, stages = sim_data
    results = run_simulation(riders, stages, n_iterations=10, seed=1)
    assert len(results) == 10


def test_each_iteration_has_21_stage_results(sim_data):
    riders, stages = sim_data
    results = run_simulation(riders, stages, n_iterations=10, seed=2)
    for iteration in results:
        assert len(iteration.stage_results) == 21


def test_stage_winner_is_active_rider(sim_data):
    riders, stages = sim_data
    results = run_simulation(riders, stages, n_iterations=10, seed=3)
    for iteration in results:
        for stage_result in iteration.stage_results:
            winner_id = stage_result.winner_id
            assert winner_id in riders
            assert riders[winner_id].is_active(), (
                f"Winner {winner_id} is DNS/DNF but won a stage"
            )


def test_all_riders_have_gc_times(sim_data):
    riders, stages = sim_data
    results = run_simulation(riders, stages, n_iterations=10, seed=4)
    rider_ids = set(riders.keys())
    for iteration in results:
        assert set(iteration.gc_times.keys()) == rider_ids, (
            "gc_times must contain an entry for every rider"
        )


def test_dns_rider_never_wins_gc(sim_data):
    riders, stages = sim_data
    # Deep-copy so we don't mutate the shared fixture
    riders_copy = copy.deepcopy(riders)
    # Mark the first rider as DNS
    dns_rider_id = next(iter(riders_copy))
    riders_copy[dns_rider_id].dns = True

    results = run_simulation(riders_copy, stages, n_iterations=10, seed=5)
    for iteration in results:
        gc_times = iteration.gc_times
        gc_winner_id = min(
            (rid for rid, t in gc_times.items() if t < float("inf")),
            key=lambda rid: gc_times[rid],
        )
        assert gc_winner_id != dns_rider_id, (
            f"DNS rider {dns_rider_id} should never win GC"
        )


def test_seeded_run_is_deterministic(sim_data):
    riders, stages = sim_data
    results_a = run_simulation(riders, stages, n_iterations=10, seed=42)
    results_b = run_simulation(riders, stages, n_iterations=10, seed=42)

    for a, b in zip(results_a, results_b):
        gc_winner_a = min(a.gc_times, key=lambda rid: a.gc_times[rid])
        gc_winner_b = min(b.gc_times, key=lambda rid: b.gc_times[rid])
        assert gc_winner_a == gc_winner_b, (
            "Seeded runs must produce identical GC winner sequences"
        )
