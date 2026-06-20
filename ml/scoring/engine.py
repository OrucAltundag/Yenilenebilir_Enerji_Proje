"""Deterministik GES/RES skor motoru (config-tabanlı).

Rapor 6'daki metodolojiyi koddan ayırır: tüm normalizasyon sınırları ve ham
skor min/max değerleri ``scoring_config.json`` içinde versiyonlanır. Aynı motor
hem toplu (pipeline) hem tekil (API senaryo) skorlamada kullanılır.

Formül (calculate_scores.py ile birebir):
    norm(x)   = (x - min) / (max - min)
    GES_ham   = norm(ALLSKY)*60 + norm(tesvik)*30 - norm(egim)*10
    GES_skor  = (GES_ham - GES_ham_min) / (GES_ham_max - GES_ham_min) * 100
    (RES için ALLSKY yerine WS10M)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from common.schema import (
    WEIGHT_INCENTIVE,
    WEIGHT_PRODUCTION,
    WEIGHT_SLOPE_PENALTY,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "ml" / "scoring" / "scoring_config.json"


@dataclass(frozen=True)
class ScoringConfig:
    version: str
    bounds: dict[str, dict[str, float]]  # sütun -> {min, max}
    raw_score_bounds: dict[str, dict[str, float]]  # "ges"/"res" -> {min, max}

    @classmethod
    def load(cls, path: Path = DEFAULT_CONFIG) -> "ScoringConfig":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            version=data["version"],
            bounds=data["bounds"],
            raw_score_bounds=data["raw_score_bounds"],
        )


def _norm(value: float, lo: float, hi: float) -> float:
    if hi == lo:
        return 0.0
    return (value - lo) / (hi - lo)


def _raw_score(production_norm: float, tesvik_norm: float, egim_norm: float) -> float:
    return (
        production_norm * WEIGHT_PRODUCTION
        + tesvik_norm * WEIGHT_INCENTIVE
        - egim_norm * WEIGHT_SLOPE_PENALTY
    )


def score_record(features: dict[str, float], config: ScoringConfig) -> dict[str, float]:
    """Tek bir kayıt için GES ve RES skorunu (0–100) döner."""
    b = config.bounds
    allsky_n = _norm(features["ALLSKY_SFC_SW_DWN"], **b["ALLSKY_SFC_SW_DWN"])
    ws_n = _norm(features["WS10M"], **b["WS10M"])
    egim_n = _norm(features["arazi_egimi_yuzde"], **b["arazi_egimi_yuzde"])
    tesvik_n = _norm(features["tesvik_bolgesi"], **b["tesvik_bolgesi"])

    ges_raw = _raw_score(allsky_n, tesvik_n, egim_n)
    res_raw = _raw_score(ws_n, tesvik_n, egim_n)

    gb = config.raw_score_bounds["ges"]
    rb = config.raw_score_bounds["res"]
    ges = _norm(ges_raw, gb["min"], gb["max"]) * 100
    res = _norm(res_raw, rb["min"], rb["max"]) * 100
    return {"ges": round(ges, 2), "res": round(res, 2)}
