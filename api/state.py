from __future__ import annotations
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from engine.models import RiderState, Stage, AggregatedResults


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class SimulationJob:
    job_id: str
    status: JobStatus = JobStatus.PENDING
    error: Optional[str] = None
    results: Optional[AggregatedResults] = None


class AppState:
    def __init__(self):
        self.riders: dict[int, RiderState] = {}
        self.stages: dict[int, Stage] = {}
        self.odds: dict[int, dict[str, float]] = {}
        self.current_job: Optional[SimulationJob] = None

    def new_job(self) -> SimulationJob:
        job = SimulationJob(job_id=str(uuid.uuid4()))
        self.current_job = job
        return job

    def get_job(self, job_id: str) -> Optional[SimulationJob]:
        if self.current_job and self.current_job.job_id == job_id:
            return self.current_job
        return None


app_state = AppState()
