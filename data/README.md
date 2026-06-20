# Veri Katmanları

Rapor 4.4'te tanımlanan veri katmanlarına denk düşen dizinler.

| Klasör | İçerik | Örnek dosya |
| ------ | ------ | ----------- |
| `raw/` | Kaynaktan gelen ham veri (NASA POWER, vb.) | `POWER_Daily_2025_cleaned.csv` |
| `processed/` | Birleştirilmiş, normalleştirilmiş eğitim verileri | `XGBoost_Egitim_Veriseti_Guncel.csv`, `ML_Egitime_Hazir_X_Veriseti.csv` |
| `reference/` | İl/ilçe lookup, yüzölçümü, arazi sınıfı, koordinat ve sınırlar | `il_ilce_alanlari.xlsx`, `district_boundaries.geojson` |
| `models/` | Eğitilmiş XGBoost JSON artefaktları | `Yapay_Zeka_GES_Modeli.json`, `Yapay_Zeka_RES_Modeli.json` |
| `shap/` | SHAP pickle ve global özet artefaktları | `shap_degerleri.pkl` |

> Bu klasörler büyük dosyalar içerir. Üretim deposunda Git LFS veya DVC ile yönetilmesi önerilir; `.gitignore` örnek satırlarını içerir.

## Veri Sözleşmesi (Özet)

- 12 sayısal özellik: `T2M`, `RH2M`, `WS10M`, `ALLSKY_SFC_SW_DWN`, `arazi_egimi_yuzde`, `yuzey_alani_km2`, 5 arazi one-hot alanı, `tesvik_bolgesi`.
- Hedefler: `GES_YATIRIM_SKORU`, `RES_YATIRIM_SKORU` (0–100 arası, 2 ondalık).
- 2023 yılı için 81 il × 957 il+ilçe × 365 gün = 349.305 kayıt.

## İlçe Sınırları

- Kaynak: geoBoundaries `gbOpen` Türkiye ADM2, 2021 (OpenStreetMap/OSM Boundaries).
- Lisans: Open Data Commons Open Database License 1.0.
- `scripts/build_district_geojson.py`, 973 güncel geometriyi 957 canonical skor
  kaydıyla eşleştirir. Sonradan kurulan 17 ilçe tarihsel ana ilçenin skorunu
  kullanır; bu durum GeoJSON'da `match_method=inherited` olarak işaretlenir.
- Kaynak ve eşleştirme özeti `district_boundaries.metadata.json` dosyasındadır.
