from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    note: str | None = Field(default=None, max_length=1000)
    district_ids: list[str] = Field(default_factory=list)
    energy: str = "ges"


class ProjectOut(BaseModel):
    id: int
    owner_id: str
    name: str
    note: str | None
    district_ids: list[str]
    energy: str
    created_at: datetime

    class Config:
        from_attributes = True


class ScenarioSaveRequest(BaseModel):
    district_id: str
    overrides: dict[str, float]
    project_id: int | None = None


class ScenarioOut(BaseModel):
    id: int
    owner_id: str
    project_id: int | None
    district_id: str
    overrides: dict
    input_snapshot: dict
    result: dict
    scoring_version: str
    created_at: datetime

    class Config:
        from_attributes = True
