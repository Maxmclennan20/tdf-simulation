from __future__ import annotations
import pandas as pd
from pathlib import Path
from engine.models import Rider, Stage, RiderState, StageType


class DataLoadError(Exception):
    pass


def load_team_ttt_odds(data_dir: Path) -> dict[str, float]:
    """Load team TTT odds from team_ttt_odds.csv. Returns {team_name: decimal_odds}."""
    path = data_dir / "team_ttt_odds.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    return {str(row["team_name"]): float(row["decimal_odds"]) for _, row in df.iterrows()}


def load_all_data(data_dir: Path) -> tuple[
    dict[int, RiderState],
    dict[int, Stage],
    dict[int, dict[str, float]],
    pd.DataFrame,
    dict[int, dict[str, float]],
]:
    """
    Returns:
        riders: {rider_id: RiderState}
        stages: {stage_number: Stage}
        odds:   {rider_id: {market: decimal_odds}}
        historical_results: DataFrame
        calibration_factors: empty dict (populated later by performance_model)
    """
    if not data_dir.exists():
        raise DataLoadError(f"Data directory not found: {data_dir}")

    try:
        riders_df = pd.read_csv(data_dir / "riders.csv")
        ratings_df = pd.read_csv(data_dir / "rider_ratings.csv")
        stages_df = pd.read_csv(data_dir / "stages.csv")
        history_df = pd.read_csv(data_dir / "historical_results.csv")
        odds_df = pd.read_csv(data_dir / "odds.csv")
    except FileNotFoundError as e:
        raise DataLoadError(f"Missing CSV: {e}")

    # Build RiderState objects
    ratings_map = ratings_df.set_index("rider_id").to_dict("index")
    riders: dict[int, RiderState] = {}
    try:
        for _, row in riders_df.iterrows():
            rid = int(row["rider_id"])
            if rid in riders:
                raise DataLoadError(f"Duplicate rider_id {rid} in riders.csv")
            r = Rider(
                rider_id=rid,
                name=row["name"],
                team=row["team"],
                nationality=row["nationality"],
                birth_year=int(row["birth_year"]),
                uci_ranking=int(row["uci_ranking"]),
                young_rider_eligible=str(row["young_rider_eligible"]).lower() == "true",
            )
            rat = ratings_map.get(rid, {})
            riders[rid] = RiderState(
                rider=r,
                sprint=float(rat.get("sprint", 50)),
                climbing=float(rat.get("climbing", 50)),
                tt=float(rat.get("tt", 50)),
                gc=float(rat.get("gc", 50)),
            )
    except (ValueError, KeyError) as e:
        raise DataLoadError(f"Invalid data in riders/ratings CSV: {e}") from e

    # Build Stage objects
    stages: dict[int, Stage] = {}
    try:
        for _, row in stages_df.iterrows():
            climbs_raw = str(row.get("key_climbs", "")) if pd.notna(row.get("key_climbs")) else ""
            climbs = [c.strip() for c in climbs_raw.split("|") if c.strip()]
            is_ttt_raw = row.get("is_ttt", False)
            is_ttt = str(is_ttt_raw).strip().lower() == "true" if pd.notna(is_ttt_raw) else False
            stages[int(row["stage"])] = Stage(
                stage=int(row["stage"]),
                start=row["start"],
                finish=row["finish"],
                distance=float(row["distance"]),
                type=StageType(row["type"]),
                key_climbs=climbs,
                is_ttt=is_ttt,
            )
    except (ValueError, KeyError) as e:
        raise DataLoadError(f"Invalid data in stages CSV: {e}") from e

    # Build odds lookup
    odds: dict[int, dict[str, float]] = {}
    for _, row in odds_df.iterrows():
        rid = int(row["rider_id"])
        if rid not in odds:
            odds[rid] = {}
        odds[rid][row["market"]] = float(row["decimal_odds"])

    return riders, stages, odds, history_df, {}
