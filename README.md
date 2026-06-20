# Buraki — Yapay Zekâ Destekli Yenilenebilir Enerji Yatırım Karar Destek Sistemi

Türkiye genelinde ilçe düzeyinde **GES (Güneş Enerjisi Santrali)** ve **RES (Rüzgâr Enerjisi Santrali)** yatırımları için 0–100 aralığında ayrı skorlar üreten, harita tabanlı bir karar destek sistemi prototipi.

> Bu proje akademik bir bitirme projesi olarak başlamış olup TÜBİTAK 2209-A başvurusu kapsamında belgelendirilmiştir. Sistem **yatırım tavsiyesi değildir**; ön eleme, karşılaştırma ve açıklanabilir raporlama amacıyla geliştirilmiştir.

## Özet Mimari

```
              ┌───────────────────────────────────────────────┐
              │  Frontend (React + TypeScript)                │
              │  Harita · Karşılaştırma · Senaryo · Rapor     │
              └────────────────────┬──────────────────────────┘
                                   │ REST  /api/v1/...
              ┌────────────────────▼──────────────────────────┐
              │  Backend (FastAPI, modüler monolit)           │
              │  ScoreService · ModelService · ShapService    │
              │  ReportWorker · DataPipeline · AdminAPI       │
              └────────────────────┬──────────────────────────┘
                                   │
       ┌────────────────┬──────────┴───────────┬────────────────┐
       ▼                ▼                      ▼                ▼
   PostgreSQL/        Redis                Object Storage     XGBoost
   PostGIS                                  (modeller,        + SHAP
                                            raporlar)
```

## Veri Seti

- **2023 yılı**, 365 gün × **957 il+ilçe çifti** × 81 il = **349.305 satır**, 17 sütun.
- Kaynaklar: NASA POWER (meteoroloji), CORINE 2018 (arazi sınıfı), il/ilçe yüzölçümü ve eğim tabloları, il bazlı teşvik bölgesi.
- 12 sayısal özellik → iki XGBoost regresyonu (GES, RES) → 0–100 skor.

## Dizin Yapısı

```
Buraki/
├── backend/         # FastAPI servisi, modüler monolit
│   ├── app/
│   │   ├── api/v1/      # REST endpointleri
│   │   ├── core/        # ayarlar, güvenlik, logging
│   │   ├── db/          # SQLAlchemy modelleri, migration
│   │   ├── ml/          # model loader, feature builder
│   │   ├── schemas/     # Pydantic sözleşmeleri
│   │   └── services/    # ScoreService, ShapService, vs.
│   ├── tests/
│   └── requirements.txt
├── frontend/        # React + TypeScript web arayüzü
│   ├── src/
│   │   ├── app/         # sayfa yönlendirmeleri
│   │   ├── components/  # bileşenler (harita, grafik, vb.)
│   │   ├── lib/         # API istemcisi, hooks
│   │   └── styles/
│   └── package.json
├── ml/              # Eğitim, skor ve SHAP pipeline'ları
│   ├── pipelines/       # veri birleştirme, ad normalizasyon
│   ├── scoring/         # deterministik skor motoru
│   ├── training/        # XGBoost eğitimi
│   ├── shap/            # SHAP analizleri
│   └── notebooks/
├── data/            # Veri katmanları (versiyonlanabilir DVC/LFS)
│   ├── raw/             # NASA POWER vb. ham veri
│   ├── processed/       # birleştirilmiş eğitim verisi
│   ├── reference/       # il/ilçe lookup tabloları
│   ├── models/          # XGBoost JSON artefaktları
│   └── shap/            # SHAP pickle ve özetleri
├── docs/            # Tüm rapor ve dökümanlar
│   ├── raporlar/        # 3 ana teknik rapor + bitirme + tubitak
│   ├── notlar/          # tasarım notları, GPT tavsiyeleri
│   └── gorseller/
├── scripts/         # CLI yardımcı betikleri
├── infra/           # docker, db migration, ortam yapılandırması
└── .github/         # CI/CD
```

## Hızlı Başlangıç

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate         # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: `http://localhost:3000`

Kullanıcı testleri için demo hesaplar:

- analyst / analyst123
- admin / admin123

Test senaryoları: [`docs/KULLANICI_TEST_PLANI.md`](docs/KULLANICI_TEST_PLANI.md)

### Docker Compose (tümü)

```bash
docker compose -f infra/docker-compose.yml up --build
```

Compose, PostgreSQL sağlıklı olduktan sonra Alembic migration'larını uygular,
957 ilçe özeti ile 11.484 aylık kaydı idempotent olarak yükler ve API'yi başlatır.
`DATA_REPOSITORY=database` konteyner içinde varsayılan olarak etkindir.
PostgreSQL kullanıcı/parolasını değiştirirseniz `.env` içindeki
`API_DATABASE_URL` değerini de aynı bilgilerle güncelleyin.

PostgreSQL'i host üzerinden ayrı çalıştırmak için:

```bash
copy .env.example .env          # Windows; parolaları değiştirin
docker compose -f infra/docker-compose.yml up -d postgres redis
cd backend
alembic upgrade head
cd ..
python scripts/seed_db.py
```

## Ana Bileşenler

| Modül | Sorumluluğu |
| ----- | ----------- |
| `ml/scoring/calculate_scores.py` | Deterministik GES/RES skor motoru (üretim birincil kaynağı) |
| `ml/training/egitim_test.py` | XGBoost modellerinin eğitimi |
| `ml/shap/aciklanabilir_ai.py` | SHAP global + yerel açıklamalar |
| `backend/app/services/score_service.py` | API üzerinden skor servisi |
| `backend/app/services/shap_service.py` | Yerel/global SHAP yanıtları |
| `frontend/src/components/Map` | Choropleth Türkiye haritası |

## Belgeler

- [`docs/raporlar/01_Ana_Proje_Teknik_Raporu.docx`](docs/raporlar/01_Ana_Proje_Teknik_Raporu.docx) — proje tanımı, veri, model, yol haritası
- [`docs/raporlar/02_Sistem_ve_Arayuz_Tasarim_Raporu.docx`](docs/raporlar/02_Sistem_ve_Arayuz_Tasarim_Raporu.docx) — UX, akışlar, tasarım sistemi
- [`docs/raporlar/03_Backend_Tasarim_ve_Uygulama_Raporu.docx`](docs/raporlar/03_Backend_Tasarim_ve_Uygulama_Raporu.docx) — backend mimari, API, dağıtım
- [`docs/raporlar/tubitak/`](docs/raporlar/tubitak/) — TÜBİTAK 2209-A başvuru belgeleri

## Lisans

Akademik amaçlıdır; ticari yatırım kararlarına temel teşkil etmez.
