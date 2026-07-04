from __future__ import annotations
from collections import defaultdict
from engine.models import RiderState, Stage
from engine.config import BUNCH_FINISH_STAGES

# Bootstrap parameters (used for points/green jersey calibration)
BOOTSTRAP_ITERS_PER_STEP = 2000  # iterations per calibration step (higher = less noise, ~15s/step)
MAX_CALIBRATION_STEPS = 5        # damped iteration steps (total ~75s startup)
DAMPING = 0.5                    # geometric-mean damping prevents overshoot
BASE_SEED = 42

# Riders not in the points_win market are extreme longshots.
DEFAULT_UNRATED_ODDS = 1001.0


def _compute_market_probs(
    riders: dict[int, RiderState],
    odds: dict[int, dict[str, float]],
    active: dict[int, RiderState],
) -> dict[int, float]:
    """Return normalised market probability for every active rider."""
    raw: dict[int, float] = {}
    for rid in active:
        if rid in odds and "points_win" in odds[rid]:
            raw[rid] = 1.0 / odds[rid]["points_win"]
        else:
            raw[rid] = 1.0 / DEFAULT_UNRATED_ODDS
    total = sum(raw.values())
    return {rid: v / total for rid, v in raw.items()}


def _jersey_win_probs(
    iterations: list,
    active: dict[int, RiderState],
) -> dict[int, float]:
    """
    Return the empirical probability that each rider wins the most
    calibration-adjusted bunch-finish stage wins.

    Winner per iteration = argmax(bunch_stage_wins × points_calibration_factor).
    This is the SAME criterion the aggregator uses, so the bootstrap is
    self-consistent with the final simulation.
    """
    jersey_wins: dict[int, int] = defaultdict(int)
    for it in iterations:
        sprint_wins: dict[int, float] = defaultdict(float)
        for sr in it.stage_results:
            if sr.stage in BUNCH_FINISH_STAGES and sr.winner_id in active:
                sprint_wins[sr.winner_id] += active[sr.winner_id].points_calibration_factor
        if sprint_wins:
            winner = max(sprint_wins, key=sprint_wins.get)
            jersey_wins[winner] += 1

    total = sum(jersey_wins.values())
    if total == 0:
        return {}
    return {rid: cnt / total for rid, cnt in jersey_wins.items()}


def apply_points_calibration(
    riders: dict[int, RiderState],
    stages: dict[int, Stage],
    odds: dict[int, dict[str, float]],
) -> None:
    """
    Calibrate points_calibration_factor for the green jersey via damped
    iterative bootstrap calibration.

    WHY ITERATIVE?

    Single-pass calibration overshoots: a rider whose natural simulation
    win rate is 1.4% but whose market probability is 9% gets a 6.3× factor.
    In the next simulation this factor causes them to win 20%+ of iterations,
    far above target. The iteration oscillates without converging.

    WHY DAMPED?

    Instead of full step  factor_new = p_market / p_sim_current (which
    overshoots), use a geometric-mean half-step:

        factor_new = factor_old × (p_market / p_sim_current) ^ DAMPING

    With DAMPING=0.5 this is a bisection on log-scale. Simulations show it
    converges to within ~1 percentage point of target in 4–5 steps.

    EXAMPLE (Kooij, market=9%):
      Step 0  factor=1.00  p_sim=1.4%  multiplier=(9/1.4)^0.5=2.53
      Step 1  factor=2.53  p_sim=7%    multiplier=(9/7)^0.5=1.13
      Step 2  factor=2.86  p_sim=8%    multiplier=(9/8)^0.5=1.06
      Step 3  factor=3.03  p_sim=9%    converged ✓

    WHY BUNCH-FINISH STAGE WINS (not accumulated sprint points)?

    Using the argmax of accumulated sprint points is dominated by mountain-
    stage winners (Pogacar accumulates 300+ raw pts from 10 mountain wins).
    Counting who wins the most bunch-finish stages confines the competition
    to sprint stages where the green jersey is actually decided, while
    remaining consistent between the bootstrap criterion and the aggregator.

    WHY DEFAULT_UNRATED_ODDS?

    Without a tiny default probability for uncovered riders, they inherit
    points_calibration_factor=1.0 while covered sprinters (suppressed to
    0.3–1.5×) are overwhelmed whenever uncovered riders win any bunch stage.
    """
    from engine.monte_carlo import run_simulation

    active = {rid: rs for rid, rs in riders.items() if rs.is_active()}
    p_market = _compute_market_probs(riders, odds, active)

    # Reset calibration factors before iteration
    for rs in riders.values():
        rs.points_calibration_factor = 1.0

    for step in range(MAX_CALIBRATION_STEPS):
        iters = run_simulation(
            riders, stages,
            n_iterations=BOOTSTRAP_ITERS_PER_STEP,
            seed=BASE_SEED + step,
        )
        p_sim = _jersey_win_probs(iters, active)

        if not p_sim:
            break

        for rid, rs in riders.items():
            if not rs.is_active():
                continue
            p_s = p_sim.get(rid, 0.0)
            p_m = p_market.get(rid, 0.0)

            if p_s > 0 and p_m > 0:
                # Geometric-mean damped step on log scale
                multiplier = (p_m / p_s) ** DAMPING
                rs.points_calibration_factor *= multiplier
            elif p_m > 0:
                # Rider never won in this step — nudge factor toward zero
                rs.points_calibration_factor *= DAMPING
            # else p_m == 0: leave factor unchanged (shouldn't happen)



def apply_young_rider_calibration(
    riders: dict[int, RiderState],
    stages: dict[int, Stage],
    odds: dict[int, dict[str, float]],
) -> None:
    """
    Set young_rider_calibration_factor directly from bookmaker market probabilities.

    WHY NOT BOOTSTRAP (effective-time approach)?

    For some young rider contenders (e.g. Seixas, gc_win=11.5 but tt=72), the
    cumulative GC time from the simulation is structurally inconsistent with
    their young rider market odds.  Their TT weakness produces consistently
    worse GC times than riders like Del Toro (tt=74) and Ayuso (tt=82), so
    argmin(gc_time / yr_cal) cannot simultaneously achieve market targets for
    all covered riders — the calibration either overshoots one rider or
    drastically undershoots another.

    WHY DIRECT PROBABILITY DRAW?

    The simulation draws the young rider winner in each iteration using a
    probability-weighted draw over eligible active riders (yr_cal as weights).
    This mirrors the stage-winner draw mechanism and allows exact market
    calibration.  A DNF rider cannot win (the draw is over active riders only),
    preserving realistic correlation with race outcomes.

    yr_cal is set to the normalised market implied probability.  Riders without
    market coverage receive 1/DEFAULT_UNRATED_ODDS weight — small enough to
    ensure covered riders dominate, but non-zero so uncovered riders can
    occasionally win.
    """
    active = {rid: rs for rid, rs in riders.items() if rs.is_active()}
    eligible = {rid: rs for rid, rs in active.items() if rs.rider.young_rider_eligible}

    # Normalised market implied probabilities for all eligible riders
    raw: dict[int, float] = {}
    for rid in eligible:
        if rid in odds and "young_rider_win" in odds[rid]:
            raw[rid] = 1.0 / odds[rid]["young_rider_win"]
        else:
            raw[rid] = 1.0 / DEFAULT_UNRATED_ODDS
    total = sum(raw.values())
    if total == 0:
        return

    # Set yr_cal = normalised market probability (draw weight in _simulate_one_iteration)
    for rid in eligible:
        riders[rid].young_rider_calibration_factor = raw[rid] / total
