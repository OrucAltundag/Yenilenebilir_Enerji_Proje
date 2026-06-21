"""CSV ve SQLAlchemy veri erişim katmanları için ortak sözleşme."""

from __future__ import annotations

import unicodedata
from functools import lru_cache
from typing import Protocol

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.models import (
    DistrictMaster,
    DistrictMonthlyProfile,
    DistrictScoreSummary,
)
from app.db.session import SessionLocal


def _ascii_upper(value: str) -> str:
    text = str(value).strip().upper()
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
    )


class Repository(Protocol):
    def count_districts(self, year: int | None = None) -> int: ...
    def search(self, query: str, limit: int) -> list[dict]: ...
    def get_summary(self, district_id: str, year: int | None = None) -> dict | None: ...
    def get_monthly(self, district_id: str, year: int | None = None) -> list[dict]: ...
    def score_map(self, energy: str, year: int | None = None) -> list[dict]: ...
    def ranking(self, energy: str, limit: int, year: int | None = None) -> list[dict]: ...


class CsvDataRepository:
    """Küçük/dev kurulumları için belleğe yüklenen CSV repository."""

    def __init__(self) -> None:
        self.summary = pd.read_csv(settings.summary_csv)
        self.monthly = pd.read_csv(settings.monthly_csv)
        self.master = pd.read_csv(settings.master_csv)
        self._search_key = (
            self.summary["province"].map(_ascii_upper)
            + " "
            + self.summary["district"].map(_ascii_upper)
        )
        self.year = int(self.summary["year"].iloc[0])

    def _summary_for_year(self, year: int | None) -> pd.DataFrame:
        selected_year = self.year if year is None else year
        return self.summary[self.summary["year"] == selected_year]

    def count_districts(self, year: int | None = None) -> int:
        return len(self._summary_for_year(year))

    def search(self, query: str, limit: int) -> list[dict]:
        key = _ascii_upper(query)
        mask = self._search_key.str.contains(key, na=False)
        cols = ["district_id", "province", "district"]
        return self.summary.loc[mask, cols].head(limit).to_dict("records")

    def get_summary(self, district_id: str, year: int | None = None) -> dict | None:
        summary = self._summary_for_year(year)
        row = summary[summary["district_id"] == district_id]
        if row.empty:
            return None
        return row.iloc[0].to_dict()

    def get_monthly(self, district_id: str, year: int | None = None) -> list[dict]:
        selected_year = self.year if year is None else year
        if selected_year != self.year:
            return []
        rows = self.monthly[self.monthly["district_id"] == district_id]
        return rows.sort_values("ay")[["ay", "ges_mean", "res_mean"]].to_dict(
            "records"
        )

    def score_map(self, energy: str, year: int | None = None) -> list[dict]:
        mean_col = f"{energy.upper()}_YATIRIM_SKORU_mean"
        pct_col = f"{energy}_percentile"
        out = self._summary_for_year(year)[
            ["district_id", "province", "district", mean_col, pct_col]
        ].rename(columns={mean_col: "score", pct_col: "percentile"})
        return out.to_dict("records")

    def ranking(self, energy: str, limit: int, year: int | None = None) -> list[dict]:
        rank_col = f"{energy}_national_rank"
        mean_col = f"{energy.upper()}_YATIRIM_SKORU_mean"
        pct_col = f"{energy}_percentile"
        out = (
            self._summary_for_year(year).nsmallest(limit, rank_col)[
                ["district_id", "province", "district", mean_col, pct_col]
            ]
            .rename(columns={mean_col: "score", pct_col: "percentile"})
        )
        return out.to_dict("records")


