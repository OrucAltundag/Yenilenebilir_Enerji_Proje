"""Deterministik skor servis katmanı.

Rapora göre üretimin birincil skor kaynağı bu modül olmalı; XGBoost yardımcı
motor olarak kullanılır. Formülasyon ve normalizasyon sabitleri scoring_config
artefaktında versiyonlanır.
"""

from app.ml.scoring_engine import ScoringConfig, score_record


class ScoreService:
    def __init__(self, config: ScoringConfig) -> None:
        self.config = config

    def compute_ges(self, features: dict[str, float]) -> float:
        return score_record(features, self.config)["ges"]

    def compute_res(self, features: dict[str, float]) -> float:
        return score_record(features, self.config)["res"]
