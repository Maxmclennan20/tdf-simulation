from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from api.state import app_state, JobStatus

router = APIRouter()

VALID_MARKETS = {"gc", "gc_podium", "stages", "stages_all",
                 "points_jersey", "kom", "young_rider", "head_to_head",
                 "stage_summary"}


class OddsRow(BaseModel):
    rider_id: int
    name: str
    team: str
    win_pct: float
    podium_pct: Optional[float] = None
    decimal_odds: float
    fractional_odds: str
    stage: Optional[int] = None


def _get_completed_job(job_id: str):
    job = app_state.get_job(job_id)
    if job is None:
        raise HTTPException(404, detail={"error": "not_found", "detail": f"Job {job_id} not found"})
    if job.status != JobStatus.COMPLETE:
        raise HTTPException(400, detail={"error": "not_complete", "detail": f"Job status: {job.status}"})
    return job


@router.get("/results/{job_id}/{market}")
def get_results(job_id: str, market: str, stage: Optional[int] = None):
    if market not in VALID_MARKETS:
        raise HTTPException(400, detail={"error": "invalid_market",
                                         "detail": f"Valid markets: {sorted(VALID_MARKETS)}"})
    job = _get_completed_job(job_id)
    res = job.results

    if market == "gc":
        return res.gc
    if market == "gc_podium":
        return res.gc_podium
    if market == "stages":
        if stage is not None:
            return res.stages.get(stage, [])
        return res.stages_all
    if market == "stages_all":
        return res.stages_all
    if market == "points_jersey":
        return res.points_jersey
    if market == "kom":
        return res.kom
    if market == "young_rider":
        return res.young_rider
    if market == "head_to_head":
        return [
            {"rider1_id": k[0], "rider2_id": k[1], "p1": v[0], "p2": v[1]}
            for k, v in res.head_to_head.items()
        ]
    if market == "stage_summary":
        stages = app_state.stages
        summary = []
        for stage_num in sorted(stages.keys()):
            stage = stages[stage_num]
            stage_odds = res.stages.get(stage_num, [])
            top5 = [
                {"rider_id": r.rider_id, "name": r.name, "team": r.team, "win_pct": r.win_pct}
                for r in stage_odds[:5]
            ]
            summary.append({
                "stage": stage_num,
                "type": stage.type,
                "finish": stage.finish,
                "distance": stage.distance,
                "key_climbs": stage.key_climbs,
                "top5": top5,
            })
        return summary
