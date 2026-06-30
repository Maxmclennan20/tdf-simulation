from api.state import AppState, JobStatus


def test_new_job_starts_pending():
    state = AppState()
    job = state.new_job()
    assert job.status == JobStatus.PENDING


def test_get_job_returns_current():
    state = AppState()
    job = state.new_job()
    assert state.get_job(job.job_id) is job


def test_get_unknown_job_returns_none():
    state = AppState()
    assert state.get_job("nonexistent") is None
