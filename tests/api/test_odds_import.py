import io


def test_import_odds_updates_calibration(client):
    csv_content = (
        "rider_id,market,decimal_odds\n"
        "1,gc_win,2.00\n"
        "2,gc_win,5.00\n"
    )
    resp = client.post(
        "/odds/import",
        files={"file": ("odds.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Odds imported and calibration updated"


def test_import_invalid_csv_returns_400(client):
    resp = client.post(
        "/odds/import",
        files={"file": ("bad.csv", io.BytesIO(b"not,valid,csv\n1,2"), "text/csv")},
    )
    assert resp.status_code == 400
