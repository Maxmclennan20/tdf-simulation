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

    sprint_stages = (StageType.FLAT, StageType.HILLY)
    raw: dict[int, float] = {}
    for rid, rs in riders.items():
        if not rs.is_active():
            continue
        primary = getattr(rs, primary_attr)
        secondary = getattr(rs, secondary_attr)
        cal = rs.stage_calibration_factor if stage_type in sprint_stages else rs.calibration_factor
        raw[rid] = (
            primary * factors["primary"] + secondary * factors["secondary"]
        ) * rs.form * cal

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
    target_field: str = "calibration_factor",
) -> None:
    """
    Mutates riders[].{target_field} in-place.
    Algorithm:
      1. Extract market-implied probability: p_market = 1 / decimal_odds, normalised
      2. Compute model-implied probability from raw weights (with target_field reset to 1.0)
      3. target_field = p_market / p_model (1.0 for riders with no odds)
    """
    # Step 1: market-implied probabilities
    market_raw: dict[int, float] = {}
    for rid, rs in riders.items():
        if not rs.is_active():
            continue
        if rid in odds and market in odds[rid]:
            market_raw[rid] = 1.0 / odds[rid][market]

    if not market_raw:
        return  # No odds data — leave all factors at 1.0

    # Normalise to remove overround
    total_market = sum(market_raw.values())
    p_market: dict[int, float] = {rid: v / total_market for rid, v in market_raw.items()}

    # Step 2: model-implied probabilities (reset target field to 1.0 first)
    for rs in riders.values():
        setattr(rs, target_field, 1.0)
    model_weights = compute_stage_weights(riders, stage_type)

    # Step 3: set calibration factors
    for rid, rs in riders.items():
        if not rs.is_active():
            continue
        if rid in p_market:
            p_model_rid = model_weights.get(rid, 0.0)
            setattr(rs, target_field, p_market[rid] / p_model_rid if p_model_rid > 0 else 1.0)
        else:
            setattr(rs, target_field, 1.0)
