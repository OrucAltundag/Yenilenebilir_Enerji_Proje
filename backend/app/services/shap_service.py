"""SHAP açıklama servisi.

Ağaç tabanlı XGBoost modelleri için TreeExplainer ile yerel özellik katkılarını
üretir. Katkıların toplamı + beklenen değer, model tahminine tolerans içinde
eşit olmalıdır (rapor 7.1). Global SHAP üretimi offline yapılır; bu serviste
yerel açıklama anlık hesaplanır.
"""

from __future__ import annotations

import numpy as np
import shap
import xgboost as xgb

from app.ml.schema import FEATURE_ORDER
from app.services.model_service import ModelService

TOLERANCE = 0.01


class ShapService:
    def __init__(self, model_service: ModelService) -> None:
        self.model_service = model_service
        self._explainers: dict[str, shap.TreeExplainer] = {}

    def _explainer(self, energy: str) -> shap.TreeExplainer:
        if energy not in self._explainers:
            booster = self.model_service._models[energy]
            self._explainers[energy] = shap.TreeExplainer(booster)
        return self._explainers[energy]

    def explain_local(self, energy: str, features: dict[str, float]) -> dict:
        explainer = self._explainer(energy)
        vector = np.array([[float(features[k]) for k in FEATURE_ORDER]])
        dmatrix = xgb.DMatrix(vector, feature_names=list(FEATURE_ORDER))

        shap_values = explainer.shap_values(dmatrix)[0]
        expected = float(explainer.expected_value)
        prediction = float(self.model_service.predict(energy, features))

        contributions = [
            {
                "feature": name,
                "value": round(float(features[name]), 4),
                "shap_value": round(float(sv), 4),
            }
            for name, sv in zip(FEATURE_ORDER, shap_values)
        ]
        # Toplam tutarlılık kontrolü
        total = expected + float(np.sum(shap_values))
        consistent = abs(total - prediction) <= max(TOLERANCE, abs(prediction) * 1e-3)

        return {
            "energy": energy,
            "expected_value": round(expected, 4),
            "prediction_value": round(prediction, 4),
            "contributions": sorted(
                contributions, key=lambda c: abs(c["shap_value"]), reverse=True
            ),
            "consistent": consistent,
        }


_shap_service: ShapService | None = None


def get_shap_service() -> ShapService:
    global _shap_service
    if _shap_service is None:
        from app.services.model_service import get_model_service

        _shap_service = ShapService(get_model_service())
    return _shap_service
