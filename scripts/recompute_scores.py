"""Skor sütunlarını yeni ağırlıklarla yeniden hesaplayan tek seferlik araç.

2026-06-21 revizyonu:
    - Üretim ağırlığı  60 → 80
    - Teşvik ağırlığı  30 → 10  (etki minimalize)
    - Eğim cezası     -10 (sabit)

Çalıştırma:
    cd <repo-root>
    python scripts/recompute_scores.py

İşledikleri:
    - data/processed/XGBoost_Egitim_Veriseti_Temiz.csv (build_summary girdisi)
    - data/processed/XGBoost_Egitim_Veriseti_Duzeltilmis.csv (training girdisi)
    - ml/scoring/scoring_config.json (weights + raw_score_bounds güncellenir)

Sıra: normalize edilirken aynı dataset üzerindeki min/max kullanılır; hem GES
hem RES için ham skor min/max değerleri config'e yazılır — backend canlı
senaryo simülasyonu bu bounds ile çalışacaktır.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml"))

from common.schema import (  # noqa: E402
    WEIGHT_INCENTIVE,
    WEIGHT_PRODUCTION,
    WEIGHT_SLOPE_PENALTY,
)

DATA = ROOT / "data" / "processed"
CONFIG_PATH = ROOT / "ml" / "scoring" / "scoring_config.json"

TARGETS = [
    DATA / "XGBoost_Egitim_Veriseti_Temiz.csv",
    DATA / "XGBoost_Egitim_Veriseti_Duzeltilmis.csv",
    DATA / "XGBoost_Egitim_Veriseti_Guncel.csv",
    DATA / "XGBoost_Egitim_Veriseti_Final.csv",
]

NORM_COLS = ("ALLSKY_SFC_SW_DWN", "WS10M", "arazi_egimi_yuzde", "tesvik_bolgesi")


def _normalize(series: pd.Series, lo: float, hi: float) -> pd.Series:
    if hi == lo:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - lo) / (hi - lo)


def _load_bounds() -> dict[str, dict[str, float]]:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return cfg["bounds"]


def _recompute(path: Path, bounds: dict[str, dict[str, float]]) -> tuple[float, float, float, float]:
    df = pd.read_csv(path)
    for col in NORM_COLS:
        if col not in df.columns:
            raise SystemExit(f"{path.name}: beklenen sütun yok: {col}")
    if "arazi_egimi_yuzde" in df.columns:
        df["arazi_egimi_yuzde"] = df["arazi_egimi_yuzde"].fillna(
            df["arazi_egimi_yuzde"].mean()
        )

    allsky_n = _normalize(df["ALLSKY_SFC_SW_DWN"], **bounds["ALLSKY_SFC_SW_DWN"])
    ws_n = _normalize(df["WS10M"], **bounds["WS10M"])
    egim_n = _normalize(df["arazi_egimi_yuzde"], **bounds["arazi_egimi_yuzde"])
    tesvik_n = _normalize(df["tesvik_bolgesi"], **bounds["tesvik_bolgesi"])

    ges_raw = (
        allsky_n * WEIGHT_PRODUCTION
        + tesvik_n * WEIGHT_INCENTIVE
        - egim_n * WEIGHT_SLOPE_PENALTY
    )
    res_raw = (
        ws_n * WEIGHT_PRODUCTION
        + tesvik_n * WEIGHT_INCENTIVE
        - egim_n * WEIGHT_SLOPE_PENALTY
    )

    ges_min, ges_max = float(ges_raw.min()), float(ges_raw.max())
    res_min, res_max = float(res_raw.min()), float(res_raw.max())

    ges_score = ((ges_raw - ges_min) / (ges_max - ges_min)) * 100.0
    res_score = ((res_raw - res_min) / (res_max - res_min)) * 100.0

    df["GES_YATIRIM_SKORU"] = ges_score.round(2)
    df["RES_YATIRIM_SKORU"] = res_score.round(2)

    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(
        f"{path.name}: {len(df)} satır → "
        f"GES raw=[{ges_min:.3f}, {ges_max:.3f}] · RES raw=[{res_min:.3f}, {res_max:.3f}]"
    )
    return ges_min, ges_max, res_min, res_max


def _write_config(
    weights: dict[str, float],
    raw_bounds: dict[str, dict[str, float]],
) -> None:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    cfg["weights"] = weights
    cfg["raw_score_bounds"] = raw_bounds
    CONFIG_PATH.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"scoring_config.json güncellendi → weights={weights}")


def main() -> None:
    print(
        f"Ağırlıklar: üretim={WEIGHT_PRODUCTION}, teşvik={WEIGHT_INCENTIVE}, "
        f"eğim cezası=-{WEIGHT_SLOPE_PENALTY}"
    )
    bounds = _load_bounds()
    primary = TARGETS[0]
    ges_min, ges_max, res_min, res_max = _recompute(primary, bounds)
    # Diğer datasetler için (training dataset) aynı min/max'a bağlı olarak işlenir
    for extra in TARGETS[1:]:
        if extra.exists():
            _recompute(extra, bounds)
        else:
            print(f"{extra.name}: bulunamadı, atlandı")

    weights = {
        "uretim_potansiyeli": WEIGHT_PRODUCTION,
        "tesvik_avantaji": WEIGHT_INCENTIVE,
        "egim_cezasi": -WEIGHT_SLOPE_PENALTY,
    }
    raw_bounds = {
        "ges": {"min": ges_min, "max": ges_max},
        "res": {"min": res_min, "max": res_max},
    }
    _write_config(weights, raw_bounds)


if __name__ == "__main__":
    main()
