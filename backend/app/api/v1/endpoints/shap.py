import json

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.data.repository import get_repository
from app.ml.schema import FEATURE_ORDER
from app.schemas.shap import ShapContribution, ShapExplanation, ShapRequest
from app.services.shap_service import get_shap_service

router = APIRouter()


@router.get("/global/{energy}")
def global_shap(energy: str):
    """Aktif model için önceden hesaplanmış global SHAP özetini döner."""
    if energy not in ("ges", "res"):
        raise HTTPException(status_code=422, detail="energy 'ges' veya 'res' olmalı")
    if not settings.global_shap_path.exists():
        raise HTTPException(
            status_code=503,
            detail="Global SHAP artefaktı yok; ml/shap/build_global_shap.py çalıştırın",
        )
    data = json.loads(settings.global_shap_path.read_text(encoding="utf-8"))
    model = data.get("models", {}).get(energy)
    if model is None:
        raise HTTPException(status_code=404, detail="Enerji türü için özet yok")
    return {"energy": energy, "sample_size": data.get("sample_size"), **model}


@router.post("/local", response_model=ShapExplanation)
def local_shap(payload: ShapRequest):
    """Verilen özellik vektörü için yerel SHAP açıklaması döner."""
    missing = [f for f in FEATURE_ORDER if f not in payload.features]
    if missing:
        raise HTTPException(status_code=422, detail=f"Eksik özellikler: {missing}")

    result = get_shap_service().explain_local(payload.energy, payload.features)
    return ShapExplanation(
        energy=result["energy"],
        expected_value=result["expected_value"],
        prediction_value=result["prediction_value"],
        contributions=[ShapContribution(**c) for c in result["contributions"]],
        model_version=payload.model_version or "active",
    )


@router.get("/district/{district_id}/{energy}", response_model=ShapExplanation)
def district_shap(district_id: str, energy: str):
    """Bir ilçenin temsili (yıllık ortalama) girdileri için SHAP açıklaması."""
    if energy not in ("ges", "res"):
        raise HTTPException(status_code=422, detail="energy 'ges' veya 'res' olmalı")
    repo = get_repository()
    row = repo.get_summary(district_id)
    if row is None:
        raise HTTPException(status_code=404, detail="İlçe bulunamadı")

    features = {k: row[k] for k in FEATURE_ORDER}
    result = get_shap_service().explain_local(energy, features)
    return ShapExplanation(
        energy=result["energy"],
        expected_value=result["expected_value"],
        prediction_value=result["prediction_value"],
        contributions=[ShapContribution(**c) for c in result["contributions"]],
        model_version="active",
    )
