"""Faz 2 — scoring_config.json üretimi.

Veri setinden 4 normalize sütununun min/max sınırlarını ve GES/RES ham skor
min/max değerlerini hesaplayıp versiyonlanmış scoring_config.json'a yazar.
calculate_scores.py'deki MinMaxScaler + ham skor ölçekleme mantığını birebir
yeniden üretir.

Çalıştırma:
    python ml/scoring/build_config.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))

from common.schema import (  # noqa: E402
    SCORE_NORM_COLUMNS,
    WEIGHT_INCENTIVE,
    WEIGHT_PRODUCTION,
    WEIGHT_SLOPE_PENALTY,
)

INPUT = ROOT / "data" / "processed" / "XGBoost_Egitim_Veriseti_Guncel.csv"
OUTPUT = ROOT / "ml" / "scoring" / "scoring_config.json"
VERSION = "2023.1"


def main() -> None:
    df = pd.read_csv(INPUT)
    df["arazi_egimi_yuzde"] = df["arazi_egimi_yuzde"].fillna(
        df["arazi_egimi_yuzde"].mean()
    )

    bounds = {
        col: {"lo": float(df[col].min()), "hi": float(df[col].max())}
        for col in SCORE_NORM_COLUMNS
    }

    def norm(col: str) -> pd.Series:
        lo, hi = bounds[col]["lo"], bounds[col]["hi"]
        return (df[col] - lo) / (hi - lo)

    ges_raw = (
        norm("ALLSKY_SFC_SW_DWN") * WEIGHT_PRODUCTION
        + norm("tesvik_bolgesi") * WEIGHT_INCENTIVE
        - norm("arazi_egimi_yuzde") * WEIGHT_SLOPE_PENALTY
    )
    res_raw = (
        norm("WS10M") * WEIGHT_PRODUCTION
        + norm("tesvik_bolgesi") * WEIGHT_INCENTIVE
        - norm("arazi_egimi_yuzde") * WEIGHT_SLOPE_PENALTY
    )

    config = {
        "version": VERSION,
        "data_period": "2023-01-01..2023-12-31",
        "weights": {
            "uretim_potansiyeli": WEIGHT_PRODUCTION,
            "tesvik_avantaji": WEIGHT_INCENTIVE,
            "egim_cezasi": -WEIGHT_SLOPE_PENALTY,
        },
        "bounds": {
            col: {"lo": bounds[col]["lo"], "hi": bounds[col]["hi"]}
            for col in SCORE_NORM_COLUMNS
        },
        "raw_score_bounds": {
            "ges": {"min": float(ges_raw.min()), "max": float(ges_raw.max())},
            "res": {"min": float(res_raw.min()), "max": float(res_raw.max())},
        },
        "score_bands": [
            {"label": "Çok Yüksek", "min": 80, "max": 100},
            {"label": "Yüksek", "min": 60, "max": 80},
            {"label": "Orta", "min": 40, "max": 60},
            {"label": "Düşük", "min": 20, "max": 40},
            {"label": "Çok Düşük", "min": 0, "max": 20},
        ],
    }

    OUTPUT.write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"scoring_config.json yazıldı (sürüm {VERSION})")
    print("Sınırlar:")
    for col, b in config["bounds"].items():
        print(f"  {col}: [{b['lo']:.4f}, {b['hi']:.4f}]")
    print(f"GES ham skor: [{ges_raw.min():.4f}, {ges_raw.max():.4f}]")
    print(f"RES ham skor: [{res_raw.min():.4f}, {res_raw.max():.4f}]")


if __name__ == "__main__":
    main()
