from __future__ import annotations
import pandas as pd
from pathlib import Path
from engine.models import Rider, Stage, RiderState, StageType


class DataLoadError(Exception):
    pass


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
    for _, row in riders_df.iterrows():
        rid = int(row["rider_id"])
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

    # Build Stage objects
    stages: dict[int, Stage] = {}
    for _, row in stages_df.iterrows():
        climbs_raw = str(row.get("key_climbs", "")) if pd.notna(row.get("key_climbs")) else ""
        climbs = [c.strip() for c in climbs_raw.split("|") if c.strip()]
        stages[int(row["stage"])] = Stage(
            stage=int(row["stage"]),
            start=row["start"],
            finish=row["finish"],
            distance=float(row["distance"]),
            type=StageType(row["type"]),
            key_climbs=climbs,
        )

    # Build odds lookup
    odds: dict[int, dict[str, float]] = {}
    for _, row in odds_df.iterrows():
        rid = int(row["rider_id"])
        if rid not in odds:
            odds[rid] = {}
        odds[rid][row["market"]] = float(row["decimal_odds"])

    return riders, stages, odds, history_df, {}
