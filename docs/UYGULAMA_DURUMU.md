# Buraki — Uygulama Durumu

**Güncelleme:** 2026-06-20

Bu belge [`YAPIM_PLANI.md`](YAPIM_PLANI.md)'ndaki fazların gerçekleşen durumunu özetler.

## Tamamlanan Fazlar

| Faz | Durum | Çıktılar | Doğrulama |
| --- | ----- | -------- | --------- |
| **0** Ortam/iskelet | ✅ | venv (Py 3.12, 93+ paket), dizin yapısı, docker-compose, CI | `pytest` yeşil |
| **1** Veri sağlamlaştırma | ✅ | `district_master.csv` (957), `district_alias.csv`, `data_quality_report.json`, **117/117 sıfır yüzölçümü düzeltildi** → `XGBoost_Egitim_Veriseti_Temiz.csv` | Kalite kapıları: 957 ilçe, 365 gün, 0 sıfır alan |
| **2** Deterministik skor motoru | ✅ | `scoring_config.json` (gerçek min/max), `ml/scoring/engine.py`, backend kopyası | Golden test: CSV skorlarını ±0.05 üretir |
| **3** Özet veri | ✅ | `district_score_summary.csv` (957), `district_monthly_profile.csv` (11.484) | İlk sıralar Şanlıurfa (raporla uyumlu) |
| **4** Backend API | ✅ | search, summary, district GeoJSON, scores/map, scores/ranking, scenarios/simulate | API, geometri ve CORS testleri geçti |
| **5** Frontend MVP | ✅ | MapLibre choropleth harita, dashboard, sıralama, arama, ilçe detay, aylık grafik, SHAP paneli, login, projeler, senaryo kaydı, PDF rapor ve admin paneli | Lint, type-check, production build ve tarayıcı etkileşim testi geçti |
| **6** SHAP | ✅ | `shap/local`, `shap/district`, `shap/global`, `global_shap_summary.json` | SHAP toplam=tahmin tutarlılığı testi geçti |
| **7** Kalıcılık | ✅ | SQLite (dev) persistence, `saved_project`/`saved_scenario`, kaydet/listele/sil | Owner/IDOR izolasyon testi geçti |
| **8** Rapor/Auth/Admin | ✅ | JWT login + RBAC, PDF rapor (reportlab), admin publish/rollback + audit log | 4 test (login, PDF, RBAC 403, publish+audit) |
| **9** DB geçişi/Observability | ✅ | SQL/CSV ortak repository, yıllık özet + aylık profil migration'ı, idempotent seed, `readyz`/`metrics` | CSV-SQL sözleşme testi; migration → seed → API smoke testi ✓ |

## Test Özeti

```
backend/  : 21 passed  (önceki API testleri + SQL/CSV eşdeğerliği,
                        idempotent seed ve Alembic şema testi)
ml/tests/ :  3 passed  (golden scoring, score bounds, GeoJSON integrity)
frontend/ : lint + type-check + Next.js production build geçti
```

Kullanıcı testi için adım adım plan: [`KULLANICI_TEST_PLANI.md`](KULLANICI_TEST_PLANI.md).

## Kimlik / Roller (demo)

| Kullanıcı | Parola | Rol |
| --------- | ------ | --- |
| admin | admin123 | admin (publish/rollback/audit) |
| analyst | analyst123 | analyst |

`POST /api/v1/auth/login` → `access_token` → `Authorization: Bearer <token>`.
Parola hashleme pbkdf2_sha256 (bcrypt 5.x uyumsuzluğu nedeniyle).

## Tek Komutla Yeniden Üretim

```bash
# Backend venv ile:
python scripts/build_all.py     # Veri, geometri, skor ve SHAP artefaktları
```

## API Doğrulanan Endpointler

| Endpoint | Örnek |
| -------- | ----- |
| `GET /api/v1/districts/search?q=şanlıurfa` | İlçe arama |
| `GET /api/v1/districts/geojson` | 973 güncel ilçe sınırı + canonical kimlik |
| `GET /api/v1/districts/{id}/summary` | Özet + aylık + girdiler |
| `GET /api/v1/scores/ranking?energy=ges&limit=5` | İlk 5: ŞANLIURFA/HARRAN (73.91)… |
| `GET /api/v1/scores/map?energy=res` | 957 ilçe choropleth verisi |
| `POST /api/v1/scenarios/simulate` | Teşvik/eğim senaryosu |
| `GET /api/v1/shap/district/{id}/ges` | Yerel SHAP |
| `GET /api/v1/shap/global/ges` | Global önem (ALLSKY, teşvik, eğim) |

## Bekleyen / Sonraki Adımlar

- **Gerçek PostgreSQL ortam doğrulaması**: repository ve PostgreSQL dialect SQL üretimi doğrulandı; bu makinede Docker bulunmadığı için canlı konteyner entegrasyon testi çalıştırılamadı. Docker olan ortamda Compose migration → seed → API sırasını otomatik uygular.
- **Vector tile geçişi**: 3,4 MB GeoJSON MVP için yeterli; veri veya trafik büyüdüğünde PMTiles/MVT ile kademeli yüklemeye geçilebilir.
- **Rapor kuyruğu**: PDF şu an senkron üretiliyor; yük artarsa RQ worker'a taşınabilir (kütüphane kurulu).
- **Gerçek OIDC**: demo kullanıcı deposu yerine kurumsal kimlik sağlayıcı.

## Önemli Tasarım Notları

- **Deterministik motor birincil**, XGBoost yardımcı, SHAP açıklama — rapordaki ilkeye sadık.
- Yerel SQLite geliştirmede CSV repository, PostgreSQL bağlantısında SQL repository otomatik seçilir; iki uygulama aynı API sözleşmesiyle test edilir.
- Harita 973 güncel sınırı gösterir; veri setinde bulunmayan 17 yeni ilçe tarihsel ana ilçe skorunu açıklamalı biçimde miras alır.
- Tüm skor yanıtları `data_version`/`scoring_version` taşır; arayüzde "yatırım tavsiyesi değildir" uyarısı sabit.
