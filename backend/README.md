# Buraki Backend

FastAPI tabanlı modüler monolit. PostgreSQL/PostGIS, Redis ve XGBoost ile çalışır.

## Komutlar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest
ruff check app
```

Varsayılan yerel geliştirme SQLite + CSV repository ile sunucusuz çalışır.
PostgreSQL repository için proje kökündeki `.env.example` dosyasını `.env` olarak
kopyalayın ve aşağıdaki sırayı kullanın:

```bash
alembic upgrade head
cd ..
python scripts/seed_db.py
cd backend
uvicorn app.main:app --reload
```

`DATA_REPOSITORY=auto`, SQLite'ta CSV'yi; PostgreSQL bağlantısında SQL
repository'yi seçer. Zorunlu seçim için `csv` veya `database` verilebilir.

## API Yüzeyi (taslak)

| Yol | Açıklama |
| --- | -------- |
| `GET /api/v1/districts/search?q=` | İl/ilçe arama |
| `GET /api/v1/districts/{id}/summary` | İlçe özet skoru |
| `GET /api/v1/scores/map?energy=ges` | Choropleth harita için skorlar |
| `GET /api/v1/scores/ranking?energy=res` | İlçe sıralaması |
| `POST /api/v1/shap/local` | Yerel SHAP açıklaması |
| `GET /api/v1/shap/global/{energy}` | Global SHAP özet |
| `POST /api/v1/scenarios/simulate` | Senaryo simülasyonu |
| `POST /api/v1/reports/jobs` | Rapor üretim işi |

Tüm yanıtlar `data_version`, `scoring_version`, `model_version` metadata'sını içermelidir.
