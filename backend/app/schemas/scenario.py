from pydantic import BaseModel


class ScenarioRequest(BaseModel):
    district_id: str
    year: int = 2023
    overrides: dict[str, float]


class ScenarioResult(BaseModel):
    district_id: str
    baseline_ges: float | None = None
    baseline_res: float | None = None
    scenario_ges: float | None = None
    scenario_res: float | None = None
    delta_ges: float | None = None
    delta_res: float | None = None
    scoring_version: str
