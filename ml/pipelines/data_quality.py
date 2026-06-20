"""Faz 1 — Veri Kalite Raporu.

Rapor 5.2 ve 10.1'deki kalite kapılarını otomatik kontrol eder:
- district_count (hedef 957)
- her ilçe için kayıt sayısı (hedef 365)
- sıfır yüzölçümü sayısı (hedef 0)
- özellik aralıkları ve eksik değerler
- skor dağılımları

Çalıştırma:
    python ml/pipelines/data_quality.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))

from common.schema import FEATURE_ORDER, TARGET_COLUMNS  # noqa: E402

DATA = ROOT / "data"
DEFAULT_INPUT = DATA / "processed" / "XGBoost_Egitim_Veriseti_Temiz.csv"
OUT_REPORT = DATA / "processed" / "data_quality_report.json"

EXPECTED_DISTRICTS = 957
EXPECTED_DAYS = 365


def build_report(input_csv: Path = DEFAULT_INPUT) -> dict:
    df = pd.read_csv(input_csv)
    df["il"] = df["il"].str.strip().str.upper()
    df["ilce"] = df["ilce"].str.strip()

    per_district = df.groupby(["il", "ilce"]).size()
    district_count = int(per_district.shape[0])

    area_zero = (
        df.groupby(["il", "ilce"])["yuzey_alani_km2"].first().eq(0).sum()
    )

    feature_stats = {}
    for col in FEATURE_ORDER:
        s = pd.to_numeric(df[col], errors="coerce")
        feature_stats[col] = {
            "min": float(s.min()),
            "max": float(s.max()),
            "mean": round(float(s.mean()), 4),
            "null": int(s.isna().sum()),
        }

    target_stats = {}
    for col in TARGET_COLUMNS:
        s = pd.to_numeric(df[col], errors="coerce")
        target_stats[col] = {
            "min": round(float(s.min()), 2),
            "max": round(float(s.max()), 2),
            "mean": round(float(s.mean()), 2),
            "p10": round(float(s.quantile(0.10)), 2),
            "p90": round(float(s.quantile(0.90)), 2),
        }

    gates = {
        "district_count_ok": district_count == EXPECTED_DISTRICTS,
        "all_districts_365_ok": bool(per_district.eq(EXPECTED_DAYS).all()),
        "area_zero_ok": int(area_zero) == 0,
    }

    return {
        "input_file": input_csv.name,
        "row_count": int(len(df)),
        "district_count": district_count,
        "expected_district_count": EXPECTED_DISTRICTS,
        "province_count": int(df["il"].nunique()),
        "records_per_district": {
            "min": int(per_district.min()),
            "max": int(per_district.max()),
            "expected": EXPECTED_DAYS,
        },
        "area_zero_count": int(area_zero),
        "feature_stats": feature_stats,
        "target_stats": target_stats,
        "quality_gates": gates,
        "all_gates_passed": all(gates.values()),
    }


def main() -> None:
    report = build_report()
    OUT_REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Satır            : {report['row_count']:,}")
    print(f"İlçe sayısı       : {report['district_count']} (hedef {EXPECTED_DISTRICTS})")
    print(f"İl sayısı         : {report['province_count']}")
    print(
        f"Kayıt/ilçe        : {report['records_per_district']['min']}–"
        f"{report['records_per_district']['max']} (hedef {EXPECTED_DAYS})"
    )
    print(f"Sıfır yüzölçümü   : {report['area_zero_count']}")
    print("Kalite kapıları   :")
    for gate, ok in report["quality_gates"].items():
        print(f"  - {gate}: {'GEÇTİ' if ok else 'KALDI'}")
    print(f"-> Rapor: {OUT_REPORT}")
    if not report["all_gates_passed"]:
        raise SystemExit("Veri kalite kapılarından en az biri başarısız")


if __name__ == "__main__":
    main()
