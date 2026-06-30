from __future__ import annotations
from engine.models import RiderState, StageType
from engine.config import STAGE_FACTORS, STAGE_RATING_MAP


def compute_stage_weights(
    riders: dict[int, RiderState],
    stage_type: StageType,
) -> dict[int, float]:
    """Return normalised probability weights for active riders on a given stage type."""
    factors = STAGE_FACTORS[stage_type]
    primary_attr, secondary_attr = STAGE_RATING_MAP[stage_type]

    raw: dict[int, float] = {}
    for rid, rs in riders.items():
        if not rs.is_active():
            continue
        primary = getattr(rs, primary_attr)
        secondary = getattr(rs, secondary_attr)
        raw[rid] = (
            primary * factors["primary"] + secondary * factors["secondary"]
        ) * rs.form * rs.calibration_factor

    total = sum(raw.values())
    if total == 0:
        # Fallback: equal weights
        n = len(raw)
        return {rid: 1.0 / n for rid in raw}
    return {rid: w / total for rid, w in raw.items()}


def apply_odds_calibration(
    riders: dict[int, RiderState],
    odds: dict[int, dict[str, float]],
    market: str,
    stage_type: StageType,
) -> None:
    """
    Mutates riders[].calibration_factor in-place.
    Algorithm per spec:
      1. Extract market-implied probability: p_market = 1 / decimal_odds, normalised
      2. Compute model-implied probability from raw weights
      3. calibration_factor = p_market / p_model (1.0 for riders with no odds)
    """
    # Step 1: market-implied probabilities
    market_raw: dict[int, float] = {}
    for rid, rs in riders.items():
        if not rs.is_active():
            continue
        if rid in odds and market in odds[rid]:
            market_raw[rid] = 1.0 / odds[rid][market]

    if not market_raw:
        return  # No odds data — leave all calibration_factors at 1.0

    # Normalise to remove overround
    total_market = sum(market_raw.values())
    p_market: dict[int, float] = {rid: v / total_market for rid, v in market_raw.items()}

    # Step 2: model-implied probabilities (pre-calibration, all factors reset to 1.0)
    for rs in riders.values():
        rs.calibration_factor = 1.0
    model_weights = compute_stage_weights(riders, stage_type)

    # Step 3: set calibration factors
    # p_market[rid] is normalised over the market subset (overround removed)
    # p_model[rid] is the full-field model weight (already sums to 1 over all active riders)
    # Dividing gives a factor that boosts/dampens the rider relative to the full field
    for rid, rs in riders.items():
        if not rs.is_active():
            continue
        if rid in p_market:
            p_model_rid = model_weights.get(rid, 0.0)
            if p_model_rid > 0:
                rs.calibration_factor = p_market[rid] / p_model_rid
            else:
                rs.calibration_factor = 1.0
        else:
            rs.calibration_factor = 1.0
