"""XGBoost modellerini yükler ve tahmin servisini sağlar."""

from __future__ import annotations

import xgboost as xgb

from app.core.config import settings
from app.ml.schema import FEATURE_ORDER


class ModelService:
    def __init__(self) -> None:
        self._models: dict[str, xgb.Booster] = {}

    def load_all(self) -> None:
        self.load("ges", settings.ges_model_file)
        self.load("res", settings.res_model_file)

    def load(self, energy: str, filename: str) -> None:
        booster = xgb.Booster()
        booster.load_model(str(settings.model_registry_dir / filename))
        # feature_schema doğrulaması (rapor 5.3)
        model_features = booster.feature_names
        if model_features and tuple(model_features) != FEATURE_ORDER:
            raise RuntimeError(
                f"{energy} modeli feature şeması beklenenden farklı: {model_features}"
            )
        self._models[energy] = booster

    def is_loaded(self, energy: str) -> bool:
        return energy in self._models

    def predict(self, energy: str, features: dict[str, float]) -> float:
        if energy not in self._models:
            raise RuntimeError(f"Model yüklü değil: {energy}")
        booster = self._models[energy]
        vector = [float(features[k]) for k in FEATURE_ORDER]
        dmatrix = xgb.DMatrix([vector], feature_names=list(FEATURE_ORDER))
        return float(booster.predict(dmatrix)[0])


_model_service: ModelService | None = None


def get_model_service() -> ModelService:
    global _model_service
    if _model_service is None:
        _model_service = ModelService()
        _model_service.load_all()
    return _model_service
