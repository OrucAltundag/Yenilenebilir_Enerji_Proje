from pydantic import BaseModel


class ScoreMapItem(BaseModel):
    district_id: str
    province: str
    district: str
    score: float
    percentile: float | None = None


class ScoreMapResponse(BaseModel):
    energy: str
    year: int
    period: str
    items: list[ScoreMapItem]


class ScoreRankingResponse(BaseModel):
    energy: str
    year: int
    items: list[ScoreMapItem]
