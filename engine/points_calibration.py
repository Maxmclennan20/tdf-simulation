from __future__ import annotations
from collections import defaultdict
from engine.models import RiderState, Stage
from engine.config import BUNCH_FINISH_STAGES
from engine.odds_converter import remove_overround_power

# Bootstrap parameters (used for points/green jersey calibration)
BOOTSTRAP_ITERS_PER_STEP = 2000  # iterations per calibration step (higher = less noise, ~15s/step)
MAX_CALIBRATION_STEPS = 5        # damped iteration steps (total ~75s startup)
DAMPING = 0.5                    # geometric-mean damping prevents overshoot
BASE_SEED = 42

# Bootstrap parameters for GC calibration.
# apply_odds_calibration calibrates mountain-stage win probability, but GC is
# also decided by TT stages.  Riders with high TT ratings (e.g. Evenepoel tt=97)
# or mediocre mountain but good all-round ratings win the GC far more than their
# mountain-stage calibration implies.  Bootstrap measures actual GC win rates.
GC_BOOTSTRAP_ITERS_PER_STEP = 6000  # iterations per step (higher SE per step: ±0.64pp vs ±1.1pp)
GC_MAX_CALIBRATION_STEPS = 8        # 8 steps × 6000 iters; fewer steps needed with lower noise
GC_MAX_CAL_FACTOR = 100.0           # hard ceiling: prevents TT-weak riders (Seixas, Del Toro) from
                                    # inflating calibration_factor to 1000+ without improving GC rate
GC_DAMPING = 0.5
GC_BASE_SEED = 542

# Riders not in the points_win market are extreme longshots.
DEFAULT_UNRATED_ODDS = 1001.0


def _compute_market_probs(
    riders: dict[int, RiderState],
    odds: dict[int, dict[str, float]],
    active: dict[int, RiderState],
) -> dict[int, float]:
    """Return power-method de-margined market probability for every active rider."""
    raw: dict[int, float] = {}
    for rid in active:
        if rid in odds and "points_win" in odds[rid]:
            raw[rid] = 1.0 / odds[rid]["points_win"]
        else:
            raw[rid] = 1.0 / DEFAULT_UNRATED_ODDS
    return remove_overround_power(raw)


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

    # Power-method de-margined market implied probabilities for all eligible riders
    raw: dict[int, float] = {}
    for rid in eligible:
        if rid in odds and "young_rider_win" in odds[rid]:
            raw[rid] = 1.0 / odds[rid]["young_rider_win"]
        else:
            raw[rid] = 1.0 / DEFAULT_UNRATED_ODDS
    if not raw:
        return
    p_market = remove_overround_power(raw)

    # Set yr_cal = de-margined market probability (draw weight in _simulate_one_iteration)
    for rid in eligible:
        riders[rid].young_rider_calibration_factor = p_market[rid]


def apply_gc_bootstrap_calibration(
    riders: dict[int, RiderState],
    stages: dict[int, Stage],
    odds: dict[int, dict[str, float]],
) -> None:
    """
    Fine-tune calibration_factor for all covered GC riders via damped iterative bootstrap.

    WHY BOOTSTRAP ON TOP OF apply_odds_calibration?

    apply_odds_calibration sets calibration_factor = p_market / p_model where
    p_model is the mountain-stage win probability.  But the GC is not decided
    purely on mountain stages — TT stages add significant time.  Riders with
    high TT ratings (e.g. Evenepoel tt=97) gain disproportionate GC time in
    TTs, winning the GC far more often than their mountain-weight calibration
    implies.  Conversely strong climbers that are TT-weak (e.g. Seixas tt=72)
    win the GC less than expected.

    The bootstrap runs the full 21-stage simulation, measures actual GC win
    rates, and applies damped bisection corrections — identical in structure to
    the green jersey calibration.

    WHY ALL COVERED RIDERS (including 251-odds longshots)?

    Riders with gc_win=251 odds (target ~0.3% each) often show up at 2-4% in
    simulation because good all-round ratings give them time gains in TTs.
    With ~30 such riders, they collectively steal ~40% of probability away from
    the favourites.  Suppressing them via bootstrap restores that probability to
    Pogacar, Vingegaard, etc.

    Must be called AFTER apply_odds_calibration + apply_ranking_calibration so
    that the starting calibration_factor values are already sensible.
    """
    from engine.monte_carlo import run_simulation

    active = {rid: rs for rid, rs in riders.items() if rs.is_active()}

    # Market-implied probabilities for ALL covered GC riders, de-margined via
    # the power method — MUST match apply_odds_calibration so the bootstrap
    # refines the same targets rather than re-targeting proportional ones.
    raw_market: dict[int, float] = {}
    for rid, rs in active.items():
        if rid in odds and "gc_win" in odds[rid]:
            raw_market[rid] = 1.0 / odds[rid]["gc_win"]
    if not raw_market:
        return
    p_market = remove_overround_power(raw_market)

    for step in range(GC_MAX_CALIBRATION_STEPS):
        iters = run_simulation(
            riders, stages,
            n_iterations=GC_BOOTSTRAP_ITERS_PER_STEP,
            seed=GC_BASE_SEED + step,
        )

        # Measure GC win rates
        wins: dict[int, int] = defaultdict(int)
        for it in iters:
            ranked = sorted(it.gc_times.items(), key=lambda x: x[1])
            if ranked:
                wins[ranked[0][0]] += 1
        n = len(iters)
        p_sim = {rid: cnt / n for rid, cnt in wins.items()}

        if not p_sim:
            break

        for rid in p_market:
            if rid not in riders or not riders[rid].is_active():
                continue
            p_s = p_sim.get(rid, 0.0)
            p_m = p_market[rid]

            if p_s > 0 and p_m > 0:
                multiplier = (p_m / p_s) ** GC_DAMPING
                riders[rid].calibration_factor *= multiplier
            elif p_m > 0:
                # Covered rider never won in this step — gentle nudge up.
                # Using 1.1 (not 1.5) prevents TT-weak riders like Seixas from
                # exploding to cal=5000 when their structural TT ceiling means
                # no amount of mountain-stage boosting achieves their market GC %.
                riders[rid].calibration_factor *= 1.1

            # Hard ceiling: prevents calibration divergence for riders whose
            # TT deficit structurally limits their GC win probability below
            # their market odds (e.g. Seixas tt=72 → ~880s TT loss per race).
            riders[rid].calibration_factor = min(
                GC_MAX_CAL_FACTOR, riders[rid].calibration_factor
            )
