from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.state import app_state, JobStatus
from api.job_runner import start_simulation_job

router = APIRouter()


class SimulateRequest(BaseModel):
    seed: Optional[int] = None


class JobResponse(BaseModel):
    job_id: str
    status: str


@router.post("/simulate", response_model=JobResponse)
def trigger_simulation(request: SimulateRequest):
    if (app_state.current_job and
            app_state.current_job.status in (JobStatus.PENDING, JobStatus.RUNNING)):
        raise HTTPException(
            409,
            detail={"error": "job_running",
                    "detail": f"Job {app_state.current_job.job_id} is already active"}
        )
    job = start_simulation_job(request.seed)
    return JobResponse(job_id=job.job_id, status=job.status)


@router.get("/jobs/{job_id}/status", response_model=JobResponse)
def get_job_status(job_id: str):
    job = app_state.get_job(job_id)
    if job is None:
        raise HTTPException(404, detail={"error": "not_found", "detail": f"Job {job_id} not found"})
    return JobResponse(job_id=job.job_id, status=job.status)
