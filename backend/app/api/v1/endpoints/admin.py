"""Yönetici endpointleri: veri sürümü yayınlama/geri alma + audit log.

Rapor 4.2: staging/published ayrımı, pointer swap, rollback aktif pointer'ı
değiştirir (veri silmez), her işlem audit log üretir. Sadece admin rolü erişir.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_role
from app.db.models import AuditLog, DatasetVersion
from app.db.session import get_db

router = APIRouter()


class PublishRequest(BaseModel):
    version: str
    district_count: int | None = None
    area_zero: int | None = None


def _audit(db: Session, actor: str, action: str, detail: dict) -> None:
    db.add(AuditLog(actor=actor, action=action, detail=detail))


@router.get("/dataset/active")
def active_dataset(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("admin")),
):
    active = db.query(DatasetVersion).filter(DatasetVersion.is_active.is_(True)).first()
    if active is None:
        return {"active": None}
    return {"active": active.version, "status": active.status}


@router.post("/dataset/publish")
def publish_dataset(
    payload: PublishRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("admin")),
):
    # Kalite kapısı (rapor 10): 957 ilçe ve 0 sıfır alan beklenir
    if payload.district_count is not None and payload.district_count != 957:
        raise HTTPException(status_code=422, detail="district_count 957 olmalı")
    if payload.area_zero not in (None, 0):
        raise HTTPException(status_code=422, detail="area_zero 0 olmalı")

    existing = (
        db.query(DatasetVersion)
        .filter(DatasetVersion.version == payload.version)
        .first()
    )
    if existing is None:
        existing = DatasetVersion(version=payload.version)
        db.add(existing)
    existing.status = "published"
    existing.district_count = payload.district_count
    existing.area_zero = payload.area_zero

    # Pointer swap: önceki aktifi pasifleştir
    db.query(DatasetVersion).update({DatasetVersion.is_active: False})
    existing.is_active = True

    _audit(db, principal.user_id, "dataset.publish", {"version": payload.version})
    db.commit()
    return {"active": payload.version, "status": "published"}


@router.post("/dataset/rollback")
def rollback_dataset(
    version: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("admin")),
):
    target = (
        db.query(DatasetVersion)
        .filter(DatasetVersion.version == version)
        .first()
    )
    if target is None:
        raise HTTPException(status_code=404, detail="Sürüm bulunamadı")
    db.query(DatasetVersion).update({DatasetVersion.is_active: False})
    target.is_active = True
    _audit(db, principal.user_id, "dataset.rollback", {"version": version})
    db.commit()
    return {"active": version}


@router.get("/audit")
def audit_log(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("admin")),
    limit: int = 50,
):
    rows = (
        db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    )
    return [
        {
            "actor": r.actor,
            "action": r.action,
            "detail": r.detail,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
