from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_readyz_all_green():
    r = client.get("/api/v1/readyz")
    assert r.status_code == 200
    body = r.json()
    assert body["ready"] is True
    assert body["checks"]["district_count_ok"] is True
    assert body["checks"]["district_geometry"] is True
    assert body["checks"]["ges_model"] is True
    assert body["checks"]["res_model"] is True


def test_metrics_exposes_district_count():
    r = client.get("/api/v1/metrics")
    assert r.status_code == 200
    assert "buraki_district_count 957" in r.text
