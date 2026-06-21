from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.core.config import settings
from app.data.repository import get_repository
from app.schemas.district import (
    DistrictItem,
    DistrictCompareRequest,
    DistrictSearchResponse,
    DistrictSummary,
    MonthlyPoint,
)

router = APIRouter()


@router.get("/search", response_model=DistrictSearchResponse)
def search_districts(
    q: str = Query(..., min_length=2, description="İl/ilçe adı araması"),
    limit: int = Query(10, ge=1, le=50),
):
    """İl/ilçe adına göre arama yapar."""
    repo = get_repository()
    items = [DistrictItem(**r) for r in repo.search(q, limit)]
    return DistrictSearchResponse(items=items, total=len(items))


@router.get("/geojson", response_class=FileResponse)
def district_geojson():
    """MapLibre için canonical kimliklerle eşleştirilmiş ilçe geometrileri."""
    if not settings.district_geometry_path.exists():
        raise HTTPException(
            status_code=503,
            detail="İlçe geometrisi yok; scripts/build_district_geojson.py çalıştırın",
        )
    return FileResponse(
        settings.district_geometry_path,
        media_type="application/geo+json",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.post("/compare", response_model=list[DistrictSummary])
def compare_districts(payload: DistrictCompareRequest):
    """2–5 ilçenin özetlerini tek sözleşmede döndürür."""
    if len(set(payload.district_ids)) != len(payload.district_ids):
        raise HTTPException(status_code=422, detail="İlçe kimlikleri benzersiz olmalı")
    return [district_summary(district_id, payload.year) for district_id in payload.district_ids]


@router.get("/{district_id}/summary", response_model=DistrictSummary)
def district_summary(district_id: str, year: int = 2023):
    """Seçilen ilçe için yıllık özet skor, girdiler ve aylık profili döner."""
    repo = get_repository()
    row = repo.get_summary(district_id, year)
    if row is None:
        raise HTTPException(status_code=404, detail="İlçe bulunamadı")

    monthly = [MonthlyPoint(**m) for m in repo.get_monthly(district_id, year)]
    return DistrictSummary(
        district_id=row["district_id"],
        province=row["province"],
        district=row["district"],
        year=int(row["year"]),
        ges_score_mean=row["GES_YATIRIM_SKORU_mean"],
        res_score_mean=row["RES_YATIRIM_SKORU_mean"],
        national_rank_ges=int(row["ges_national_rank"]),
        national_rank_res=int(row["res_national_rank"]),
        percentile_ges=row["ges_percentile"],
        percentile_res=row["res_percentile"],
        features={
            "ALLSKY_SFC_SW_DWN": row["ALLSKY_SFC_SW_DWN"],
            "WS10M": row["WS10M"],
            "T2M": row["T2M"],
            "RH2M": row["RH2M"],
            "arazi_egimi_yuzde": row["arazi_egimi_yuzde"],
            "yuzey_alani_km2": row["yuzey_alani_km2"],
            "tesvik_bolgesi": row["tesvik_bolgesi"],
        },
        monthly=monthly,
        data_version=settings.data_version,
        scoring_version=settings.data_version,
    )
