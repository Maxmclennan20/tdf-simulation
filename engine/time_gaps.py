from __future__ import annotations
import numpy as np
from engine.models import RiderState, StageType
from engine.config import TIME_GAP_PARAMS, TIER_HIGH_THRESHOLD, TIER_MID_THRESHOLD


def _get_tier(rating: float) -> str:
    if rating > TIER_HIGH_THRESHOLD:
        return "tier_high"
    elif rating >= TIER_MID_THRESHOLD:
        return "tier_mid"
    return "tier_low"


def generate_time_gaps(
    riders: dict[int, RiderState],
    stage_type: StageType,
    winner_id: int,
    rng: np.random.Generator,
) -> dict[int, float]:
    """
    Returns time gaps in seconds behind the stage winner for all active riders.
    Flat/hilly stages return 0 for all riders (bunch finish).
    Mountain/TT stages use log-normal distribution per rider rating tier.
    """
    gaps: dict[int, float] = {}

    if stage_type in (StageType.FLAT, StageType.HILLY):
        for rid, rs in riders.items():
            if rs.is_active():
                gaps[rid] = 0.0
        return gaps

    param_key = "mountain" if stage_type == StageType.MOUNTAIN else "tt"
    rating_attr = "climbing" if stage_type == StageType.MOUNTAIN else "tt"
    params = TIME_GAP_PARAMS[param_key]

    for rid, rs in riders.items():
        if not rs.is_active():
            continue
        if rid == winner_id:
            gaps[rid] = 0.0
            continue
        rating = getattr(rs, rating_attr)
        tier = _get_tier(rating)
        mu, sigma = params[tier]
        gaps[rid] = float(rng.lognormal(mean=mu, sigma=sigma))

    return gaps
