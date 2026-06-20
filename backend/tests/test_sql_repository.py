from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.data.repository import CsvDataRepository, SqlDataRepository
from app.db.models import DistrictMonthlyProfile, DistrictScoreSummary
from app.db.seed import seed_analytics_data
from app.db.session import Base


@pytest.fixture(scope="module")
def repositories():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False)
    seed_analytics_data(session_factory=session_factory)
    return CsvDataRepository(), SqlDataRepository(session_factory=session_factory), session_factory


def test_sql_repository_matches_csv_contract(repositories):
    csv_repo, sql_repo, _ = repositories
    assert sql_repo.count_districts() == csv_repo.count_districts() == 957
    assert sql_repo.ranking("ges", 10) == csv_repo.ranking("ges", 10)
    assert sql_repo.ranking("res", 10) == csv_repo.ranking("res", 10)
    assert sql_repo.search("ankara", 8) == csv_repo.search("ankara", 8)

    district_id = csv_repo.ranking("ges", 1)[0]["district_id"]
    csv_summary = csv_repo.get_summary(district_id)
    sql_summary = sql_repo.get_summary(district_id)
    assert sql_summary is not None and csv_summary is not None
    for key in (
        "province",
        "district",
        "GES_YATIRIM_SKORU_mean",
        "RES_YATIRIM_SKORU_mean",
        "ges_national_rank",
        "res_national_rank",
        "ALLSKY_SFC_SW_DWN",
        "WS10M",
    ):
        assert sql_summary[key] == csv_summary[key]
    assert sql_repo.get_monthly(district_id) == csv_repo.get_monthly(district_id)


def test_seed_is_idempotent(repositories):
    _, _, session_factory = repositories
    seed_analytics_data(session_factory=session_factory)
    with session_factory() as db:
        assert len(db.scalars(select(DistrictScoreSummary)).all()) == 957
        assert len(db.scalars(select(DistrictMonthlyProfile)).all()) == 11_484


def test_alembic_upgrade_creates_repository_tables(tmp_path: Path):
    database = tmp_path / "migration.db"
    backend_root = Path(__file__).resolve().parents[1]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database.as_posix()}")

    command.upgrade(config, "head")
    tables = set(inspect(create_engine(f"sqlite:///{database.as_posix()}")).get_table_names())
    assert {"district_master", "district_score_summary", "district_monthly_profile"} <= tables
