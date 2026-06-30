import time
import engine.config as cfg


def run_job(client, monkeypatch):
    monkeypatch.setattr(cfg, "SIMULATION_ITERATIONS", 100)
    resp = client.post("/simulate", json={"seed": 42})
    job_id = resp.json()["job_id"]
    for _ in range(30):
        s = client.get(f"/jobs/{job_id}/status").json()["status"]
        if s == "complete":
            break
        time.sleep(0.3)
    return job_id


def test_get_gc_results(client, monkeypatch):
    job_id = run_job(client, monkeypatch)
    resp = client.get(f"/results/{job_id}/gc")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert all("win_pct" in r for r in data)
    assert all("decimal_odds" in r for r in data)


def test_get_stages_results(client, monkeypatch):
    job_id = run_job(client, monkeypatch)
    resp = client.get(f"/results/{job_id}/stages")
    assert resp.status_code == 200


def test_invalid_market_returns_400(client, monkeypatch):
    job_id = run_job(client, monkeypatch)
    resp = client.get(f"/results/{job_id}/invalid_market")
    assert resp.status_code == 400


def test_export_gc_csv(client, monkeypatch):
    job_id = run_job(client, monkeypatch)
    resp = client.get(f"/export/{job_id}/gc")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    lines = resp.text.strip().split("\n")
    assert lines[0].startswith("rider_id")
    assert len(lines) > 1


def test_export_stages_csv(client, monkeypatch):
    job_id = run_job(client, monkeypatch)
    resp = client.get(f"/export/{job_id}/stages")
    assert resp.status_code == 200
    lines = resp.text.strip().split("\n")
    assert "stage" in lines[0]
