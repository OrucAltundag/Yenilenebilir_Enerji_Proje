"""Faz 1 — 117 Sıfır Yüzölçümü Düzeltmesi.

Final veri setinde yüzölçümü 0 olan ilçeleri ``data/reference/ilce_yuzolcumu.csv``
kaynağından il-bazlı normalize edilmiş ad eşleştirmesiyle doldurur. Veri
setindeki "(ESKİ_AD)" ekleri temizlenir; tam eşleşme bulunamazsa rapidfuzz ile
en yakın ilçe (eşik üstü) seçilir.

Çıktı: data/processed/XGBoost_Egitim_Veriseti_Temiz.csv

Çalıştırma:
    python ml/pipelines/fix_zero_area.py
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd
from rapidfuzz import process, fuzz

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
INPUT = DATA / "processed" / "XGBoost_Egitim_Veriseti_Guncel.csv"
AREA_SRC = DATA / "reference" / "ilce_yuzolcumu.csv"
OUTPUT = DATA / "processed" / "XGBoost_Egitim_Veriseti_Temiz.csv"

MATCH_THRESHOLD = 82  # rapidfuzz benzerlik eşiği

# Bilinen tarihi ad değişiklikleri (veri seti adı -> referans adı), il bazlı
MANUAL_ALIAS: dict[str, dict[str, str]] = {
    "AFYONKARAHISAR": {"SINCANLI": "SINANPASA"},
    # Referans CSV'de "ONDOKUZMAYIS" (19 Mayıs) tarih olarak bozulmuş: "2021-05-19"
    "SAMSUN": {"ONDOKUZMAYIS": "2021-05-19"},
    "SIIRT": {"AYDINLAR": "TILLO"},
    "DENIZLI": {"AKKOY": "PAMUKKALE"},
}


def norm(value: str) -> str:
    text = str(value).strip().upper()
    text = re.sub(r"\(.*?\)", "", text)  # parantez içi ekleri at
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.split())


def build_area_lookup() -> dict[str, dict[str, float]]:
    area = pd.read_csv(AREA_SRC)
    area["il_n"] = area["il"].map(norm)
    area["ilce_n"] = area["ilce"].map(norm)
    lookup: dict[str, dict[str, float]] = {}
    for _, r in area.iterrows():
        lookup.setdefault(r["il_n"], {})[r["ilce_n"]] = float(r["yuzey_alani_km2"])
    return lookup


def resolve_area(
    il_n: str, ilce_n: str, lookup: dict, province_mean: dict[str, float]
) -> tuple[float | None, str, float]:
    candidates = lookup.get(il_n, {})
    if not candidates:
        return None, "il_yok", 0.0
    # 1) Manuel alias (tarihi ad değişikliği)
    alias_target = MANUAL_ALIAS.get(il_n, {}).get(ilce_n)
    if alias_target is not None:
        key = norm(alias_target)
        if key in candidates:
            return candidates[key], "manual_alias", 100.0
    # 2) Tam eşleşme
    if ilce_n in candidates:
        return candidates[ilce_n], "exact", 100.0
    # 3) İl merkezi placeholder (ilçe adı = il adı) -> il ortalaması
    if ilce_n == il_n:
        return province_mean[il_n], "merkez_ortalama", 0.0
    # 4) Bulanık eşleşme
    match = process.extractOne(ilce_n, list(candidates.keys()), scorer=fuzz.WRatio)
    if match and match[1] >= MATCH_THRESHOLD:
        return candidates[match[0]], "fuzzy", float(match[1])
    return None, "esik_alti", float(match[1]) if match else 0.0


def main() -> None:
    df = pd.read_csv(INPUT)
    df["il"] = df["il"].str.strip().str.upper()
    df["ilce"] = df["ilce"].str.strip()
    df["yuzey_alani_km2"] = df["yuzey_alani_km2"].astype(float)

    lookup = build_area_lookup()
    province_mean = {
        il_n: (sum(d.values()) / len(d)) for il_n, d in lookup.items() if d
    }

    # Sıfır alanlı benzersiz il/ilçe çiftleri
    zero_mask = df["yuzey_alani_km2"].eq(0)
    zero_pairs = df.loc[zero_mask, ["il", "ilce"]].drop_duplicates()

    fixes: dict[tuple[str, str], float] = {}
    unresolved: list[tuple[str, str, str, float]] = []
    for _, r in zero_pairs.iterrows():
        area, method, score = resolve_area(
            norm(r["il"]), norm(r["ilce"]), lookup, province_mean
        )
        if area is not None and area > 0:
            fixes[(r["il"], r["ilce"])] = area
        else:
            unresolved.append((r["il"], r["ilce"], method, score))

    # Uygula
    for (il, ilce), area in fixes.items():
        m = zero_mask & df["il"].eq(il) & df["ilce"].eq(ilce)
        df.loc[m, "yuzey_alani_km2"] = area

    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    remaining = int(df["yuzey_alani_km2"].eq(0).groupby([df["il"], df["ilce"]]).first().sum())
    print(f"Sıfır alanlı ilçe (başlangıç): {len(zero_pairs)}")
    print(f"Düzeltilen                    : {len(fixes)}")
    print(f"Çözülemeyen                   : {len(unresolved)}")
    for il, ilce, method, score in unresolved[:20]:
        print(f"  - {il} / {ilce}  ({method}, skor={score:.0f})")
    print(f"Kalan sıfır alanlı ilçe       : {remaining}")
    print(f"-> Temiz veri seti: {OUTPUT.name}")


if __name__ == "__main__":
    main()