class SqlDataRepository:
    """PostgreSQL/SQLite üzerinde aynı API sözleşmesini sağlayan repository."""

    def __init__(
        self,
        session_factory: sessionmaker = SessionLocal,
        year: int = 2023,
    ) -> None:
        self.session_factory = session_factory
        self.year = year

    def _selected_year(self, year: int | None) -> int:
        return self.year if year is None else year

    def count_districts(self, year: int | None = None) -> int:
        with self.session_factory() as db:
            return int(
                db.scalar(
                    select(func.count()).select_from(DistrictScoreSummary).where(
                        DistrictScoreSummary.year == self._selected_year(year)
                    )
                )
                or 0
            )

    def search(self, query: str, limit: int) -> list[dict]:
        key = _ascii_upper(query)
        with self.session_factory() as db:
            rows = db.execute(
                select(
                    DistrictMaster.district_id,
                    DistrictMaster.province,
                    DistrictMaster.district,
                )
                .join(
                    DistrictScoreSummary,
                    DistrictScoreSummary.district_id == DistrictMaster.district_id,
                )
                .where(
                    DistrictScoreSummary.year == self.year,
                    DistrictMaster.search_key.contains(key),
                )
                .order_by(DistrictScoreSummary.ges_national_rank)
                .limit(limit)
            ).mappings()
            return [dict(row) for row in rows]

    @staticmethod
    def _summary_dict(
        district: DistrictMaster, summary: DistrictScoreSummary
    ) -> dict:
        return {
            "district_id": district.district_id,
            "province": district.province,
            "district": district.district,
            "GES_YATIRIM_SKORU_mean": summary.ges_score_mean,
            "GES_YATIRIM_SKORU_median": summary.ges_score_median,
            "GES_YATIRIM_SKORU_min": summary.ges_score_min,
            "GES_YATIRIM_SKORU_max": summary.ges_score_max,
            "GES_YATIRIM_SKORU_p10": summary.ges_score_p10,
            "GES_YATIRIM_SKORU_p90": summary.ges_score_p90,
            "GES_YATIRIM_SKORU_stddev": summary.ges_score_stddev,
            "RES_YATIRIM_SKORU_mean": summary.res_score_mean,
            "RES_YATIRIM_SKORU_median": summary.res_score_median,
            "RES_YATIRIM_SKORU_min": summary.res_score_min,
            "RES_YATIRIM_SKORU_max": summary.res_score_max,
            "RES_YATIRIM_SKORU_p10": summary.res_score_p10,
            "RES_YATIRIM_SKORU_p90": summary.res_score_p90,
            "RES_YATIRIM_SKORU_stddev": summary.res_score_stddev,
            "sample_count": summary.sample_count,
            "T2M": summary.t2m,
            "RH2M": summary.rh2m,
            "WS10M": summary.ws10m,
            "ALLSKY_SFC_SW_DWN": summary.allsky_sfc_sw_dwn,
            "arazi_egimi_yuzde": summary.arazi_egimi_yuzde,
            "yuzey_alani_km2": summary.yuzey_alani_km2,
            "yuzey_Orman_ve_Doğa": summary.land_forest_nature,
            "yuzey_Su_Yüzeyi": summary.land_water,
            "yuzey_Sulak_Alan": summary.land_wetland,
            "yuzey_Tarım_Arazisi": summary.land_agriculture,
            "yuzey_Şehir_Yerleşimi": summary.land_urban,
            "tesvik_bolgesi": summary.tesvik_bolgesi,
            "year": summary.year,
            "ges_national_rank": summary.ges_national_rank,
            "ges_percentile": summary.ges_percentile,
            "res_national_rank": summary.res_national_rank,
            "res_percentile": summary.res_percentile,
        }

    def get_summary(self, district_id: str, year: int | None = None) -> dict | None:
        with self.session_factory() as db:
            row = db.execute(
                select(DistrictMaster, DistrictScoreSummary)
                .join(
                    DistrictScoreSummary,
                    DistrictScoreSummary.district_id == DistrictMaster.district_id,
                )
                .where(
                    DistrictMaster.district_id == district_id,
                    DistrictScoreSummary.year == self._selected_year(year),
                )
            ).one_or_none()
            if row is None:
                return None
            return self._summary_dict(row[0], row[1])

    def get_monthly(self, district_id: str, year: int | None = None) -> list[dict]:
        with self.session_factory() as db:
            rows = db.execute(
                select(
                    DistrictMonthlyProfile.month.label("ay"),
                    DistrictMonthlyProfile.ges_mean,
                    DistrictMonthlyProfile.res_mean,
                )
                .where(
                    DistrictMonthlyProfile.district_id == district_id,
                    DistrictMonthlyProfile.year == self._selected_year(year),
                )
                .order_by(DistrictMonthlyProfile.month)
            ).mappings()
            return [dict(row) for row in rows]

    def _score_rows(
        self,
        energy: str,
        limit: int | None = None,
        year: int | None = None,
    ) -> list[dict]:
        if energy == "ges":
            score_column = DistrictScoreSummary.ges_score_mean
            percentile_column = DistrictScoreSummary.ges_percentile
            rank_column = DistrictScoreSummary.ges_national_rank
        else:
            score_column = DistrictScoreSummary.res_score_mean
            percentile_column = DistrictScoreSummary.res_percentile
            rank_column = DistrictScoreSummary.res_national_rank

        statement = (
            select(
                DistrictMaster.district_id,
                DistrictMaster.province,
                DistrictMaster.district,
                score_column.label("score"),
                percentile_column.label("percentile"),
            )
            .join(
                DistrictScoreSummary,
                DistrictScoreSummary.district_id == DistrictMaster.district_id,
            )
            .where(DistrictScoreSummary.year == self._selected_year(year))
            .order_by(rank_column)
        )
        if limit is not None:
            statement = statement.limit(limit)
        with self.session_factory() as db:
            rows = db.execute(statement).mappings()
            return [dict(row) for row in rows]

    def score_map(self, energy: str, year: int | None = None) -> list[dict]:
        return self._score_rows(energy, year=year)

    def ranking(self, energy: str, limit: int, year: int | None = None) -> list[dict]:
        return self._score_rows(energy, limit, year)


# Eski importları kırmamak için geriye uyumlu ad.
DataRepository = CsvDataRepository


def _resolved_backend() -> str:
    configured = settings.data_repository.lower()
    if configured == "auto":
        return "csv" if settings.database_url.startswith("sqlite") else "database"
    if configured not in {"csv", "database"}:
        raise RuntimeError("DATA_REPOSITORY auto, csv veya database olmalı")
    return configured


@lru_cache
def get_repository() -> Repository:
    if _resolved_backend() == "database":
        return SqlDataRepository()
    return CsvDataRepository()
