"""Faz 6 — Global SHAP özeti (offline artefakt).

Eğitim veri setinden örneklem alıp GES ve RES modelleri için ortalama mutlak
SHAP katkılarını (global özellik önemi) hesaplar ve JSON olarak yazar. Backend
bu artefaktı doğrudan servis eder; 349.305 kayıt için anlık hesaplama yapılmaz
(rapor 8).

Çıktı: data/shap/global_shap_summary.json

Çalıştırma:
    python ml/shap/build_global_shap.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import shap
import xgboost as xgb

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))

from common.schema import FEATURE_ORDER  # noqa: E402

DATA = ROOT / "data"
INPUT = DATA / "processed" / "XGBoost_Egitim_Veriseti_Temiz.csv"
MODELS = {
    "ges": DATA / "models" / "Yapay_Zeka_GES_Modeli.json",
    "res": DATA / "models" / "Yapay_Zeka_RES_Modeli.json",
}
OUTPUT = DATA / "shap" / "global_shap_summary.json"
SAMPLE_SIZE = 2000


def main() -> None:
    df = pd.read_csv(INPUT).sample(n=SAMPLE_SIZE, random_state=42)
    X = df[list(FEATURE_ORDER)].astype(float)

    summary: dict[str, object] = {"sample_size": SAMPLE_SIZE, "models": {}}
    for energy, path in MODELS.items():
        booster = xgb.Booster()
        booster.load_model(str(path))
        explainer = shap.TreeExplainer(booster)
        dmatrix = xgb.DMatrix(X.values, feature_names=list(FEATURE_ORDER))
        shap_values = explainer.shap_values(dmatrix)

        mean_abs = np.abs(shap_values).mean(axis=0)
        importance = sorted(
            (
                {"feature": f, "mean_abs_shap": round(float(v), 4)}
                for f, v in zip(FEATURE_ORDER, mean_abs)
            ),
            key=lambda d: d["mean_abs_shap"],
            reverse=True,
        )
        summary["models"][energy] = {
            "expected_value": round(float(explainer.expected_value), 4),
            "feature_importance": importance,
        }
        print(f"[{energy.upper()}] en etkili 3 özellik:")
        for item in importance[:3]:
            print(f"   {item['feature']}: {item['mean_abs_shap']}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> Global SHAP özeti: {OUTPUT.name}")


if __name__ == "__main__":
    main()
