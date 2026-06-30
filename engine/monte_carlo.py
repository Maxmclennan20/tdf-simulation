"""Monte Carlo simulation runner for the Tour de France 2026."""
from __future__ import annotations

import numpy as np

from engine.models import IterationResult, StageResult, RiderState, Stage
from engine.config import (
    SIMULATION_ITERATIONS,
    TDF_POINTS_SCALE,
    KOM_POINTS,
    TIER_HIGH_THRESHOLD,
)
from engine.performance_model import compute_stage_weights
from engine.time_gaps import generate_time_gaps

YOUNG_RIDER_BIRTH_YEAR = 2003  # UCI rule: born on/after 1 Jan 2003


def _simulate_one_stage(
    riders: dict[int, RiderState],
    stage: Stage,
    rng: np.random.Generator,
) -> tuple[int, dict[int, float], dict[int, int], dict[int, int]]:
    """Simulate a single stage.

    Returns (winner_id, stage_time_gaps, stage_points, kom_points).

    - winner_id: chosen from active riders using performance-model weights
    - stage_time_gaps: time in seconds behind winner for active riders; 0.0 for inactive
    - stage_points: top-15 finishers get TDF_POINTS_SCALE points (position -> points)
    - kom_points: for each key_climb, stage winner gets KOM_POINTS["HC"][1] = 20 pts
    """
    stage_type = stage.type

    # Build probability weights over active riders only
    weights_dict = compute_stage_weights(riders, stage_type)
    active_ids = list(weights_dict.keys())
    probs = np.array([weights_dict[rid] for rid in active_ids], dtype=float)

    # Normalise (should already sum to 1, but guard against floating-point drift)
    probs /= probs.sum()

    # Draw winner
    winner_idx = rng.choice(len(active_ids), p=probs)
    winner_id = active_ids[winner_idx]

    # Generate time gaps from winner for active riders
    active_gaps = generate_time_gaps(riders, stage_type, winner_id, rng)

    # All riders get a gc_time_gap entry; inactive riders get 0.0 (excluded from GC anyway)
    all_gaps: dict[int, float] = {}
    for rid in riders:
        if riders[rid].is_active():
            all_gaps[rid] = active_gaps.get(rid, 0.0)
        else:
            all_gaps[rid] = 0.0

    # Determine stage finish order for points (by time gap ascending)
    sorted_active = sorted(active_ids, key=lambda rid: active_gaps.get(rid, 0.0))

    # Stage points (top 15 positions)
    stage_points: dict[int, int] = {}
    for pos, rid in enumerate(sorted_active, start=1):
        pts = TDF_POINTS_SCALE.get(pos, 0)
        if pts > 0:
            stage_points[rid] = pts

    # KOM points: stage winner gets 20 pts per key climb
    kom_pts_this_stage: dict[int, int] = {}
    if stage.key_climbs:
        climb_pts = KOM_POINTS["HC"][1]  # 20 per climb
        total_kom = climb_pts * len(stage.key_climbs)
        kom_pts_this_stage[winner_id] = total_kom

    return winner_id, all_gaps, stage_points, kom_pts_this_stage


def _simulate_one_iteration(
    riders: dict[int, RiderState],
    stages: dict[int, Stage],
    rng: np.random.Generator,
) -> IterationResult:
    """Run all stages in stage-number order and return an IterationResult.

    Cumulative GC times are tracked across all stages.
    DNS/DNF riders always carry float('inf') GC time so they never win GC.
    """
    # Initialise cumulative accumulators
    cumulative_gc: dict[int, float] = {
        rid: float("inf") if not rs.is_active() else 0.0
        for rid, rs in riders.items()
    }
    cumulative_points: dict[int, int] = {rid: 0 for rid in riders}
    cumulative_kom: dict[int, int] = {rid: 0 for rid in riders}
    dnf_ids: set[int] = {rid for rid, rs in riders.items() if rs.dnf}

    stage_results: list[StageResult] = []

    for stage_num in sorted(stages.keys()):
        stage = stages[stage_num]
        winner_id, gap_map, s_points, s_kom = _simulate_one_stage(riders, stage, rng)

        # Accumulate GC times (only for active riders — inf stays inf)
        for rid in riders:
            if riders[rid].is_active():
                cumulative_gc[rid] += gap_map[rid]

        # Accumulate points jersey points
        for rid, pts in s_points.items():
            cumulative_points[rid] = cumulative_points.get(rid, 0) + pts

        # Accumulate KOM points
        for rid, pts in s_kom.items():
            cumulative_kom[rid] = cumulative_kom.get(rid, 0) + pts

        # Determine top-3 for this stage (by gap ascending among active riders)
        active_ids = [rid for rid in riders if riders[rid].is_active()]
        sorted_active = sorted(active_ids, key=lambda rid: gap_map[rid])
        top3 = sorted_active[:3]

        stage_results.append(
            StageResult(
                stage=stage_num,
                winner_id=winner_id,
                top3_ids=top3,
                time_gaps=gap_map,
            )
        )

    return IterationResult(
        stage_results=stage_results,
        gc_times=dict(cumulative_gc),
        points_scores=dict(cumulative_points),
        kom_scores=dict(cumulative_kom),
        dnf_ids=dnf_ids,
    )


def run_simulation(
    riders: dict[int, RiderState],
    stages: dict[int, Stage],
    n_iterations: int = SIMULATION_ITERATIONS,
    seed: int | None = None,
) -> list[IterationResult]:
    """Run n_iterations full-race simulations.

    Uses a single numpy RNG seeded with `seed` (random if None).
    Returns a list of IterationResult objects, one per iteration.
    """
    rng = np.random.default_rng(seed)
    return [
        _simulate_one_iteration(riders, stages, rng)
        for _ in range(n_iterations)
    ]
