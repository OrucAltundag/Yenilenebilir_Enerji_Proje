from pydantic import BaseModel


class ShapRequest(BaseModel):
    energy: str
    features: dict[str, float]
    model_version: str | None = None


class ShapContribution(BaseModel):
    feature: str
    value: float
    shap_value: float


class ShapExplanation(BaseModel):
    energy: str
    expected_value: float
    prediction_value: float
    contributions: list[ShapContribution]
    model_version: str
    data_version: str | None = None
