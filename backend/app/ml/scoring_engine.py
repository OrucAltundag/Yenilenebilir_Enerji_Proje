"""Deterministik skor motoru (backend kopyası).

ml/scoring/engine.py ile aynı formülü uygular; scoring_config.json'dan sınırları
okur. Senaryo simülasyonu ve doğrulama için kullanılır.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.ml.schema import (
    WEIGHT_INCENTIVE,
    WEIGHT_PRODUCTION,
    WEIGHT_SLOPE_PENALTY,
)


@dataclass(frozen=True)
class ScoringConfig:
    version: str
    bounds: dict[str, dict[str, float]]
    raw_score_bounds: dict[str, dict[str, float]]

    @classmethod
    def load(cls, path: Path) -> "ScoringConfig":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            version=data["version"],
            bounds=data["bounds"],
            raw_score_bounds=data["raw_score_bounds"],
        )


def _norm(value: float, lo: float, hi: float) -> float:
    return 0.0 if hi == lo else (value - lo) / (hi - lo)


def score_record(features: dict[str, float], config: ScoringConfig) -> dict[str, float]:
    b = config.bounds
    allsky_n = _norm(features["ALLSKY_SFC_SW_DWN"], **b["ALLSKY_SFC_SW_DWN"])
    ws_n = _norm(features["WS10M"], **b["WS10M"])
    egim_n = _norm(features["arazi_egimi_yuzde"], **b["arazi_egimi_yuzde"])
    tesvik_n = _norm(features["tesvik_bolgesi"], **b["tesvik_bolgesi"])

    ges_raw = allsky_n * WEIGHT_PRODUCTION + tesvik_n * WEIGHT_INCENTIVE - egim_n * WEIGHT_SLOPE_PENALTY
    res_raw = ws_n * WEIGHT_PRODUCTION + tesvik_n * WEIGHT_INCENTIVE - egim_n * WEIGHT_SLOPE_PENALTY

    gb = config.raw_score_bounds["ges"]
    rb = config.raw_score_bounds["res"]
    return {
        "ges": round(_norm(ges_raw, gb["min"], gb["max"]) * 100, 2),
        "res": round(_norm(res_raw, rb["min"], rb["max"]) * 100, 2),
    }
