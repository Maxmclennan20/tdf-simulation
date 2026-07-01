from __future__ import annotations
from collections import defaultdict
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
        if stage_type == StageType.FLAT:
            cal = rs.stage_calibration_factor
        elif stage_type == StageType.HILLY:
            cal = rs.hilly_calibration_factor
        else:
            cal = rs.calibration_factor
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


def apply_ttt_calibration(
    riders: dict[int, RiderState],
    team_ttt_odds: dict[str, float],
) -> None:
    """
    Set ttt_team_factor for every rider based on team TTT market odds.
    Algorithm mirrors apply_odds_calibration but operates at team level.
      1. p_market[team] = (1/decimal_odds), normalised over teams with odds
      2. p_model[team] = mean raw TT weight for that team, normalised over same teams
      3. ttt_team_factor = p_market / p_model (1.0 for teams with no odds)
    """
    # Group active riders by team
    team_riders: dict[str, list[int]] = defaultdict(list)
    for rid, rs in riders.items():
        if rs.is_active():
            team_riders[rs.rider.team].append(rid)

    # Teams without market odds are extreme longshots — treat as 1001.0 odds
    # so they don't absorb probability from the rated teams.
    DEFAULT_UNRATED_ODDS = 1001.0

    # Market probabilities across ALL active teams (rated + unrated)
    market_raw: dict[str, float] = {}
    for team_name in team_riders:
        if team_name in team_ttt_odds:
            market_raw[team_name] = 1.0 / team_ttt_odds[team_name]
        else:
            market_raw[team_name] = 1.0 / DEFAULT_UNRATED_ODDS

    total_market = sum(market_raw.values())
    if total_market == 0:
        return
    p_market = {team: v / total_market for team, v in market_raw.items()}

    # Model probabilities (raw TT weight per team, normalised over ALL teams)
    model_raw: dict[str, float] = {}
    for team_name, rids in team_riders.items():
        weights = [
            (riders[rid].tt * 0.80 + riders[rid].gc * 0.20) * riders[rid].form
            for rid in rids
        ]
        model_raw[team_name] = sum(weights) / len(weights) if weights else 1.0

    total_model = sum(model_raw.values())
    p_model = {team: v / total_model for team, v in model_raw.items()}

    # Apply factors to all active riders
    for team_name, rids in team_riders.items():
        pm = p_market.get(team_name, 0.0)
        pmod = p_model.get(team_name, 0.0)
        factor = pm / pmod if pmod > 0 else 1.0
        for rid in rids:
            riders[rid].ttt_team_factor = factor


def apply_ranking_calibration(
    riders: dict[int, RiderState],
    ranking_pts: dict[int, float],
    odds: dict[int, dict[str, float]],
    market: str = "gc_win",
    target_field: str = "calibration_factor",
    stage_type: StageType = StageType.MOUNTAIN,
) -> None:
    """
    Calibrate riders NOT covered by bookmaker odds using UCI ranking points.

    Only mutates {target_field} for active riders that have no entry in odds[market].
    Algorithm:
      1. Identify uncovered riders (active, not in bookmaker odds for `market`)
      2. Among uncovered riders that have ranking data:
         p_market[rid] = ranking_pts[rid] / sum(ranking_pts of all uncovered riders with data)
      3. Compute base model weights for uncovered riders (calibration_factor reset to 1.0)
         p_model[rid]  = raw_weight[rid] / sum(raw_weights of all uncovered riders)
      4. target_field = p_market / p_model  (only for riders with ranking data;
         riders without data keep target_field = 1.0)
    """
    # Identify bookmaker-covered riders
    covered = {rid for rid, mkt in odds.items() if market in mkt}

    # Uncovered active riders
    uncovered = [rid for rid, rs in riders.items() if rs.is_active() and rid not in covered]
    if not uncovered:
        return

    # Save and reset calibration factors for uncovered riders so base weights are pure
    saved = {rid: getattr(riders[rid], target_field) for rid in uncovered}
    for rid in uncovered:
        setattr(riders[rid], target_field, 1.0)

    # Compute base model weights for uncovered riders only
    factors = STAGE_FACTORS[stage_type]
    primary_attr, secondary_attr = STAGE_RATING_MAP[stage_type]
    raw_model: dict[int, float] = {}
    for rid in uncovered:
        rs = riders[rid]
        raw_model[rid] = (
            getattr(rs, primary_attr) * factors["primary"]
            + getattr(rs, secondary_attr) * factors["secondary"]
        ) * rs.form

    total_model = sum(raw_model.values())
    if total_model == 0:
        # Restore saved values and abort
        for rid in uncovered:
            setattr(riders[rid], target_field, saved[rid])
        return

    p_model = {rid: w / total_model for rid, w in raw_model.items()}

    # Market-implied distribution from ranking points (only uncovered riders with data)
    pts_with_data = {rid: ranking_pts[rid] for rid in uncovered if rid in ranking_pts}
    if not pts_with_data:
        # No ranking data for any uncovered rider — restore and abort
        for rid in uncovered:
            setattr(riders[rid], target_field, saved[rid])
        return

    total_pts = sum(pts_with_data.values())
    p_market = {rid: pts / total_pts for rid, pts in pts_with_data.items()}

    # Set calibration factors
    for rid in uncovered:
        if rid in p_market:
            p_mod = p_model.get(rid, 0.0)
            setattr(riders[rid], target_field, p_market[rid] / p_mod if p_mod > 0 else 1.0)
        else:
            setattr(riders[rid], target_field, 1.0)


def apply_points_calibration(
    riders: dict[int, RiderState],
    odds: dict[int, dict[str, float]],
) -> None:
    """
    Calibrate points_calibration_factor from the 'points_win' (green jersey) market.

    The green jersey is primarily a sprinters' competition, so flat-stage weights
    serve as the model proxy for expected points accumulation.

    Algorithm (mirrors apply_odds_calibration):
      1. p_market = normalised 1/odds for riders in the 'points_win' market
      2. p_model  = normalised flat-stage weights (sprint × form × stage_calibration_factor)
      3. points_calibration_factor = p_market / p_model  (1.0 for uncovered riders)
    """
    market_raw: dict[int, float] = {}
    for rid, rs in riders.items():
        if rs.is_active() and rid in odds and "points_win" in odds[rid]:
            market_raw[rid] = 1.0 / odds[rid]["points_win"]

    if not market_raw:
        return

    total_market = sum(market_raw.values())
    p_market = {rid: v / total_market for rid, v in market_raw.items()}

    # Model: flat-stage sprint weights (reset points_calibration_factor to 1.0 first)
    for rs in riders.values():
        rs.points_calibration_factor = 1.0
    model_weights = compute_stage_weights(riders, StageType.FLAT)

    # Normalise model weights over riders with market odds only
    covered_model_total = sum(model_weights.get(rid, 0.0) for rid in p_market)
    if covered_model_total == 0:
        return
    p_model = {rid: model_weights.get(rid, 0.0) / covered_model_total for rid in p_market}

    for rid, rs in riders.items():
        if not rs.is_active():
            continue
        if rid in p_market:
            pm = p_model.get(rid, 0.0)
            rs.points_calibration_factor = p_market[rid] / pm if pm > 0 else 1.0
        else:
            rs.points_calibration_factor = 1.0
