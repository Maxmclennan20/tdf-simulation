from __future__ import annotations
import csv
import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from api.routes.results import VALID_MARKETS, _get_completed_job

router = APIRouter()


@router.get("/export/{job_id}/{market}")
def export_csv(job_id: str, market: str, stage: int | None = None):
    if market not in VALID_MARKETS:
        raise HTTPException(400, detail={"error": "invalid_market",
                                         "detail": f"Valid: {sorted(VALID_MARKETS)}"})
    job = _get_completed_job(job_id)
    res = job.results

    output = io.StringIO()
    writer = csv.writer(output)

    if market == "stages" and stage is not None:
        rows = res.stages.get(stage, [])
        writer.writerow(["rider_id", "rider_name", "team", "stage", "win_pct",
                         "decimal_odds", "fractional_odds"])
        for r in rows:
            writer.writerow([r.rider_id, r.name, r.team, stage,
                              r.win_pct, r.decimal_odds, r.fractional_odds])
    elif market in ("stages", "stages_all"):
        rows = res.stages_all
        writer.writerow(["rider_id", "rider_name", "team", "stage", "win_pct",
                         "decimal_odds", "fractional_odds"])
        for r in rows:
            writer.writerow([r.rider_id, r.name, r.team, "all",
                              r.win_pct, r.decimal_odds, r.fractional_odds])
    elif market == "gc_podium":
        writer.writerow(["rider_id", "rider_name", "team", "win_pct", "podium_pct",
                         "decimal_odds", "fractional_odds"])
        for r in res.gc_podium:
            writer.writerow([r.rider_id, r.name, r.team, r.win_pct, r.podium_pct,
                              r.decimal_odds, r.fractional_odds])
    else:
        market_map = {"gc": res.gc, "points_jersey": res.points_jersey,
                      "kom": res.kom, "young_rider": res.young_rider}
        rows = market_map.get(market, [])
        writer.writerow(["rider_id", "rider_name", "team", "win_pct",
                         "decimal_odds", "fractional_odds"])
        for r in rows:
            writer.writerow([r.rider_id, r.name, r.team, r.win_pct,
                              r.decimal_odds, r.fractional_odds])

    output.seek(0)
    filename = f"{market}_odds_{job_id[:8]}.csv"
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
