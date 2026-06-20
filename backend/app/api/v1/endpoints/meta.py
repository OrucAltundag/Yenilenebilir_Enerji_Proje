"""Gözlemlenebilirlik: readiness ve temel ürün metrikleri (rapor 10).

readyz: veri kaynakları yüklü mü, model yüklü mü, kalite değişmezleri sağlanıyor mu
(district_count==957, area_zero==0). Bu değişmezler bozulursa alarm üretilmelidir.
"""

from __future__ import annotations

from fastapi import APIRouter, Response

from app.core.config import settings
from app.data.repository import get_repository
from app.services.model_service import get_model_service

router = APIRouter()

EXPECTED_DISTRICTS = 957


@router.get("/readyz")
def readyz():
    checks: dict[str, bool] = {}
    detail: dict[str, object] = {}

    try:
        repo = get_repository()
        district_count = repo.count_districts()
        checks["data_loaded"] = district_count > 0
        checks["district_count_ok"] = district_count == EXPECTED_DISTRICTS
        detail["district_count"] = district_count
    except Exception as exc:  # noqa: BLE001
        checks["data_loaded"] = False
        detail["data_error"] = str(exc)

    checks["district_geometry"] = settings.district_geometry_path.exists()
    if checks["district_geometry"]:
        detail["district_geometry_bytes"] = settings.district_geometry_path.stat().st_size

    try:
        ms = get_model_service()
        checks["ges_model"] = ms.is_loaded("ges")
        checks["res_model"] = ms.is_loaded("res")
    except Exception as exc:  # noqa: BLE001
        checks["ges_model"] = False
        checks["res_model"] = False
        detail["model_error"] = str(exc)

    ready = all(checks.values())
    return {"ready": ready, "checks": checks, "detail": detail, "version": settings.data_version}


@router.get("/metrics")
def metrics():
    """Prometheus uyumlu sade metrik çıktısı."""
    repo = get_repository()
    lines = [
        "# HELP buraki_district_count Yüklü ilçe sayısı",
        "# TYPE buraki_district_count gauge",
        f"buraki_district_count {repo.count_districts()}",
        "# HELP buraki_expected_districts Beklenen ilçe sayısı",
        "# TYPE buraki_expected_districts gauge",
        f"buraki_expected_districts {EXPECTED_DISTRICTS}",
    ]
    return Response("\n".join(lines) + "\n", media_type="text/plain")
