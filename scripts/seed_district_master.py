"""Canonical district master ve alias CSV artefaktlarını üretir.

Çalıştırma:
    python scripts/seed_district_master.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.pipelines.district_master import OUT_ALIAS, OUT_MASTER, build  # noqa: E402


def main() -> None:
    master, alias = build()
    OUT_MASTER.parent.mkdir(parents=True, exist_ok=True)
    master.to_csv(OUT_MASTER, index=False, encoding="utf-8-sig")
    alias.to_csv(OUT_ALIAS, index=False, encoding="utf-8-sig")
    print(f"district_master: {len(master)} kayıt -> {OUT_MASTER}")
    print(f"district_alias: {len(alias)} kayıt -> {OUT_ALIAS}")


if __name__ == "__main__":
    main()
