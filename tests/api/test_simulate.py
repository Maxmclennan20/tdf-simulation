import time
import pytest


def test_simulate_returns_job_id(client):
    resp = client.post("/simulate", json={})
    assert resp.status_code == 200
    assert "job_id" in resp.json()


def test_simulate_with_seed(client):
    resp = client.post("/simulate", json={"seed": 42})
    assert resp.status_code == 200


def test_job_status_eventually_complete(client, monkeypatch):
    import engine.config as cfg
    monkeypatch.setattr(cfg, "SIMULATION_ITERATIONS", 100)
    resp = client.post("/simulate", json={"seed": 1})
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]
    for _ in range(30):
        status_resp = client.get(f"/jobs/{job_id}/status")
        assert status_resp.status_code == 200
        if status_resp.json()["status"] == "complete":
            break
        time.sleep(0.3)
    assert status_resp.json()["status"] == "complete"


def test_concurrent_simulate_returns_409(client):
    from api.state import app_state, JobStatus
    job = app_state.new_job()
    job.status = JobStatus.RUNNING
    resp = client.post("/simulate", json={})
    assert resp.status_code == 409


def test_unknown_job_status_returns_404(client):
    resp = client.get("/jobs/nonexistent-id/status")
    assert resp.status_code == 404
