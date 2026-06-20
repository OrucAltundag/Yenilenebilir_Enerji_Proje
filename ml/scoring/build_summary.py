"""Faz 3 — district_score_summary üretimi.

Temiz veri setini district_master ile birleştirip ilçe/yıl bazında özet üretir:
mean, median, min, max, p10, p90, stddev, sample_count + ulusal rank ve
percentile (GES ve RES için ayrı). Rapor 3.4'teki agregasyon görünümünün
dosya tabanlı karşılığıdır; backend bu dosyayı doğrudan servis eder.

Çıktı:
    data/processed/district_score_summary.csv
    data/processed/district_monthly_profile.csv (aylık ortalama profil)

Çalıştırma:
    python ml/scoring/build_summary.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))

from common.schema import FEATURE_ORDER  # noqa: E402

DATA = ROOT / "data"
INPUT = DATA / "processed" / "XGBoost_Egitim_Veriseti_Temiz.csv"
MASTER = DATA / "reference" / "district_master.csv"
OUT_SUMMARY = DATA / "processed" / "district_score_summary.csv"
OUT_MONTHLY = DATA / "processed" / "district_monthly_profile.csv"
YEAR = 2023


def _agg(series_group, col: str) -> pd.DataFrame:
    g = series_group[col]
    return pd.DataFrame(
        {
            f"{col}_mean": g.mean().round(2),
            f"{col}_median": g.median().round(2),
            f"{col}_min": g.min().round(2),
            f"{col}_max": g.max().round(2),
            f"{col}_p10": g.quantile(0.10).round(2),
            f"{col}_p90": g.quantile(0.90).round(2),
            f"{col}_stddev": g.std().round(2),
        }
    )


def main() -> None:
    df = pd.read_csv(INPUT)
    df["il"] = df["il"].str.strip().str.upper()
    df["ilce"] = df["ilce"].str.strip()

    master = pd.read_csv(MASTER)[["district_id", "province", "district"]]
    df = df.merge(
        master, left_on=["il", "ilce"], right_on=["province", "district"], how="left"
    )

    grouped = df.groupby(["district_id", "il", "ilce"])
    ges = _agg(grouped, "GES_YATIRIM_SKORU")
    res = _agg(grouped, "RES_YATIRIM_SKORU")
    counts = grouped.size().rename("sample_count")

    # Temsili girdi ortalamaları (ilçe detay ekranı için)
    feat_means = grouped[list(FEATURE_ORDER)].mean().round(4)

    summary = pd.concat([ges, res, counts, feat_means], axis=1).reset_index()
    summary = summary.rename(columns={"il": "province", "ilce": "district"})
    summary["year"] = YEAR

    # Ulusal sıralama ve percentile
    for energy in ["GES", "RES"]:
        col = f"{energy}_YATIRIM_SKORU_mean"
        summary[f"{energy.lower()}_national_rank"] = (
            summary[col].rank(ascending=False, method="min").astype(int)
        )
        summary[f"{energy.lower()}_percentile"] = (
            summary[col].rank(pct=True).mul(100).round(2)
        )

    summary = summary.sort_values("ges_national_rank").reset_index(drop=True)
    summary.to_csv(OUT_SUMMARY, index=False, encoding="utf-8-sig")

    # Aylık profil
    df["ay"] = pd.to_datetime(df["tarih"], format="%Y%m%d").dt.month
    monthly = (
        df.groupby(["district_id", "ay"])[
            ["GES_YATIRIM_SKORU", "RES_YATIRIM_SKORU"]
        ]
        .mean()
        .round(2)
        .reset_index()
        .rename(
            columns={
                "GES_YATIRIM_SKORU": "ges_mean",
                "RES_YATIRIM_SKORU": "res_mean",
            }
        )
    )
    monthly.to_csv(OUT_MONTHLY, index=False, encoding="utf-8-sig")

    print(f"Özet satır       : {len(summary)} ilçe -> {OUT_SUMMARY.name}")
    print(f"Aylık profil     : {len(monthly)} satır -> {OUT_MONTHLY.name}")
    print(f"İl/ilçe eşleşmeyen: {summary['district_id'].isna().sum()}")
    print("\nGES ilk 5 ilçe (yıllık ortalama):")
    top = summary.nsmallest(5, "ges_national_rank")
    for _, r in top.iterrows():
        print(
            f"  {r['ges_national_rank']:>3}. {r['province']}/{r['district']:<20} "
            f"GES={r['GES_YATIRIM_SKORU_mean']:.2f}"
        )


if __name__ == "__main__":
    main()
