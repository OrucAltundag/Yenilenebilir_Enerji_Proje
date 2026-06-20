import unicodedata

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.core.auth import current_user
from app.core.config import settings
from app.data.repository import get_repository
from app.ml.schema import FEATURE_ORDER
from app.services.report_service import build_district_report
from app.services.shap_service import get_shap_service

router = APIRouter()


@router.get("/district/{district_id}.pdf")
def district_report_pdf(
    district_id: str,
    energy: str = "ges",
    user: str = Depends(current_user),
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
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{ascii_name}"'},
    )
