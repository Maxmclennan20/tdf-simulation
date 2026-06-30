import pytest


def test_get_riders_returns_list(client):
    resp = client.get("/riders")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 15


def test_rider_has_expected_fields(client):
    resp = client.get("/riders")
    r = resp.json()[0]
    for field in ["rider_id", "name", "team", "sprint", "climbing", "tt", "gc",
                  "form", "dns", "dnf"]:
        assert field in r, f"Missing field: {field}"


def test_put_rider_updates_form(client):
    resp = client.put("/riders/1", json={"form": 1.3})
    assert resp.status_code == 200
    resp2 = client.get("/riders")
    r1 = next(r for r in resp2.json() if r["rider_id"] == 1)
    assert r1["form"] == pytest.approx(1.3)


def test_put_rider_dns(client):
    client.put("/riders/2", json={"dns": True})
    resp = client.get("/riders")
    r2 = next(r for r in resp.json() if r["rider_id"] == 2)
    assert r2["dns"] is True


def test_put_nonexistent_rider_returns_404(client):
    resp = client.put("/riders/9999", json={"form": 1.0})
    assert resp.status_code == 404


def test_get_stages_returns_21(client):
    resp = client.get("/stages")
    assert resp.status_code == 200
    assert len(resp.json()) == 21
