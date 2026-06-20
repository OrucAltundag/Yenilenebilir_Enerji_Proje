"""SQLAlchemy ORM modelleri.

Rapora göre tablo iskeleti:
- district_master            : kanonik il/ilçe kimliği
- district_alias             : kaynak adı -> district_id eşlemesi
- daily_observation          : 349.305 günlük meteorolojik kayıt
- district_score_summary     : önceden hesaplanmış yıllık/aylık özet
- model_registry             : aktif/önceki modeller
- dataset_version            : veri sürüm pointer'ı
- audit_log                  : yönetici işlemleri
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Date, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DistrictMaster(Base):
    __tablename__ = "district_master"

    district_id: Mapped[str] = mapped_column(String, primary_key=True)
    province: Mapped[str] = mapped_column(String, index=True)
    district: Mapped[str] = mapped_column(String)
    search_key: Mapped[str | None] = mapped_column(String, index=True)
    yuzey_alani_km2: Mapped[float | None] = mapped_column(Float)
    arazi_egimi_yuzde: Mapped[float | None] = mapped_column(Float)
    tesvik_bolgesi: Mapped[int | None] = mapped_column(Integer)

    observations: Mapped[list["DailyObservation"]] = relationship(
        back_populates="district"
    )
    summaries: Mapped[list["DistrictScoreSummary"]] = relationship(
        back_populates="district", cascade="all, delete-orphan"
    )
    monthly_profiles: Mapped[list["DistrictMonthlyProfile"]] = relationship(
        back_populates="district", cascade="all, delete-orphan"
    )


class DailyObservation(Base):
    __tablename__ = "daily_observation"

    id: Mapped[int] = mapped_column(primary_key=True)
    district_id: Mapped[str] = mapped_column(
        ForeignKey("district_master.district_id"), index=True
    )
    date: Mapped[Date] = mapped_column(Date, index=True)
    t2m: Mapped[float | None] = mapped_column(Float)
    rh2m: Mapped[float | None] = mapped_column(Float)
    ws10m: Mapped[float | None] = mapped_column(Float)
    allsky_sfc_sw_dwn: Mapped[float | None] = mapped_column(Float)
    ges_score: Mapped[float | None] = mapped_column(Float)
    res_score: Mapped[float | None] = mapped_column(Float)

    district: Mapped[DistrictMaster] = relationship(back_populates="observations")


class DistrictScoreSummary(Base):
    """API'nin kullandığı önceden hesaplanmış yıllık ilçe özeti."""

    __tablename__ = "district_score_summary"

    district_id: Mapped[str] = mapped_column(
        ForeignKey("district_master.district_id"), primary_key=True
    )
    year: Mapped[int] = mapped_column(Integer, primary_key=True)

    ges_score_mean: Mapped[float] = mapped_column(Float)
    ges_score_median: Mapped[float] = mapped_column(Float)
    ges_score_min: Mapped[float] = mapped_column(Float)
    ges_score_max: Mapped[float] = mapped_column(Float)
    ges_score_p10: Mapped[float] = mapped_column(Float)
    ges_score_p90: Mapped[float] = mapped_column(Float)
    ges_score_stddev: Mapped[float] = mapped_column(Float)

    res_score_mean: Mapped[float] = mapped_column(Float)
    res_score_median: Mapped[float] = mapped_column(Float)
    res_score_min: Mapped[float] = mapped_column(Float)
    res_score_max: Mapped[float] = mapped_column(Float)
    res_score_p10: Mapped[float] = mapped_column(Float)
    res_score_p90: Mapped[float] = mapped_column(Float)
    res_score_stddev: Mapped[float] = mapped_column(Float)
    sample_count: Mapped[int] = mapped_column(Integer)

    t2m: Mapped[float] = mapped_column(Float)
    rh2m: Mapped[float] = mapped_column(Float)
    ws10m: Mapped[float] = mapped_column(Float)
    allsky_sfc_sw_dwn: Mapped[float] = mapped_column(Float)
    arazi_egimi_yuzde: Mapped[float] = mapped_column(Float)
    yuzey_alani_km2: Mapped[float] = mapped_column(Float)
    land_forest_nature: Mapped[float] = mapped_column(Float)
    land_water: Mapped[float] = mapped_column(Float)
    land_wetland: Mapped[float] = mapped_column(Float)
    land_agriculture: Mapped[float] = mapped_column(Float)
    land_urban: Mapped[float] = mapped_column(Float)
    tesvik_bolgesi: Mapped[float] = mapped_column(Float)

    ges_national_rank: Mapped[int] = mapped_column(Integer, index=True)
    ges_percentile: Mapped[float] = mapped_column(Float)
    res_national_rank: Mapped[int] = mapped_column(Integer, index=True)
    res_percentile: Mapped[float] = mapped_column(Float)

    district: Mapped[DistrictMaster] = relationship(back_populates="summaries")


class DistrictMonthlyProfile(Base):
    """İlçe başına aylık GES/RES ortalama skorları."""

    __tablename__ = "district_monthly_profile"

    district_id: Mapped[str] = mapped_column(
        ForeignKey("district_master.district_id"), primary_key=True
    )
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    month: Mapped[int] = mapped_column(Integer, primary_key=True)
    ges_mean: Mapped[float] = mapped_column(Float)
    res_mean: Mapped[float] = mapped_column(Float)

    district: Mapped[DistrictMaster] = relationship(back_populates="monthly_profiles")


class SavedProject(Base):
    """Kullanıcının kaydettiği analiz/karşılaştırma projesi."""

    __tablename__ = "saved_project"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    note: Mapped[str | None] = mapped_column(String)
    district_ids: Mapped[list] = mapped_column(JSON, default=list)
    energy: Mapped[str] = mapped_column(String, default="ges")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    scenarios: Mapped[list["SavedScenario"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class SavedScenario(Base):
    """Senaryo simülasyonu kaydı (input_snapshot + scoring_version saklanır)."""

    __tablename__ = "saved_scenario"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[str] = mapped_column(String, index=True)
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("saved_project.id"), nullable=True
    )
    district_id: Mapped[str] = mapped_column(String, index=True)
    overrides: Mapped[dict] = mapped_column(JSON, default=dict)
    input_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    scoring_version: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    project: Mapped["SavedProject | None"] = relationship(back_populates="scenarios")


class DatasetVersion(Base):
    """Veri sürümü kaydı; aktif sürüm pointer'ı is_active ile tutulur."""

    __tablename__ = "dataset_version"

    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(String, unique=True)
    status: Mapped[str] = mapped_column(String, default="staging")  # staging|published
    is_active: Mapped[bool] = mapped_column(default=False)
    district_count: Mapped[int | None] = mapped_column(Integer)
    area_zero: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AuditLog(Base):
    """Yönetici işlemleri için denetim kaydı."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String, index=True)
    action: Mapped[str] = mapped_column(String)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
