# Buraki — Büyük Aşamalı Yapım Planı

**Proje:** Yapay Zekâ Destekli Yenilenebilir Enerji Yatırım Karar Destek Sistemi
**Sürüm:** 1.0 · **Tarih:** 2026-06-20
**Kaynak belgeler:** `docs/raporlar/01–03` + bitirme raporu + TÜBİTAK 2209-A

Bu belge; teknoloji yığınını, kullanılacak tüm kütüphaneleri ve projeyi sıfırdan üretime taşıyacak **9 fazlı** yol haritasını tanımlar. Her faz; amaç, kütüphaneler, görevler, çıktı ve kabul kriterleri içerir.

---

## 0. Mimari Özet

```
Frontend (Next.js/React/TS)  ──REST /api/v1──▶  Backend (FastAPI modüler monolit)
   MapLibre · Recharts · Query                     ScoreService · ModelService
                                                    ShapService · ReportWorker
                                                          │
                  ┌───────────────────┬─────────────────┼──────────────────┐
                  ▼                   ▼                  ▼                  ▼
            PostgreSQL/PostGIS     Redis          Object Storage      XGBoost+SHAP
            (district, daily,    (cache/queue)   (model, rapor)       (inference)
             summary, registry)
```

**Temel ilke (raporlardan):** Deterministik skor motoru birincil kaynaktır; XGBoost yardımcı/yaklaşıklayıcı, SHAP ise açıklama katmanıdır. Skorlar yatırım tavsiyesi değildir.

---

## 1. Teknoloji Yığını ve Kütüphane Envanteri

### 1.1 Backend (Python 3.12)

| Kütüphane | Sürüm | Amaç |
| --------- | ----- | ---- |
| `fastapi` | 0.115.x | REST API çatısı |
| `uvicorn[standard]` | 0.32.x | ASGI sunucu |
| `pydantic` / `pydantic-settings` | 2.10.x / 2.7.x | Şema doğrulama, ayar yönetimi |
| `SQLAlchemy` | 2.0.x | ORM |
| `psycopg[binary]` | 3.2.x | PostgreSQL sürücüsü |
| `alembic` | 1.14.x | DB migration |
| `geoalchemy2` | 0.16.x | PostGIS geometri tipleri |
| `redis` | 5.2.x | Cache / pub-sub |
| `rq` | 2.0.x | İş kuyruğu (rapor, batch SHAP) |
| `python-jose[cryptography]` | 3.3.x | JWT |
| `passlib[bcrypt]` | 1.7.x | Parola hashleme |
| `numpy` / `pandas` | 2.2.x / 2.2.x | Sayısal/veri işleme |
| `scikit-learn` | 1.6.x | Yardımcı ML metrikleri |
| `xgboost` | 2.1.x | GES/RES regresyon modelleri |
| `shap` | 0.46.x | Açıklanabilirlik (TreeExplainer) |
| `httpx` | 0.28.x | Dış servis çağrıları (NASA POWER vb.) |
| `loguru` | 0.7.x | Yapısal loglama |
| `pytest` / `pytest-asyncio` | 8.3.x | Test |
| `ruff` / `mypy` | 0.8.x / 1.13.x | Lint / tip kontrol |

**Rapor önerilen ek paketler (faza göre eklenecek):** `weasyprint` veya `reportlab` (PDF rapor üretimi), `boto3` / `minio` (object storage), `prometheus-client` + `opentelemetry` (gözlemlenebilirlik), `slowapi` (rate limit).

### 1.2 Frontend (Node.js 20+ — KURULMASI GEREKİYOR)

| Kütüphane | Amaç |
| --------- | ---- |
| `next` 15 · `react` 19 · `react-dom` 19 | Uygulama çatısı |
| `typescript` 5 | Tip güvenliği |
| `@tanstack/react-query` 5 | Sunucu durumu / cache |
| `maplibre-gl` 4 | Vektör tile choropleth harita |
| `recharts` 2 | Erişilebilir grafikler |
| `zod` 3 | Şema doğrulama (API tipleri) |
| `eslint` + `eslint-config-next` | Lint |

