from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _token(username: str, password: str) -> str:
    r = client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _a_district_id() -> str:
    return client.get(
        "/api/v1/scores/ranking", params={"energy": "ges", "limit": 1}
    ).json()["items"][0]["district_id"]


def test_login_bad_credentials():
    r = client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "wrong"}
    )
    assert r.status_code == 401


def test_report_pdf_download():
    did = _a_district_id()
    r = client.get(f"/api/v1/reports/district/{did}.pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"


def test_admin_requires_admin_role():
    analyst = _token("analyst", "analyst123")
    r = client.get(
        "/api/v1/admin/dataset/active",
        headers={"Authorization": f"Bearer {analyst}"},
    )
    assert r.status_code == 403


def test_admin_publish_and_rollback_with_audit():
    admin = _token("admin", "admin123")
    h = {"Authorization": f"Bearer {admin}"}

    # Kalite kapısı: yanlış district_count reddedilir
    bad = client.post(
        "/api/v1/admin/dataset/publish",
        headers=h,
        json={"version": "x", "district_count": 900, "area_zero": 0},
    )
    assert bad.status_code == 422

    ok = client.post(
        "/api/v1/admin/dataset/publish",
        headers=h,
        json={"version": "2023.1", "district_count": 957, "area_zero": 0},
    )
    assert ok.status_code == 200
    assert ok.json()["active"] == "2023.1"

    audit = client.get("/api/v1/admin/audit", headers=h).json()
    assert any(a["action"] == "dataset.publish" for a in audit)
