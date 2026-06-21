"""ML / Developer paneli için Pydantic şemaları."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

EnergyTarget = Literal["ges", "res"]
JobStatus = Literal["queued", "running", "completed", "failed"]
ModelStatus = Literal["completed", "candidate", "active", "archived", "failed"]


class TrainingJobCreate(BaseModel):
    energy_targets: list[EnergyTarget] = Field(default_factory=lambda: ["ges", "res"])
    dataset_version: str | None = None
    test_size: float = 0.2
    random_state: int = 42
    n_estimators: int = 400
    learning_rate: float = 0.05
    max_depth: int = 6
    note: str | None = None
    register_model: bool = True
    generate_shap: bool = False
    quick_mode: bool = True  # küçük veri/kısa eğitim


class TrainingJobSummary(BaseModel):
    id: int
    status: JobStatus
    requested_by: str
    dataset_version: str | None
    energy_targets: list[str]
    note: str | None
    started_at: datetime | None
    finished_at: datetime | None
    duration_seconds: float | None
    created_at: datetime


class TrainingJobDetail(TrainingJobSummary):
    parameters: dict[str, Any]
    error_message: str | None
    log_text: str | None
    result_models: dict[str, Any]


class ModelSummary(BaseModel):
    id: int
    model_version: str
    energy_type: EnergyTarget
    status: ModelStatus
    dataset_version: str | None
    scoring_version: str | None
    metrics: dict[str, float]
    created_by: str
    created_at: datetime
    activated_at: datetime | None
    training_job_id: int | None
    notes: str | None


class ModelDetail(ModelSummary):
    artifact_path: str | None
    feature_names: list[str]
    feature_importance: dict[str, float]
    parameters: dict[str, Any]


class ModelStatusChange(BaseModel):
    note: str | None = None


class ModelCompareResponse(BaseModel):
    left: ModelDetail
    right: ModelDetail
    metric_diff: dict[str, float]
    feature_importance_diff: dict[str, float]


class DataQualityReport(BaseModel):
    total_rows: int
    district_count: int
    missing_values: int
    zero_area_count: int
    outlier_count: int
    dataset_version: str
    sources: list[str]
    warnings: list[str]
