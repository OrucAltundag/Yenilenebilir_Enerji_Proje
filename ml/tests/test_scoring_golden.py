"""Golden test — deterministik motor CSV'deki skorları yeniden üretmeli.

scoring_config.json kullanılarak hesaplanan GES/RES skorları, veri setindeki
GES_YATIRIM_SKORU / RES_YATIRIM_SKORU sütunlarıyla tolerans içinde eşleşmelidir.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))

from scoring.engine import ScoringConfig, score_record  # noqa: E402

DATA = ROOT / "data" / "processed" / "XGBoost_Egitim_Veriseti_Guncel.csv"
TOLERANCE = 0.05  # yuvarlama kaynaklı puan farkı toleransı


@pytest.fixture(scope="module")
def sample() -> pd.DataFrame:
    df = pd.read_csv(DATA)
    df["arazi_egimi_yuzde"] = df["arazi_egimi_yuzde"].fillna(
        df["arazi_egimi_yuzde"].mean()
    )
    return df.sample(n=500, random_state=7).reset_index(drop=True)


def test_engine_reproduces_csv_scores(sample: pd.DataFrame) -> None:
    config = ScoringConfig.load()
    max_ges_diff = 0.0
    max_res_diff = 0.0
    for _, row in sample.iterrows():
        result = score_record(row.to_dict(), config)
        max_ges_diff = max(max_ges_diff, abs(result["ges"] - row["GES_YATIRIM_SKORU"]))
        max_res_diff = max(max_res_diff, abs(result["res"] - row["RES_YATIRIM_SKORU"]))

    assert max_ges_diff <= TOLERANCE, f"GES sapması çok yüksek: {max_ges_diff}"
    assert max_res_diff <= TOLERANCE, f"RES sapması çok yüksek: {max_res_diff}"


def test_score_bounds(sample: pd.DataFrame) -> None:
    config = ScoringConfig.load()
    for _, row in sample.head(50).iterrows():
        result = score_record(row.to_dict(), config)
        assert 0.0 <= result["ges"] <= 100.0
        assert 0.0 <= result["res"] <= 100.0
