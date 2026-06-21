"""Developer / ML paneli endpoint'leri.

Yetkilendirme:
- training-jobs, models, data-quality: developer veya admin
- model activate, archive: yalnız admin
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_role
from app.core.config import settings
from app.db.models import AuditLog, ModelRegistry, TrainingJob
from app.db.session import get_db
from app.schemas.ml import (
    DataQualityReport,
    ModelCompareResponse,
    ModelDetail,
    ModelStatusChange,
    ModelSummary,
    TrainingJobCreate,
    TrainingJobDetail,
    TrainingJobSummary,
)
from app.services import model_registry_service, training_service

router = APIRouter()


def _job_summary(job: TrainingJob) -> TrainingJobSummary:
    return TrainingJobSummary(
        id=job.id,
        status=job.status,  # type: ignore[arg-type]
        requested_by=job.requested_by,
        dataset_version=job.dataset_version,
        energy_targets=list(job.energy_targets or []),
        note=job.note,
        started_at=job.started_at,
        finished_at=job.finished_at,
        duration_seconds=job.duration_seconds,
        created_at=job.created_at,
    )


def _job_detail(job: TrainingJob) -> TrainingJobDetail:
    base = _job_summary(job)
    return TrainingJobDetail(
        **base.model_dump(),
        parameters=dict(job.parameters or {}),
        error_message=job.error_message,
        log_text=job.log_text,
        result_models=dict(job.result_models or {}),
    )


def _model_summary(model: ModelRegistry) -> ModelSummary:
    return ModelSummary(
        id=model.id,
        model_version=model.model_version,
        energy_type=model.energy_type,  # type: ignore[arg-type]
        status=model.status,  # type: ignore[arg-type]
        dataset_version=model.dataset_version,
        scoring_version=model.scoring_version,
        metrics={k: float(v) for k, v in (model.metrics or {}).items() if isinstance(v, (int, float))},
        created_by=model.created_by,
        created_at=model.created_at,
        activated_at=model.activated_at,
        training_job_id=model.training_job_id,
        notes=model.notes,
    )


def _model_detail(model: ModelRegistry) -> ModelDetail:
    base = _model_summary(model)
    return ModelDetail(
        **base.model_dump(),
        artifact_path=model.artifact_path,
        feature_names=list(model.feature_names or []),
        feature_importance={
            k: float(v) for k, v in (model.feature_importance or {}).items()
        },
        parameters=dict(model.parameters or {}),
    )


# ---------- Training Jobs ----------


@router.get("/training-jobs", response_model=list[TrainingJobSummary])
def list_training_jobs(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("developer", "admin")),
    limit: int = Query(50, ge=1, le=200),
):
    rows = (
        db.query(TrainingJob)
        .order_by(TrainingJob.created_at.desc())
        .limit(limit)
        .all()
    )
    return [_job_summary(r) for r in rows]


@router.post("/training-jobs", response_model=TrainingJobDetail, status_code=201)
def create_training_job(
    payload: TrainingJobCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("developer", "admin")),
):
    job = training_service.create_job(db, principal.user_id, payload)
    background.add_task(training_service.run_job_async, job.id)
    return _job_detail(job)


@router.get("/training-jobs/{job_id}", response_model=TrainingJobDetail)
def get_training_job(
    job_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("developer", "admin")),
):
    job = db.get(TrainingJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job bulunamadı")
    return _job_detail(job)


@router.get("/training-jobs/{job_id}/logs")
def get_training_job_logs(
    job_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("developer", "admin")),
):
    job = db.get(TrainingJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job bulunamadı")
    return {
        "job_id": job.id,
        "status": job.status,
        "log": job.log_text or "",
        "error": job.error_message,
    }


# ---------- Models ----------


@router.get("/approvals", response_model=list[ModelSummary])
def model_approvals(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("developer", "admin")),
):
    rows = (
        db.query(ModelRegistry)
        .filter(ModelRegistry.status == "candidate")
        .order_by(ModelRegistry.created_at.desc())
        .all()
    )
    return [_model_summary(row) for row in rows]


@router.get("/models", response_model=list[ModelSummary])
def list_models(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("developer", "admin")),
    energy: str | None = Query(None, pattern="^(ges|res)$"),
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
):
    rows = model_registry_service.list_models(db, energy, status, limit)
    return [_model_summary(r) for r in rows]


@router.get("/models/active", response_model=list[ModelSummary])
def list_active_models(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("developer", "admin")),
):
    return [_model_summary(m) for m in model_registry_service.active_models(db)]


@router.get("/models/compare", response_model=ModelCompareResponse)
def compare_models(
    left_id: int = Query(...),
    right_id: int = Query(...),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("developer", "admin")),
):
    raw = model_registry_service.compare(db, left_id, right_id)
    return ModelCompareResponse(
        left=_model_detail(raw["left"]),
        right=_model_detail(raw["right"]),
        metric_diff=raw["metric_diff"],
        feature_importance_diff=raw["feature_importance_diff"],
    )


@router.get("/models/{model_id}", response_model=ModelDetail)
def get_model(
    model_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("developer", "admin")),
):
    return _model_detail(model_registry_service.get_model(db, model_id))


@router.post("/models/{model_id}/mark-candidate", response_model=ModelSummary)
def mark_candidate(
    model_id: int,
    payload: ModelStatusChange,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("developer", "admin")),
):
    return _model_summary(
        model_registry_service.mark_candidate(db, model_id, principal.user_id, payload.note)
    )


@router.post("/models/{model_id}/activate", response_model=ModelSummary)
def activate_model(
    model_id: int,
    payload: ModelStatusChange,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("admin")),
):
    return _model_summary(
        model_registry_service.activate(db, model_id, principal.user_id, payload.note)
    )


@router.post("/models/{model_id}/archive", response_model=ModelSummary)
def archive_model(
    model_id: int,
    payload: ModelStatusChange,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("admin")),
):
    return _model_summary(
        model_registry_service.archive(db, model_id, principal.user_id, payload.note)
    )


# ---------- Data quality ----------


@router.get("/logs")
def technical_logs(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("developer", "admin")),
    limit: int = Query(100, ge=1, le=200),
):
    jobs = db.query(TrainingJob).order_by(TrainingJob.created_at.desc()).limit(limit).all()
    audits_query = db.query(AuditLog)
    if principal.role != "admin":
        audits_query = audits_query.filter(AuditLog.actor == principal.user_id)
    audits = audits_query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    items = [
        {
            "id": f"training-{job.id}",
            "source": "training",
            "level": "error" if job.status == "failed" else "info",
            "message": job.error_message or job.log_text or f"Eğitim durumu: {job.status}",
            "actor": job.requested_by,
            "created_at": job.created_at.isoformat(),
        }
        for job in jobs
    ]
    items.extend(
        {
            "id": f"audit-{row.id}",
            "source": "audit",
            "level": "info",
            "message": f"{row.action}: {row.detail}",
            "actor": row.actor,
            "created_at": row.created_at.isoformat(),
        }
        for row in audits
    )
    return sorted(items, key=lambda item: item["created_at"], reverse=True)[:limit]


@router.get("/data-quality/latest", response_model=DataQualityReport)
def data_quality_latest(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("developer", "admin")),
):
    report_path: Path = settings.data_dir / "processed" / "data_quality_report.json"
    warnings: list[str] = []
    total_rows = 0
    district_count = 0
    missing_values = 0
    zero_area_count = 0
    outlier_count = 0
    sources: list[str] = []
    dataset_version = settings.data_version

    if report_path.exists():
        import json

        try:
            raw = json.loads(report_path.read_text(encoding="utf-8"))
            total_rows = int(raw.get("total_rows", raw.get("row_count", 0)) or 0)
            district_count = int(raw.get("district_count", 0) or 0)
            missing_values = int(raw.get("missing_values", 0) or 0)
            zero_area_count = int(raw.get("zero_area_count", raw.get("area_zero", 0)) or 0)
            outlier_count = int(raw.get("outlier_count", 0) or 0)
            sources = list(raw.get("sources", []))
            warnings = list(raw.get("warnings", []))
            dataset_version = raw.get("dataset_version", dataset_version)
        except Exception as exc:
            warnings.append(f"Rapor okunamadı: {exc}")
    else:
        warnings.append("data_quality_report.json bulunamadı; veri seti taranamadı")

    return DataQualityReport(
        total_rows=total_rows,
        district_count=district_count,
        missing_values=missing_values,
        zero_area_count=zero_area_count,
        outlier_count=outlier_count,
        dataset_version=dataset_version,
        sources=sources,
        warnings=warnings,
    )
