"""Model registry servis katmanı (aktif model yönetimi, karşılaştırma)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import AuditLog, ModelRegistry


def _audit(db: Session, actor: str, action: str, detail: dict) -> None:
    db.add(AuditLog(actor=actor, action=action, detail=detail))


def list_models(
    db: Session,
    energy: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[ModelRegistry]:
    q = db.query(ModelRegistry)
    if energy:
        q = q.filter(ModelRegistry.energy_type == energy)
    if status:
        q = q.filter(ModelRegistry.status == status)
    return q.order_by(ModelRegistry.created_at.desc()).limit(limit).all()


def get_model(db: Session, model_id: int) -> ModelRegistry:
    model = db.get(ModelRegistry, model_id)
    if model is None:
        raise HTTPException(status_code=404, detail="Model bulunamadı")
    return model


def active_models(db: Session) -> list[ModelRegistry]:
    return (
        db.query(ModelRegistry)
        .filter(ModelRegistry.status == "active")
        .order_by(ModelRegistry.energy_type.asc())
        .all()
    )


def mark_candidate(
    db: Session, model_id: int, actor: str, note: str | None = None
) -> ModelRegistry:
    model = get_model(db, model_id)
    if model.status not in {"completed", "archived"}:
        raise HTTPException(
            status_code=400,
            detail=f"Aday gösterilemez (status={model.status})",
        )
    model.status = "candidate"
    if note:
        model.notes = note
    _audit(
        db,
        actor,
        "ml.model.candidate",
        {"model_id": model.id, "version": model.model_version},
    )
    db.commit()
    db.refresh(model)
    return model


def activate(
    db: Session, model_id: int, actor: str, note: str | None = None
) -> ModelRegistry:
    model = get_model(db, model_id)
    if model.status not in {"candidate", "completed"}:
        raise HTTPException(
            status_code=400,
            detail=f"Aktif yapılamaz (status={model.status})",
        )
    # Aynı enerji türündeki diğer aktif modeli arşivle
    others = (
        db.query(ModelRegistry)
        .filter(
            ModelRegistry.energy_type == model.energy_type,
            ModelRegistry.status == "active",
            ModelRegistry.id != model.id,
        )
        .all()
    )
    for other in others:
        other.status = "archived"
    model.status = "active"
    model.activated_at = datetime.now(timezone.utc)
    if note:
        model.notes = note
    _audit(
        db,
        actor,
        "ml.model.activate",
        {
            "model_id": model.id,
            "version": model.model_version,
            "energy": model.energy_type,
            "archived_ids": [o.id for o in others],
        },
    )
    db.commit()
    db.refresh(model)
    return model


def archive(
    db: Session, model_id: int, actor: str, note: str | None = None
) -> ModelRegistry:
    model = get_model(db, model_id)
    model.status = "archived"
    if note:
        model.notes = note
    _audit(
        db,
        actor,
        "ml.model.archive",
        {"model_id": model.id, "version": model.model_version},
    )
    db.commit()
    db.refresh(model)
    return model


def compare(db: Session, left_id: int, right_id: int) -> dict:
    left = get_model(db, left_id)
    right = get_model(db, right_id)

    metric_diff: dict[str, float] = {}
    for key in {*left.metrics.keys(), *right.metrics.keys()}:
        try:
            metric_diff[key] = float(right.metrics.get(key, 0.0)) - float(
                left.metrics.get(key, 0.0)
            )
        except (TypeError, ValueError):
            continue

    importance_diff: dict[str, float] = {}
    keys: Iterable[str] = set(left.feature_importance) | set(right.feature_importance)
    for k in keys:
        importance_diff[k] = float(right.feature_importance.get(k, 0.0)) - float(
            left.feature_importance.get(k, 0.0)
        )

    return {
        "left": left,
        "right": right,
        "metric_diff": metric_diff,
        "feature_importance_diff": importance_diff,
    }
