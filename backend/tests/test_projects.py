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


def test_scenario_cannot_attach_to_another_users_project():
    did = _a_district_id()
    project = client.post(
        "/api/v1/projects",
        headers=ALICE,
        json={"name": "Alice projesi", "district_ids": [did], "energy": "ges"},
    ).json()

    response = client.post(
        "/api/v1/projects/scenarios",
        headers=BOB,
        json={
            "district_id": did,
            "project_id": project["id"],
            "overrides": {"tesvik_bolgesi": 2},
        },
    )

    assert response.status_code == 403


def test_project_rejects_unknown_district_and_energy():
    unknown_district = client.post(
        "/api/v1/projects",
        headers=ALICE,
        json={"name": "Hatalı", "district_ids": ["TR-does-not-exist"], "energy": "ges"},
    )
    unknown_energy = client.post(
        "/api/v1/projects",
        headers=ALICE,
        json={"name": "Hatalı", "district_ids": [], "energy": "coal"},
    )

    assert unknown_district.status_code == 422
    assert unknown_energy.status_code == 422
