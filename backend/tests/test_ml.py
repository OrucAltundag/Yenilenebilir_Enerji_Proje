"""Developer/ML endpoint testleri."""

from __future__ import annotations

import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login(username: str, password: str) -> dict[str, str]:
    res = client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_developer_login_works():
    headers = _login("developer", "developer123")
    res = client.get("/api/v1/ml/training-jobs", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_analyst_cannot_access_ml_endpoints():
    headers = _login("analyst", "analyst123")
    res = client.get("/api/v1/ml/training-jobs", headers=headers)
    assert res.status_code == 403


def test_anonymous_blocked_from_ml():
    res = client.get("/api/v1/ml/training-jobs")
    assert res.status_code in (401, 403)


def test_create_training_job_returns_queued_and_completes():
    headers = _login("developer", "developer123")
    payload = {
        "energy_targets": ["ges", "res"],
        "quick_mode": True,
        "n_estimators": 30,
        "max_depth": 3,
        "note": "test eğitimi",
    }
    res = client.post("/api/v1/ml/training-jobs", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["status"] in {"queued", "running", "completed", "failed"}
    job_id = body["id"]

    # Job arka planda çalışır — kısa süre bekleyip durum kontrolü yapalım
    deadline = time.time() + 60
    last_status = body["status"]
    while time.time() < deadline:
        detail = client.get(
            f"/api/v1/ml/training-jobs/{job_id}", headers=headers
        ).json()
        last_status = detail["status"]
        if last_status in {"completed", "failed"}:
            break
        time.sleep(0.5)

    assert last_status == "completed", detail.get("error_message") or detail


def test_developer_cannot_activate_model():
    headers = _login("developer", "developer123")
    models = client.get("/api/v1/ml/models", headers=headers).json()
    if not models:
        return
    target = models[0]["id"]
    res = client.post(
        f"/api/v1/ml/models/{target}/activate", json={}, headers=headers
    )
    assert res.status_code == 403


def test_admin_can_activate_candidate_model():
    dev = _login("developer", "developer123")
    adm = _login("admin", "admin123")
    completed = [
        m
        for m in client.get("/api/v1/ml/models", headers=dev).json()
        if m["status"] == "completed"
    ]
    if not completed:
        return
    target = completed[0]["id"]
    cand = client.post(
        f"/api/v1/ml/models/{target}/mark-candidate", json={}, headers=dev
    )
    assert cand.status_code == 200, cand.text
    assert cand.json()["status"] == "candidate"

    act = client.post(
        f"/api/v1/ml/models/{target}/activate", json={}, headers=adm
    )
    assert act.status_code == 200, act.text
    assert act.json()["status"] == "active"


def test_data_quality_endpoint():
    headers = _login("developer", "developer123")
    res = client.get("/api/v1/ml/data-quality/latest", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert "dataset_version" in body
    assert isinstance(body["warnings"], list)
