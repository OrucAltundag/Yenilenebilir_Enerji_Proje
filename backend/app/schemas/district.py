from pydantic import BaseModel, Field


class DistrictItem(BaseModel):
    district_id: str
    province: str
    district: str


class DistrictSearchResponse(BaseModel):
    items: list[DistrictItem]
    total: int


class DistrictCompareRequest(BaseModel):
    district_ids: list[str] = Field(min_length=2, max_length=5)
    year: int = Field(default=2023, ge=2000, le=2100)


class MonthlyPoint(BaseModel):
    ay: int
    ges_mean: float
    res_mean: float


class DistrictSummary(BaseModel):
    district_id: str
    province: str
    district: str
    year: int
    ges_score_mean: float | None = None
    res_score_mean: float | None = None
    national_rank_ges: int | None = None
    national_rank_res: int | None = None
    percentile_ges: float | None = None
    percentile_res: float | None = None
    features: dict[str, float] = Field(default_factory=dict)
    monthly: list[MonthlyPoint] = Field(default_factory=list)
    data_version: str | None = None
    scoring_version: str | None = None
