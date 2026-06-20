"""Canonical ilçe özetlerini SQLite veya PostgreSQL'e idempotent yükler.

Önerilen üretim sırası:
    cd backend
    alembic upgrade head
    cd ..
    python scripts/seed_db.py

Yerel geçici SQLite şeması için ``--create-schema`` kullanılabilir.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import inspect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.seed import seed_analytics_data  # noqa: E402
from app.db.session import engine, init_db  # noqa: E402

REQUIRED_TABLES = {
    "district_master",
    "district_score_summary",
    "district_monthly_profile",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--create-schema",
        action="store_true",
        help="Alembic yerine yalnızca yerel geliştirme için create_all çalıştır",
    )
    args = parser.parse_args()

    if args.create_schema:
        init_db()

    available = set(inspect(engine).get_table_names())
    missing = REQUIRED_TABLES - available
    if missing:
        raise SystemExit(
            "Eksik DB tabloları: "
            f"{', '.join(sorted(missing))}. Önce 'cd backend && alembic upgrade head' çalıştırın."
        )

    counts = seed_analytics_data()
    for table, count in counts.items():
        print(f"{table}: {count} kayıt")


if __name__ == "__main__":
    main()
