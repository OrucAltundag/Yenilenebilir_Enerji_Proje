"""Deterministik skor motoru.

Rapora göre üretimin birincil skor kaynağı bu modül olmalı; XGBoost yardımcı
motor olarak kullanılır. Formülasyon ve normalizasyon sabitleri scoring_config
artefaktında versiyonlanır.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoringConfig:
    version: str
    weights: dict[str, float]
    norm_bounds: dict[str, tuple[float, float]]


class ScoreService:
    def __init__(self, config: ScoringConfig) -> None:
        self.config = config

    def compute_ges(self, features: dict[str, float]) -> float:
        raise NotImplementedError

    def compute_res(self, features: dict[str, float]) -> float:
        raise NotImplementedError
