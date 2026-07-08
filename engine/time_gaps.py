from __future__ import annotations
import math
import numpy as np
from engine.models import RiderState, StageType


def _mountain_params(climbing: float) -> tuple[float, float]:
    """
    Continuous lognormal parameters for mountain stage time gaps.

    mu scales linearly with distance from the elite threshold (rating 99).
    Base mu=2.5 gives Pogacar (99) a median ~12s loss, Evenepoel (88) ~37s,
    Hindley (86) ~45s, and a pure sprinter (55) ~8 min.

    sigma is large (≥0.8) to capture real-world variability: sometimes stages
    are controlled and gaps are tiny; occasionally the GC blows apart.
    """
    deficit = max(0.0, 99.0 - climbing)
    mu = max(0.5, min(7.5, 2.5 + 0.10 * deficit))
    sigma = min(1.2, max(0.8, 0.8 + 0.004 * deficit))
    return mu, sigma


def _tt_params(tt: float) -> tuple[float, float]:
    """
    Continuous lognormal parameters for TT stage time gaps.

    Uses a piecewise linear formula — the slope is much steeper in the
    elite TT range (tt 92-99) than for mid-tier riders.  This reflects
    the outsized gap a world-class TT specialist like Evenepoel (tt=97)
    creates over Pogacar (tt=94) or Vingegaard (tt=92) in a 40-50km TT.

    Calibrated so:
      • tt=97 (Evenepoel, as loser):  ~24s median loss
      • tt=94 (Pogacar):              ~65s median loss
      • tt=92 (Vingegaard):           ~85s median loss
      • tt=82 (Ayuso):               ~220s median loss
      • tt=72 (Seixas):              ~440s median loss
    """
    deficit = max(0.0, 99.0 - tt)
    if deficit <= 5:
        mu = 2.5 + 0.34 * deficit
    elif deficit <= 12:
        mu = 4.2 + 0.12 * (deficit - 5)
    else:
        mu = 5.04 + 0.07 * (deficit - 12)
    mu = max(0.5, min(7.0, mu))
    sigma = min(1.0, max(0.6, 0.6 + 0.005 * deficit))
    return mu, sigma


def generate_time_gaps(
    riders: dict[int, RiderState],
    stage_type: StageType,
    winner_id: int,
    rng: np.random.Generator,
) -> dict[int, float]:
    """
    Returns time gaps in seconds behind the stage winner for all active riders.
    Flat/hilly stages return 0 for all riders (bunch finish).
    Mountain/TT stages use a continuous rating-based lognormal model.
    """
    gaps: dict[int, float] = {}

    if stage_type in (StageType.FLAT, StageType.HILLY):
        for rid, rs in riders.items():
            if rs.is_active():
                gaps[rid] = 0.0
        return gaps

    is_mountain = stage_type == StageType.MOUNTAIN

    for rid, rs in riders.items():
        if not rs.is_active():
            continue
        if rid == winner_id:
            gaps[rid] = 0.0
            continue
        # Form adjusts effective rating: good form slightly narrows deficits,
        # bad form widens them.  Scale factor 25 means form=0.82 (1-sigma bad)
        # reduces effective climbing/tt by ~5 points, form=1.22 adds ~5 points.
        form_adj = 25.0 * math.log(max(0.01, rs.form))
        # Calibration penalty: when calibration_factor < 1.0 the market implies
        # this rider underperforms raw ratings (health, team tactics, etc.).
        # Reduce effective rating by up to 14 pts at cal=0 (0 when cal >= 1.0).
        # This lets the GC bootstrap actually close the gap for riders like
        # Vingegaard and Evenepoel whose time gap performance wouldn't otherwise
        # respond to calibration_factor suppression. Note the lever is weak for
        # elite riders: their calibrated factors start well above 1.0, so eight
        # damped bootstrap steps rarely push them below the activation point —
        # doubling the scale from 7 to 14 moved Pogacar's GC rate only ~1pp
        # (68.4% -> 69.4% vs a 74.1% power-method target).
        cal_penalty = max(0.0, 14.0 * (1.0 - rs.calibration_factor))
        # gc_rating_adjust: second GC-bootstrap lever, set from market targets.
        # calibration_factor only moves stage-draw probability, which saturates
        # for the top favourite; this shifts the time-gap distributions that
        # actually decide the GC between the leading contenders.
        if is_mountain:
            mu, sigma = _mountain_params(rs.climbing + form_adj - cal_penalty + rs.gc_rating_adjust)
        else:
            mu, sigma = _tt_params(rs.tt + form_adj - cal_penalty + rs.gc_rating_adjust)
        gaps[rid] = float(rng.lognormal(mean=mu, sigma=sigma))

    return gaps
