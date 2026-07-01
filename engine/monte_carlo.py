"""Monte Carlo simulation runner for the Tour de France 2026."""
from __future__ import annotations

from collections import defaultdict

import numpy as np

from engine.models import IterationResult, StageResult, RiderState, Stage, StageType
from engine.config import (
    SIMULATION_ITERATIONS,
    STAGE_POINTS_SCALE,
    KOM_POINTS,
    BUNCH_FINISH_STAGES,
    INTERMEDIATE_SPRINT_STAGES,
    INTERMEDIATE_SPRINT_POINTS,
)
from engine.performance_model import compute_stage_weights
from engine.time_gaps import generate_time_gaps

# Used by aggregator to identify young rider jersey contenders
YOUNG_RIDER_BIRTH_YEAR = 2001  # UCI rule: under 26 on 1 Jan 2026 → born on/after 1 Jan 2001


def _simulate_ttt_stage(
    riders: dict[int, RiderState],
    stage: Stage,
    rng: np.random.Generator,
) -> tuple[int, dict[int, float], dict[int, int], dict[int, int]]:
    """Simulate a Team Time Trial.

    All riders from the same team share the same cumulative time gap.
    Team finishing order is drawn using a Plackett-Luce model weighted by
    each team's mean TT performance score (including ttt_team_factor).
    Inter-team gaps follow a log-normal distribution (~7-15 s per step).
    """
    active_ids = [rid for rid in riders if riders[rid].is_active()]

    # Group active riders by team
    teams: dict[str, list[int]] = defaultdict(list)
    for rid in active_ids:
        teams[riders[rid].rider.team].append(rid)

    team_names = list(teams.keys())

    # Compute each team's mean TT performance weight
    team_raw: dict[str, float] = {}
    for team_name in team_names:
        rids = teams[team_name]
        weights = [
            (riders[rid].tt * 0.80 + riders[rid].gc * 0.20) * riders[rid].form * riders[rid].ttt_team_factor
            for rid in rids
        ]
        team_raw[team_name] = float(np.mean(weights)) if weights else 1.0

    # Draw team finishing order using the Gumbel-max trick (equivalent to
    # Plackett-Luce but fully vectorised: O(n log n) instead of O(n²)).
    # log(score_i) + Gumbel(0,1) is equivalent to sequential weighted draws.
    scores_arr = np.array([team_raw[t] for t in team_names], dtype=float)
    scores_arr = np.clip(scores_arr, 1e-9, None)  # avoid log(0)
    gumbel_noise = rng.gumbel(loc=0.0, scale=1.0, size=len(team_names))
    noisy_log_scores = np.log(scores_arr) + gumbel_noise
    ordered_idx = np.argsort(-noisy_log_scores)  # descending
    ordered_teams = [team_names[int(i)] for i in ordered_idx]

    winner_team = ordered_teams[0]
    # Stage winner = rider with highest TT rating from winning team
    winner_id = max(teams[winner_team], key=lambda rid: riders[rid].tt)

    # Cumulative inter-team time gaps (log-normal, ~7-15 s per consecutive team)
    gap_samples = rng.lognormal(mean=2.0, sigma=0.6, size=max(len(ordered_teams) - 1, 1))
    team_gaps: dict[str, float] = {ordered_teams[0]: 0.0}
    cumulative_gap = 0.0
    for i, team_name in enumerate(ordered_teams[1:]):
        cumulative_gap += float(gap_samples[i])
        team_gaps[team_name] = cumulative_gap

    # Assign individual gaps (all team members share their team's gap)
    all_gaps: dict[int, float] = {}
    for rid in riders:
        if riders[rid].is_active():
            team = riders[rid].rider.team
            all_gaps[rid] = team_gaps.get(team, cumulative_gap)
        else:
            all_gaps[rid] = 0.0

    # Stage points: one representative per team position (highest TT rider)
    stage_points: dict[int, int] = {}
    ttt_scale = STAGE_POINTS_SCALE.get(stage.stage, {})
    for pos, team_name in enumerate(ordered_teams, start=1):
        pts = ttt_scale.get(pos, 0)
        if pts > 0:
            rep = max(teams[team_name], key=lambda rid: riders[rid].tt)
            stage_points[rep] = pts

    return winner_id, all_gaps, stage_points, {}


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
    if stage.is_ttt:
        return _simulate_ttt_stage(riders, stage, rng)

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

    # Determine stage finish order for points.
    # Bunch-finish stages (coefficient 1 & 2): all gaps are 0, so rank by a fresh
    # Gumbel-weighted sprint draw using the same performance weights.
    # Mountain/TT stages: gaps are meaningful, sort by ascending time.
    points_scale = STAGE_POINTS_SCALE.get(stage.stage, {})
    if stage.stage in BUNCH_FINISH_STAGES:
        perf = np.array([weights_dict[rid] for rid in active_ids], dtype=float)
        log_w = np.log(np.clip(perf, 1e-9, None))
        ranked_idx = np.argsort(-(log_w + rng.gumbel(size=len(active_ids))))
        sorted_active = [active_ids[int(i)] for i in ranked_idx]
        # Guarantee the drawn stage winner is always 1st
        if sorted_active[0] != winner_id:
            sorted_active.remove(winner_id)
            sorted_active.insert(0, winner_id)
    else:
        sorted_active = sorted(active_ids, key=lambda rid: active_gaps.get(rid, 0.0))

    stage_points: dict[int, int] = {}
    for pos, rid in enumerate(sorted_active, start=1):
        pts = points_scale.get(pos, 0)
        if pts > 0:
            stage_points[rid] = pts

    # Intermediate sprint bonus (bunch-finish stages only): draw top-3 by sprint weights.
    # Gives sprinters green jersey points independent of the stage finish result.
    if stage.stage in INTERMEDIATE_SPRINT_STAGES:
        sprint_raw = np.array(
            [riders[rid].sprint * riders[rid].form * riders[rid].stage_calibration_factor
             for rid in active_ids],
            dtype=float,
        )
        sprint_total = sprint_raw.sum()
        if sprint_total > 0:
            log_probs = np.log(np.clip(sprint_raw / sprint_total, 1e-9, None))
            ranked_idx = np.argsort(-(log_probs + rng.gumbel(size=len(active_ids))))
            for rank_pos, idx in enumerate(ranked_idx[:3], 1):
                bonus = INTERMEDIATE_SPRINT_POINTS.get(rank_pos, 0)
                if bonus:
                    rid = active_ids[int(idx)]
                    stage_points[rid] = stage_points.get(rid, 0) + bonus

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
