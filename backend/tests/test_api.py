from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_cors_allows_local_frontend_origins():
    for origin in ("http://localhost:3000", "http://127.0.0.1:3000"):
        response = client.options(
            "/api/v1/scores/ranking",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin


def test_search_returns_districts():
    r = client.get("/api/v1/districts/search", params={"q": "şanlıurfa"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] > 0
    assert "district_id" in body["items"][0]


def test_district_geojson_covers_current_boundaries():
    response = client.get("/api/v1/districts/geojson")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/geo+json")
    body = response.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 973
    assert len({feature["properties"]["shape_id"] for feature in body["features"]}) == 973
    assert all(feature["properties"]["district_id"] for feature in body["features"])


def test_score_map_ges():
    r = client.get("/api/v1/scores/map", params={"energy": "ges"})
    assert r.status_code == 200
    body = r.json()
    assert body["energy"] == "ges"
    assert len(body["items"]) == 957
    assert all(0 <= it["score"] <= 100 for it in body["items"][:50])


def test_ranking_top_is_sanliurfa():
    r = client.get("/api/v1/scores/ranking", params={"energy": "ges", "limit": 5})
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 5
    # Rapor bulgusu: GES ilk sıralar Şanlıurfa ilçeleri
    assert items[0]["province"] == "ŞANLIURFA"
    # Skorlar azalan sırada
    scores = [it["score"] for it in items]
    assert scores == sorted(scores, reverse=True)


def test_summary_and_scenario_roundtrip():
    top = client.get(
        "/api/v1/scores/ranking", params={"energy": "ges", "limit": 1}
    ).json()["items"][0]
    did = top["district_id"]

    summary = client.get(f"/api/v1/districts/{did}/summary").json()
    assert summary["national_rank_ges"] == 1
    assert len(summary["monthly"]) == 12
    assert summary["scoring_version"]

    # Senaryo: eğimi sıfırlamak skoru düşürmemeli/aynı kalmalı; teşviği 1 yapmak GES'i düşürür
    scn = client.post(
        "/api/v1/scenarios/simulate",
        json={"district_id": did, "overrides": {"tesvik_bolgesi": 1}},
    ).json()
    assert scn["baseline_ges"] is not None
    assert scn["scenario_ges"] is not None
    assert scn["delta_ges"] <= 0  # 6->1 teşvik düşüşü GES skorunu azaltır


def test_scenario_rejects_out_of_range():
    top = client.get(
        "/api/v1/scores/ranking", params={"energy": "ges", "limit": 1}
    ).json()["items"][0]
    r = client.post(
        "/api/v1/scenarios/simulate",
        json={"district_id": top["district_id"], "overrides": {"tesvik_bolgesi": 99}},
    )
    assert r.status_code == 422
