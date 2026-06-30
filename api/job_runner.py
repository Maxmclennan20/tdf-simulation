from __future__ import annotations
import threading
import engine.config as _cfg
from engine.monte_carlo import run_simulation
from engine.aggregator import aggregate_results
from api.state import SimulationJob, JobStatus, app_state


def run_simulation_job(job: SimulationJob, seed: int | None) -> None:
    job.status = JobStatus.RUNNING
    try:
        iterations = run_simulation(
            app_state.riders, app_state.stages,
            n_iterations=_cfg.SIMULATION_ITERATIONS, seed=seed,
        )
        job.results = aggregate_results(app_state.riders, app_state.stages, iterations)
        job.status = JobStatus.COMPLETE
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)


def start_simulation_job(seed: int | None) -> SimulationJob:
    job = app_state.new_job()
    thread = threading.Thread(target=run_simulation_job, args=(job, seed), daemon=True)
    thread.start()
    return job
