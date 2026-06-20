from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _top_district_id() -> str:
    return client.get(
        "/api/v1/scores/ranking", params={"energy": "ges", "limit": 1}
    ).json()["items"][0]["district_id"]


def test_district_shap_consistent():
    did = _top_district_id()
    r = client.get(f"/api/v1/shap/district/{did}/ges")
    assert r.status_code == 200
    body = r.json()
    assert len(body["contributions"]) == 12
    # SHAP toplamı + beklenen değer ≈ tahmin
    total = body["expected_value"] + sum(c["shap_value"] for c in body["contributions"])
    assert abs(total - body["prediction_value"]) <= 0.5
    # En etkili katkı mutlak değere göre sıralı
    abs_vals = [abs(c["shap_value"]) for c in body["contributions"]]
    assert abs_vals == sorted(abs_vals, reverse=True)


def test_local_shap_missing_features_422():
    r = client.post(
        "/api/v1/shap/local",
        json={"energy": "ges", "features": {"T2M": 10.0}},
    )
    assert r.status_code == 422
