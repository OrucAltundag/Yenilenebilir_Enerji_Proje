"""data/reference altındaki il/ilçe lookup dosyalarından district_master tablosunu üretir.

Çalıştırma:
    python scripts/seed_district_master.py
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "reference"


def main() -> None:
    alanlar = pd.read_excel(DATA_DIR / "il_ilce_alanlari.xlsx")
    yuzey = pd.read_csv(DATA_DIR / "ilce_yuzey_turu.csv")
    yuzolcum = pd.read_csv(DATA_DIR / "ilce_yuzolcumu.csv")

    print("alanlar:", alanlar.shape)
    print("yuzey:", yuzey.shape)
    print("yuzolcum:", yuzolcum.shape)
    print("TODO: il/ilçe ad normalizasyonu, canonical district_id üretimi ve DB yazımı.")


if __name__ == "__main__":
    main()
