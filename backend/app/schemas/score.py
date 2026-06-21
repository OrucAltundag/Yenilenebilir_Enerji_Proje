from typing import Literal

from pydantic import BaseModel

Energy = Literal["ges", "res"]


class ScoreMapItem(BaseModel):
    district_id: str
    province: str
    district: str
    score: float
    percentile: float | None = None


class ScoreMapResponse(BaseModel):
    energy: Energy
    year: int
    period: str
    items: list[ScoreMapItem]


class ScoreRankingResponse(BaseModel):
    energy: Energy
    year: int
    items: list[ScoreMapItem]
