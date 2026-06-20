from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
ALICE = {"X-User-Id": "alice"}
BOB = {"X-User-Id": "bob"}


def _a_district_id() -> str:
    return client.get(
        "/api/v1/scores/ranking", params={"energy": "ges", "limit": 1}
    ).json()["items"][0]["district_id"]


def test_project_crud_and_owner_isolation():
    did = _a_district_id()
    # Alice proje oluşturur
    created = client.post(
        "/api/v1/projects",
        headers=ALICE,
        json={"name": "GES adayları", "district_ids": [did], "energy": "ges"},
    )
    assert created.status_code == 201
    pid = created.json()["id"]

    # Alice kendi projesini görür
    assert client.get(f"/api/v1/projects/{pid}", headers=ALICE).status_code == 200

    # Bob erişemez (IDOR koruması)
    assert client.get(f"/api/v1/projects/{pid}", headers=BOB).status_code == 403

    # Bob'un listesi boş
    assert client.get("/api/v1/projects", headers=BOB).json() == []


def test_save_scenario_persists_snapshot():
    did = _a_district_id()
    r = client.post(
        "/api/v1/projects/scenarios",
        headers=ALICE,
        json={"district_id": did, "overrides": {"tesvik_bolgesi": 1}},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["input_snapshot"]["tesvik_bolgesi"] is not None
    assert body["result"]["delta_ges"] <= 0
    assert body["scoring_version"]

    listed = client.get("/api/v1/projects/scenarios/list", headers=ALICE)
    assert any(s["id"] == body["id"] for s in listed.json())
