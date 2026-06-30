from __future__ import annotations
import io
import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, File
from api.state import app_state
from engine.models import StageType
from engine.performance_model import apply_odds_calibration

router = APIRouter()


@router.post("/odds/import")
async def import_odds(file: UploadFile = File(...)):
    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
        required = {"rider_id", "market", "decimal_odds"}
        if not required.issubset(df.columns):
            raise HTTPException(400, detail={
                "error": "invalid_csv",
                "detail": f"CSV must have columns: {required}"
            })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail={"error": "parse_error", "detail": str(e)})

    new_odds: dict[int, dict[str, float]] = {}
    for _, row in df.iterrows():
        rid = int(row["rider_id"])
        if rid not in new_odds:
            new_odds[rid] = {}
        new_odds[rid][row["market"]] = float(row["decimal_odds"])

    app_state.odds = new_odds
    apply_odds_calibration(app_state.riders, app_state.odds,
                           "gc_win", StageType.MOUNTAIN)
    return {"message": "Odds imported and calibration updated"}
