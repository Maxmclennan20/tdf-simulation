from __future__ import annotations
from collections import defaultdict
from engine.models import RiderState, Stage
from engine.config import BUNCH_FINISH_STAGES

BOOTSTRAP_ITERATIONS = 1000
BOOTSTRAP_SEED = 42

# Riders not covered by the bookmaker points_win market are extreme longshots.
# Treating them as 1001 decimal odds suppresses them in the aggregator without
# requiring them to have zero weight (which would make their factor undefined).
DEFAULT_UNRATED_ODDS = 1001.0


def apply_points_calibration(
    riders: dict[int, RiderState],
    stages: dict[int, Stage],
    odds: dict[int, dict[str, float]],
) -> None:
    """
    Calibrate points_calibration_factor for the green jersey (points classification).

    APPROACH — bunch-finish stage wins as proxy:

    The green jersey competition is decided on sprint stages. Using who wins the
    most bunch-finish stages as the calibration proxy gives stable calibration
    factors (1–7×) compared to using total accumulated points, which produces
    extreme factors (up to 80×) due to Pogacar dominating mountain stage points.

    The aggregator determines the green jersey winner each iteration as
    argmax(bunch_stage_wins × points_calibration_factor). This correctly:
    - Suppresses GC riders: Pogacar wins few sprint stages → low count × any factor
    - Amplifies specialist sprinters: more wins × moderate market-calibrated factor
    - Suppresses uncovered riders via DEFAULT_UNRATED_ODDS → near-zero factor

    KNOWN LIMITATION:
    Merlier and Kooij remain ~2× above their market probabilities (25%/21% vs
    11%/9%) because the stage_calibration_factor spread across sprint specialists
    (Philipsen 18×, Merlier 11×, Kooij 7× from the sprint_rankings calibration)
    causes Kooij to barely win in the bootstrap, requiring a 6× amplification
    that creates winner-take-all dynamics. Fixing this requires recalibrating the
    sprint_rankings calibration to have more moderate stage_calibration_factors.
    Despite this, the distribution is a large improvement over the 76% Pogacar
    result from mountain stage point inflation.

    Algorithm:
      1. p_market for all active riders:
           covered: normalised 1/decimal_odds
           uncovered: normalised 1/DEFAULT_UNRATED_ODDS
      2. Run BOOTSTRAP_ITERATIONS with points_calibration_factor=1.0 to measure
         who wins the most bunch-finish stages (empirical p_simulation).
      3. points_calibration_factor = p_market / p_simulation (1.0 if p_sim=0)
    """
    from engine.monte_carlo import run_simulation

    active = {rid: rs for rid, rs in riders.items() if rs.is_active()}

    # Market probabilities for ALL active riders
    market_raw: dict[int, float] = {}
    for rid in active:
        if rid in odds and "points_win" in odds[rid]:
            market_raw[rid] = 1.0 / odds[rid]["points_win"]
        else:
            market_raw[rid] = 1.0 / DEFAULT_UNRATED_ODDS

    total_market = sum(market_raw.values())
    p_market = {rid: v / total_market for rid, v in market_raw.items()}

    # Bootstrap with all points_calibration_factor reset to 1.0
    for rs in riders.values():
        rs.points_calibration_factor = 1.0

    iterations = run_simulation(riders, stages, n_iterations=BOOTSTRAP_ITERATIONS, seed=BOOTSTRAP_SEED)

    # Count who wins the most bunch-finish stages per iteration
    jersey_wins: dict[int, int] = defaultdict(int)
    for it in iterations:
        sprint_wins: dict[int, int] = defaultdict(int)
        for sr in it.stage_results:
            if sr.stage in BUNCH_FINISH_STAGES and sr.winner_id in active:
                sprint_wins[sr.winner_id] += 1
        if sprint_wins:
            winner = max(sprint_wins, key=sprint_wins.get)
            jersey_wins[winner] += 1

    total_wins = sum(jersey_wins.values())
    if total_wins == 0:
        return

    p_simulation = {rid: cnt / total_wins for rid, cnt in jersey_wins.items()}

    # Set calibration factors
    for rid, rs in riders.items():
        if not rs.is_active():
            continue
        p_sim = p_simulation.get(rid, 0.0)
        p_mkt = p_market.get(rid, 0.0)
        rs.points_calibration_factor = p_mkt / p_sim if p_sim > 0 else p_mkt
