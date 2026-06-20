# Buraki ML

Veri hazırlama, deterministik skor üretimi, XGBoost eğitimi ve SHAP analizleri.

## Klasörler

| Klasör | İçerik |
| ------ | ------ |
| `pipelines/` | Ham veri birleştirme, ad normalizasyon (`veri_birlestirme.py`, `ad_normalizasyon.py`) |
| `scoring/` | Deterministik GES/RES skor motoru ve yıllık sıralamalar (`calculate_scores.py`, `ilk5.py`) |
| `training/` | XGBoost model eğitim ve değerlendirme (`egitim_test.py`, `makine_ogrenmesi.py`) |
| `shap/` | SHAP global/yerel açıklamalar (`shap_analysis.py`, `aciklanabilir_ai.py`, `shap_hesapli.py`) |
| `notebooks/` | Keşif amaçlı Jupyter notebook'ları |

## Akış (Ana Rapor 5.1)

1. NASA POWER kayıtları → `data/raw/`
2. Rakım + eğim ekle
3. Yüzölçümü ve CORINE arazi sınıfı eklenir → `data/processed/`
4. İl bazlı teşvik bölgesi eşlenir
5. Min-Max normalizasyon + GES/RES ham skor → 0–100 ölçek
6. XGBoost eğitimi → `data/models/`
7. SHAP global + yerel → `data/shap/`
