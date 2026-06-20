"""Faz 1 — Canonical İlçe Kimliği (district_master) üretimi.

Final veri setindeki il/ilçe çiftlerinden değişmez bir ``district_id`` üretir ve
kaynak adlarını bu kimliğe bağlayan bir alias tablosu oluşturur. Rapordaki
"tüm veri kaynakları tek bir district_master tablosuna bağlanmalı; anahtar
metin adı değil district_id olmalı" gereksinimini karşılar.

Çalıştırma:
    python ml/pipelines/district_master.py
"""

from __future__ import annotations

import hashlib
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
DEFAULT_INPUT = DATA / "processed" / "XGBoost_Egitim_Veriseti_Guncel.csv"
OUT_MASTER = DATA / "reference" / "district_master.csv"
OUT_ALIAS = DATA / "reference" / "district_alias.csv"


def normalize_name(value: str) -> str:
    """Eşleştirme için ad normalizasyonu: büyük harf + aksan/boşluk sadeleştirme."""
    text = str(value).strip().upper()
    # Türkçe büyük harf tutarlılığı
    text = text.replace("I", "I").replace("İ", "İ")
    # Aksanları kaldırılmış ASCII anahtarı (yalnızca eşleştirme için)
    ascii_key = (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    return " ".join(ascii_key.split())


def make_district_id(province: str, district: str) -> str:
    """İl+ilçe normalize anahtarından kararlı (deterministik) bir kimlik üretir."""
    key = f"{normalize_name(province)}|{normalize_name(district)}"
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]
    return f"TR-{digest}"


def build(input_csv: Path = DEFAULT_INPUT) -> pd.DataFrame:
    df = pd.read_csv(input_csv, usecols=["il", "ilce", "yuzey_alani_km2", "tesvik_bolgesi"])
    df["il"] = df["il"].str.strip().str.upper()
    df["ilce"] = df["ilce"].str.strip()

    grouped = (
        df.groupby(["il", "ilce"], as_index=False)
        .agg(
            yuzey_alani_km2=("yuzey_alani_km2", "first"),
            tesvik_bolgesi=("tesvik_bolgesi", "first"),
            kayit_sayisi=("il", "size"),
        )
        .sort_values(["il", "ilce"])
        .reset_index(drop=True)
    )
    grouped["district_id"] = grouped.apply(
        lambda r: make_district_id(r["il"], r["ilce"]), axis=1
    )

    master = grouped[
        ["district_id", "il", "ilce", "yuzey_alani_km2", "tesvik_bolgesi", "kayit_sayisi"]
    ].rename(columns={"il": "province", "ilce": "district"})

    alias = grouped[["district_id", "il", "ilce"]].copy()
    alias["source_name"] = alias["il"] + " / " + alias["ilce"]
    alias["normalized_name"] = alias.apply(
        lambda r: f"{normalize_name(r['il'])}|{normalize_name(r['ilce'])}", axis=1
    )
    alias["match_method"] = "exact"
    alias["confidence"] = 1.0
    alias = alias.rename(columns={"il": "source_province", "ilce": "source_district"})

    return master, alias


def main() -> None:
    master, alias = build()
    OUT_MASTER.parent.mkdir(parents=True, exist_ok=True)
    master.to_csv(OUT_MASTER, index=False, encoding="utf-8-sig")
    alias.to_csv(OUT_ALIAS, index=False, encoding="utf-8-sig")

    print(f"district_master  : {len(master)} ilçe  -> {OUT_MASTER.name}")
    print(f"district_alias   : {len(alias)} kayıt -> {OUT_ALIAS.name}")
    print(f"benzersiz il      : {master['province'].nunique()}")
    print(f"benzersiz id      : {master['district_id'].nunique()}")
    dup = master["district_id"].duplicated().sum()
    print(f"id çakışması      : {dup}")


if __name__ == "__main__":
    main()