**Faza göre eklenecek:** `@radix-ui/*` veya `shadcn/ui` (bileşen kataloğu), `@storybook/nextjs` (görsel regresyon), `playwright` (E2E), `vitest` + `@testing-library/react` (birim test), `openapi-typescript` (API'den otomatik tip üretimi).

> ⚠️ **Önkoşul:** Bu makinede Node.js/npm kurulu değil. Frontend kütüphanelerinin kurulabilmesi için Node.js 20 LTS yüklenmelidir (https://nodejs.org). Kurulum sonrası `cd frontend && npm install`.

### 1.3 ML / Veri Bilimi (Python 3.12)

| Kütüphane | Amaç |
| --------- | ---- |
| `pandas` · `numpy` | Veri birleştirme, normalizasyon |
| `xgboost` | Model eğitimi |
| `shap` | Global/yerel açıklama |
| `scikit-learn` | Bölme, metrik, GroupKFold |
| `matplotlib` · `seaborn` | Görselleştirme |
| `openpyxl` | Excel okuma (lookup tabloları) |
| `joblib` | Artefakt serileştirme |
| `jupyter` | Keşif notebook'ları |

### 1.4 Altyapı

| Bileşen | Teknoloji |
| ------- | --------- |
| Veritabanı | PostgreSQL 16 + PostGIS 3.4 |
| Cache/Kuyruk | Redis 7 |
| Konteyner | Docker + docker-compose |
| CI/CD | GitHub Actions |
| Object Storage | S3-uyumlu (MinIO/yerel veya bulut) |

---

## 2. Fazlı Yol Haritası

Toplam hedef ~12 hafta (tek geliştiricide 14–18 hafta). MVP = Faz 1–5.

### Faz 0 — Ortam ve İskelet *(Tamamlandı / sürüyor)*
- **Amaç:** Depo yapısı, bağımlılıklar, geliştirme ortamı.
- **Görevler:** Dizin yapısı ✅, `requirements.txt`/`package.json` ✅, venv + bağımlılık kurulumu (sürüyor), Node.js kurulumu (bekliyor), `.env` yapılandırması, docker-compose ✅, CI iskeleti ✅.
- **Kabul:** `uvicorn app.main:app` çalışıyor, `GET /healthz` 200 döner; `pytest` yeşil.

### Faz 1 — Veri Sağlamlaştırma ve Canonical İlçe Kimliği
- **Amaç:** Tüm kaynakları tek `district_master`'a bağlamak; rapordaki kritik veri kalitesi sorunlarını gidermek.
- **Kütüphaneler:** `pandas`, `openpyxl`, `rapidfuzz` (ad eşleştirme), `unidecode`.
- **Görevler:**
  1. İl/ilçe ad normalizasyonu (`ml/pipelines/ad_normalizasyon.py` genişlet) — büyük harf, Türkçe karakter, alias tablosu.
  2. Değişmez `district_id` üretimi; `district_alias` tablosu (source_name → district_id, match_method, confidence).
  3. **117 sıfır yüzölçümünü** düzelt (rapor 3, Ek C).
  4. NASA POWER + rakım + eğim + yüzölçümü + CORINE + teşvik birleştirme (`ml/pipelines/veri_birlestirme.py`).
  5. Veri kalite raporu şeması (district_count, area_zero, min/max, dağılım).
- **Çıktı:** `data/processed/` altında temiz final veri seti + kalite raporu JSON.
- **Kabul:** `district_count == 957`, `area_zero == 0`, her ilçe için 365 kayıt.

### Faz 2 — Deterministik Skor Motoru + Scoring Config
- **Amaç:** Üretimin birincil skor kaynağını koddan ayrıştırıp versiyonlamak.
- **Kütüphaneler:** `pandas`, `numpy`, `pydantic`.
- **Görevler:**
  1. `scoring_config.json` ham min/max değerlerini veri setinden hesapla ve doldur.
  2. `ml/scoring/calculate_scores.py`'yi config-tabanlı hale getir (ağırlıklar %60/%30/-%10).
  3. Min-Max → ham skor → 0–100 ölçek; percentile/sıralama üret.
  4. `backend/app/services/score_service.py` config'i yükleyip aynı sonucu üretsin (golden test).
- **Çıktı:** Sürümlenmiş `scoring_config.json`, checksum'lı.
- **Kabul:** Python pipeline ile backend ScoreService aynı ilçe için ±0.01 fark içinde skor üretir.

### Faz 3 — Veritabanı, Migration ve Agregasyon
- **Amaç:** Üretim şeması + önceden hesaplanmış özetler.
- **Kütüphaneler:** `SQLAlchemy`, `alembic`, `geoalchemy2`, `psycopg`.
- **Görevler:**
  1. Tablolar: `district_master`, `district_alias`, `daily_observation`, `district_score_summary`, `model_registry`, `dataset_version`, `audit_log`.
  2. Alembic migration'ları (boş DB + upgrade testi).
  3. Veri yükleme betiği (`scripts/seed_*`), 349.305 satır.
  4. `district_score_summary` üret (mean, median, p10, p90, stddev, national_rank, percentile).
  5. PostGIS ilçe geometrileri (basitleştirilmiş, vector tile için).
- **Kabul:** Dashboard sorguları özet tablodan çalışıyor; günlük tablo taranmıyor.

### Faz 4 — Çekirdek API
- **Amaç:** Frontend'in ihtiyaç duyduğu okuma endpointleri.
- **Kütüphaneler:** `fastapi`, `pydantic`, `redis`, `slowapi`.
- **Görevler:**
  1. `districts/search`, `districts/{id}/summary`, `scores/map`, `scores/ranking` implementasyonu.
  2. Redis cache; precomputed summary kullanımı.
  3. Problem Details hata şeması, `X-Request-ID`, sürüm metadata'sı.
  4. Sayfalama (cursor/limit), input doğrulama.
- **Kabul:** Tüm okuma endpointleri gerçek veriyle yanıt veriyor; yanıtlar `data_version`/`scoring_version` içeriyor.

### Faz 5 — Frontend MVP (Harita + İlçe Detay)
- **Amaç:** İlk üretilebilir kullanıcı arayüzü.
- **Kütüphaneler:** `next`, `react`, `@tanstack/react-query`, `maplibre-gl`, `recharts`, `zod`, `openapi-typescript`.
- **Görevler:**
  1. Tasarım tokenları, layout, navigation (rapor 02 tasarım sistemi).
  2. Choropleth Türkiye haritası + tablo alternatifi + legend (0–100 / percentile).
  3. İlçe detay drawer/sayfa: yıllık skor, percentile, aylık profil, girdiler, metodoloji metadata.
  4. URL-tabanlı filtre durumu; enerji türü (GES/RES) ve dönem seçimi.
  5. API tiplerini `openapi-typescript` ile üret.
- **Kabul:** Kullanıcı GES/RES seçip haritada ilçe tıklayıp detay görebiliyor. MVP burada tamamlanır.

### Faz 6 — Açıklanabilirlik (SHAP) ve Karşılaştırma
- **Amaç:** Formül katkısı + SHAP açıklaması; 2–5 ilçe karşılaştırma.
- **Kütüphaneler:** `shap`, `xgboost`, `recharts`.
- **Görevler:**
  1. `ModelService` ile XGBoost yükleme (checksum, feature_schema doğrulama, golden smoke).
  2. Yerel SHAP (`shap/local`) — sync, p95 aşılırsa async kuyruğa.
  3. Global SHAP artefaktını offline üret, object storage'a yaz, `shap/global/{energy}` servis et.
  4. Frontend: formül katkısı vs SHAP yan yana; karşılaştırma tablosu/radar/zaman serisi + CSV dışa aktarma.
- **Kabul:** SHAP katkılarının toplamı tahminle tolerans içinde; "neden farklı?" görünümü çalışıyor.

### Faz 7 — Senaryo Simülatörü ve Kayıtlı Projeler
- **Amaç:** Girdileri değiştirerek "ne olur" analizi.
- **Görevler:**
  1. `scenarios/simulate` — yalnız izinli alanlar, fiziksel aralık doğrulaması.
  2. Orijinal vs senaryo yan yana; skor/katkı farkı; varsayım listesi.
  3. `input_snapshot` + `scoring_version` ile kayıt; gözlem verisini değiştirmeme.
  4. Kayıtlı projeler (tenant/owner kontrolü, IDOR testi).
- **Kabul:** Senaryo "simülasyon" etiketiyle ayrışıyor; kalıcı veriyi bozmuyor.

### Faz 8 — Rapor Üretimi, Auth ve Yönetim
- **Amaç:** İndirilebilir rapor + güvenlik + admin ekranları.
- **Kütüphaneler:** `rq`, `weasyprint`/`reportlab`, `python-jose`, `passlib`, `boto3`/`minio`.
- **Görevler:**
  1. Rapor kuyruğu (RQ worker); PDF şablonu (rapor 02 Ek B bölümleri); süreli signed URL.
  2. OIDC/OAuth2 + RBAC + tenant kontrolü; audit log.
  3. Admin: veri paketi yükleme → kalite kontrol → publish/rollback (staging vs published, pointer swap).
  4. Model registry: aktif/önceki model, çift onay ile aktivasyon.
- **Kabul:** Rapor indirilebiliyor; publish/rollback audit log üretiyor; yetkisiz erişim engelleniyor.

### Faz 9 — Gözlemlenebilirlik, Performans ve Sürüm
- **Amaç:** Üretime hazır olma (rapor 03 Ek C kontrol listesi).
- **Kütüphaneler:** `prometheus-client`, `opentelemetry`, `playwright`, `locust`.
- **Görevler:**
  1. Metrikler/alarmlar: ready fail, model yüklenememe, `district_count≠957`, `area_zero>0`, queue backlog, rapor hata oranı.
  2. CI tam pipeline: lint, tip, unit, contract, migration, golden, container build + SBOM + güvenlik tarama, E2E, canary deploy.
  3. Erişilebilirlik (AA), performans, backup/restore + rollback tatbikatı.
- **Kabul:** Rapor 03 Ek C "Üretim Öncesi Zorunlu Kontrol Listesi" tüm maddeleri yeşil.

---

## 3. Bağımlılıklar (Faz Sırası)

```
Faz 0 → Faz 1 → Faz 2 → Faz 3 → Faz 4 → Faz 5 (MVP)
                                    └────→ Faz 6 → Faz 7 → Faz 8 → Faz 9
```

## 4. Riskler (Rapor 10.1 / Tehdit Modeli)
- İlçe ad eşleştirme hataları → canonical ID ve confidence skoru ile yönet.
- Skorun "kârlılık" sanılması → her ekranda metodoloji/sınır uyarısı.
- Büyük SHAP pickle bellek baskısı → object storage + özet tablo.
- Veri/model sürüm karışıklığı → registry + dataset_version pointer + golden test.

## 5. Sonraki Adım
1. Node.js 20 LTS kur → `cd frontend && npm install`.
2. Backend bağımlılık kurulumunu doğrula → `pytest`.
3. Faz 1'e başla: `ml/pipelines/` veri birleştirme + canonical district_id.
