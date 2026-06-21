import unicodedata

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from sqlalchemy.orm import Session

from app.core.auth import Principal, get_principal, require_role
from app.core.config import settings
from app.data.repository import get_repository
from app.db.models import AuditLog
from app.db.session import get_db
from app.ml.schema import FEATURE_ORDER
from app.services.report_service import build_district_report
from app.services.shap_service import get_shap_service

router = APIRouter()


@router.get("/district/{district_id}.pdf")
def district_report_pdf(
    district_id: str,
    energy: str = "ges",
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
):
    """İlçe için PDF analiz raporu üretir ve indirir (senkron)."""
    if energy not in ("ges", "res"):
        raise HTTPException(status_code=422, detail="energy 'ges' veya 'res' olmalı")

    repo = get_repository()
    summary = repo.get_summary(district_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="İlçe bulunamadı")

    features = {k: summary[k] for k in FEATURE_ORDER}
    shap = get_shap_service().explain_local(energy, features)

    pdf = build_district_report(
        summary=summary,
        shap=shap,
        data_version=settings.data_version,
        scoring_version=settings.data_version,
    )
    raw_name = f"buraki_{summary['province']}_{summary['district']}.pdf"
    ascii_name = (
        unicodedata.normalize("NFKD", raw_name)
        .encode("ascii", "ignore")
        .decode("ascii")
        .replace(" ", "_")
        .replace("/", "-")
    )
    db.add(
        AuditLog(
            actor=principal.user_id,
            action="report.generate",
            detail={
                "district_id": district_id,
                "district_name": f"{summary['province']} / {summary['district']}",
                "energy": energy,
            },
        )
    )
    db.commit()
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{ascii_name}"'},
    )


@router.get("/history")
def report_history(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("analyst", "developer", "admin")),
    limit: int = 100,
):
    query = db.query(AuditLog).filter(AuditLog.action == "report.generate")
    if principal.role != "admin":
        query = query.filter(AuditLog.actor == principal.user_id)
    rows = query.order_by(AuditLog.created_at.desc()).limit(min(max(limit, 1), 200)).all()
    return [
        {
            "district_id": row.detail.get("district_id", ""),
            "district_name": row.detail.get("district_name", row.detail.get("district_id", "")),
            "energy": row.detail.get("energy", "ges"),
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]
