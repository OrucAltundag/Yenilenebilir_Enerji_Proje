"""Önceden hesaplanmış CSV artefaktlarını ilişkisel veritabanına yükler."""

from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.models import (
    DatasetVersion,
    DistrictMaster,
    DistrictMonthlyProfile,
    DistrictScoreSummary,
)
from app.db.session import SessionLocal


def _search_key(province: str, district: str) -> str:
    text = f"{province} {district}".strip().upper()
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
    )


def _summary_mapping(row: pd.Series) -> dict:
    return {
        "district_id": row["district_id"],
        "year": int(row["year"]),
        "ges_score_mean": float(row["GES_YATIRIM_SKORU_mean"]),
        "ges_score_median": float(row["GES_YATIRIM_SKORU_median"]),
        "ges_score_min": float(row["GES_YATIRIM_SKORU_min"]),
        "ges_score_max": float(row["GES_YATIRIM_SKORU_max"]),
        "ges_score_p10": float(row["GES_YATIRIM_SKORU_p10"]),
        "ges_score_p90": float(row["GES_YATIRIM_SKORU_p90"]),
        "ges_score_stddev": float(row["GES_YATIRIM_SKORU_stddev"]),
        "res_score_mean": float(row["RES_YATIRIM_SKORU_mean"]),
        "res_score_median": float(row["RES_YATIRIM_SKORU_median"]),
        "res_score_min": float(row["RES_YATIRIM_SKORU_min"]),
        "res_score_max": float(row["RES_YATIRIM_SKORU_max"]),
        "res_score_p10": float(row["RES_YATIRIM_SKORU_p10"]),
        "res_score_p90": float(row["RES_YATIRIM_SKORU_p90"]),
        "res_score_stddev": float(row["RES_YATIRIM_SKORU_stddev"]),
        "sample_count": int(row["sample_count"]),
        "t2m": float(row["T2M"]),
        "rh2m": float(row["RH2M"]),
        "ws10m": float(row["WS10M"]),
        "allsky_sfc_sw_dwn": float(row["ALLSKY_SFC_SW_DWN"]),
        "arazi_egimi_yuzde": float(row["arazi_egimi_yuzde"]),
        "yuzey_alani_km2": float(row["yuzey_alani_km2"]),
        "land_forest_nature": float(row["yuzey_Orman_ve_Doğa"]),
        "land_water": float(row["yuzey_Su_Yüzeyi"]),
        "land_wetland": float(row["yuzey_Sulak_Alan"]),
        "land_agriculture": float(row["yuzey_Tarım_Arazisi"]),
        "land_urban": float(row["yuzey_Şehir_Yerleşimi"]),
        "tesvik_bolgesi": float(row["tesvik_bolgesi"]),
        "ges_national_rank": int(row["ges_national_rank"]),
        "ges_percentile": float(row["ges_percentile"]),
        "res_national_rank": int(row["res_national_rank"]),
        "res_percentile": float(row["res_percentile"]),
    }


def seed_analytics_data(
    session_factory: sessionmaker = SessionLocal,
    summary_csv: Path = settings.summary_csv,
    monthly_csv: Path = settings.monthly_csv,
    data_version: str = settings.data_version,
) -> dict[str, int]:
    """Özet ve aylık tabloları tek transaction içinde idempotent yeniler."""
    summary_df = pd.read_csv(summary_csv)
    monthly_df = pd.read_csv(monthly_csv)
    if len(summary_df) != 957:
        raise RuntimeError(f"Özet ilçe sayısı 957 değil: {len(summary_df)}")

    years = sorted(int(year) for year in summary_df["year"].unique())
    default_year = years[0]
    if len(years) != 1:
        raise RuntimeError(f"Seed tek yıl bekliyor: {years}")

    summaries = [_summary_mapping(row) for _, row in summary_df.iterrows()]
    monthly = [
        {
            "district_id": row["district_id"],
            "year": default_year,
            "month": int(row["ay"]),
            "ges_mean": float(row["ges_mean"]),
            "res_mean": float(row["res_mean"]),
        }
        for _, row in monthly_df.iterrows()
    ]

    with session_factory() as db, db.begin():
        for _, row in summary_df.iterrows():
            db.merge(
                DistrictMaster(
                    district_id=row["district_id"],
                    province=row["province"],
                    district=row["district"],
                    search_key=_search_key(row["province"], row["district"]),
                    yuzey_alani_km2=float(row["yuzey_alani_km2"]),
                    arazi_egimi_yuzde=float(row["arazi_egimi_yuzde"]),
                    tesvik_bolgesi=int(float(row["tesvik_bolgesi"])),
                )
            )
        db.flush()

        db.execute(
            delete(DistrictMonthlyProfile).where(
                DistrictMonthlyProfile.year.in_(years)
            )
        )
        db.execute(
            delete(DistrictScoreSummary).where(DistrictScoreSummary.year.in_(years))
        )
        db.execute(insert(DistrictScoreSummary), summaries)
        db.execute(insert(DistrictMonthlyProfile), monthly)

        version = db.scalar(
            select(DatasetVersion).where(DatasetVersion.version == data_version)
        )
        if version is None:
            version = DatasetVersion(version=data_version)
            db.add(version)
        version.status = "published"
        version.is_active = True
        version.district_count = len(summary_df)
        version.area_zero = int(summary_df["yuzey_alani_km2"].eq(0).sum())

    return {
        "district_master": len(summary_df),
        "district_score_summary": len(summaries),
        "district_monthly_profile": len(monthly),
    }


def main() -> None:
    """Konteyner başlangıcında kullanılabilen seed komutu."""
    counts = seed_analytics_data()
    for table, count in counts.items():
        print(f"{table}: {count} kayıt")


if __name__ == "__main__":
    main()
