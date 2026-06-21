# QA TEST RAPORU

**Tarih:** 21 Haziran 2026  
**Hedef:** Buraki yenilenebilir enerji yatırım karar destek sistemi  
**Test türü:** Kaynak kod incelemesi, backend/ML otomasyon testleri, frontend statik doğrulama ve production build, HTTP/API manuel testleri  
**Sınırlama:** Uygulama-içi tarayıcı localhost navigasyonunda yanıt vermedi. Görsel, tıklama, klavye, responsive ve cross-browser maddeleri gerçek tarayıcıda tamamlanmadı; ilgili sonuçlar “Manuel doğrulama gerekli” olarak işaretlenmiştir.

## 1. Test Edilen Alan Özeti

- **Test edilen alan:** Ana sayfa, login/session, proje ve admin yetkilendirmesi, ilçe arama API'si, backend ve ML test paketleri, frontend lint/type/build.
- **Amaç:** Temel kullanıcı akışlarının çalışabilirliği, sözleşme doğruluğu, güvenlik ve yayına hazırlık risklerini belirlemek.
- **Roller:** Anonim, analyst, developer, admin.
- **Platform:** Windows, Python 3.12.13, Next.js 15.5.19; backend `127.0.0.1:8000`, frontend `127.0.0.1:3000`.
- **Gerçek sonuçlar:** Backend 32/32 geçti; ML 5/5 geçti; frontend lint, TypeScript ve production build geçti; API health 200; production ana sayfa HTTP 200.
- **Kritik akışlar:** Login, JWT/RBAC, ilçe arama, proje izolasyonu, admin/ML yetkileri, harita ve rapor erişimi.
- **Varsayım:** Mevcut çalışma ağacı test hedefidir. Depoda commitlenmemiş kullanıcı değişiklikleri korunmuştur.
- **Ek bilgi gerekiyor:** Hedef dağıtım ortamı, production güvenlik politikası, desteklenen cihaz/tarayıcı matrisi, SLA, veri doğruluk toleransları.

## 2. Gereksinim ve Kapsam Analizi

| Başlık | Açıklama |
| --- | --- |
| Özelliğin amacı | Türkiye ilçeleri için GES/RES skorlarını harita, sıralama, karşılaştırma, senaryo ve raporlarla sunmak |
| Beklenen ana davranış | Kullanıcı ilçe bulur, skoru inceler, karşılaştırır; yetkili kullanıcı proje/senaryo kaydeder ve rapor indirir |
| Kullanıcı rolleri | Anonim, analyst, developer, admin |
| Kritik işlemler | Kimlik doğrulama, veri/model yayınlama, model aktivasyonu, proje sahipliği, rapor üretimi |
| İş kuralları | Skor 0–100; enerji `ges/res`; proje sahibi izolasyonu; admin ve developer RBAC |
| Belirsiz noktalar | Demo kimlik doğrulamasının production'da kapatılma yöntemi; anonim erişim politikası; hesap kilitleme ve parola politikası |
| Kapsam dışı | Gerçek mobil cihaz, Safari/Firefox/Edge, yük testi, ekran okuyucu ve piksel düzeyi görsel karşılaştırma |

## 3. Arayüz Bileşenleri Envanteri

| Bileşen | Tür | Beklenen davranış | Test edilecek durumlar | Öncelik |
| --- | --- | --- | --- | --- |
| Login formu | Form | Kimlik doğrular ve oturumu gösterir | Geçerli/geçersiz/boş, loading, tekrar gönderim, timeout | Kritik |
| Navigasyon | Link grubu | Role göre doğru sayfaları gösterir | Aktif durum, geri/ileri, doğrudan URL, yetkisiz rol | Yüksek |
| İlçe arama | Arama | En az 2 karakterle sonuç döndürür | Türkçe karakter, boş, uzun, özel karakter, hızlı yazma | Yüksek |
| GES/RES seçici | Toggle | Harita, sıralama ve SHAP'ı birlikte değiştirir | Hızlı geçiş, loading, API hatası | Yüksek |
| İlçe haritası | Harita | İlçe seçimiyle detaya gider | Zoom, klavye, dokunmatik, veri yok, render hatası | Yüksek |
| Sıralama tablosu | Tablo | Yıllık sıralamayı gösterir | Sıra/veri doğruluğu, boş durum, taşma | Yüksek |
| SHAP özeti | Grafik/panel | Etki büyüklüklerini açıklar | Negatif/pozitif değer, açıklama, erişilebilirlik | Orta |
| Proje/senaryo ekranları | Form/liste | Kullanıcıya ait kayıtları yönetir | CRUD, sahiplik, çift gönderim, hata geri bildirimi | Kritik |
| Admin/Developer ekranları | Yönetim | Yetkili işlemleri çalıştırır | RBAC, onay, audit, tekrar gönderim | Kritik |
| Rapor indirme | Dosya | Yetkili PDF indirir | 401/403/404, dosya adı, bozuk PDF, tekrar | Yüksek |

## 4. İnsan Gibi Manuel Kullanıcı Testleri

| ID | Kullanıcı davranışı | Test adımları | Beklenen sonuç | Öncelik |
| --- | --- | --- | --- | --- |
| MT-001 | Analyst giriş yapar | Demo hesabıyla giriş, sayfalar arası gezinme | Oturum korunur; yalnız analyst alanları görünür | Kritik |
| MT-002 | İlçe arar | `Ankara` yaz, sonuç seç, geri dön | Doğru ilçe detayı; arama durumu anlaşılır | Yüksek |
| MT-003 | Enerji türünü hızla değiştirir | GES/RES'e art arda tıkla | Son seçim tüm panellerde tutarlı kalır | Yüksek |
| MT-004 | Oturum süresi dolar | 30 dakika sonrası korumalı işlem | Oturum temizlenir, login yönlendirmesi ve açıklayıcı mesaj gelir | Kritik |
| MT-005 | Çift kayıt gönderir | Kaydet'e hızlı çift tık | Tek kayıt oluşur veya idempotent davranır | Yüksek |

## 5. Pozitif Test Senaryoları

| ID | Senaryo | Ön koşul | Adımlar/Test verisi | Beklenen sonuç | Öncelik |
| --- | --- | --- | --- | --- | --- |
| PT-001 | Geçerli login | API açık | `analyst/analyst123` | 200, bearer token, analyst rolü — **Geçti** | Kritik |
| PT-002 | İlçe arama | Veri yüklü | `q=Ankara&limit=3` | 200 ve 3 kayıt — **Geçti** | Yüksek |
| PT-003 | API health | Backend açık | `GET /healthz` | 200 `status=ok` — **Geçti** | Kritik |
| PT-004 | Production frontend | Build tamam | `GET /` | 200 ve Buraki içeriği — **Geçti** | Kritik |
| PT-005 | Admin rol engeli | Analyst token | Admin dataset endpointi | 403 — **Geçti** | Kritik |

## 6. Negatif Test Senaryoları

| ID | Senaryo | Hatalı veri/davranış | Beklenen tepki | Sonuç | Öncelik |
| --- | --- | --- | --- | --- | --- |
| NT-001 | Hatalı parola | `analyst/wrong` | 401, genel hata | **Geçti** | Yüksek |
| NT-002 | Boş login | Boş username/password | Alan bazlı doğrulama veya 401 | 401 genel hata; UX doğrulaması eksik | Orta |
| NT-003 | Boş arama | `q=` | 422, min 2 karakter sözleşmesi | **Geçti** | Orta |
| NT-004 | Token olmadan proje listesi | Authorization yok | 401 | **Kaldı: 200 ve `[]`** | Kritik |
| NT-005 | Analyst ile admin erişimi | Analyst JWT | 403 | **Geçti** | Kritik |

## 7. Edge Case ve Boundary Testleri

| ID | Durum | Beklenen sonuç | Risk | Öncelik |
| --- | --- | --- | --- | --- |
| EC-001 | Arama 1/2 karakter | 1 karakter reddedilir, 2 kabul edilir | UI/API tutarsızlığı | Orta |
| EC-002 | Limit 0, negatif, çok büyük | Sınırlandırılmış 4xx veya güvenli üst limit | Kaynak tüketimi | Yüksek |
| EC-003 | JWT tam sona ererken istek | Tek ve anlaşılır 401; UI oturumu temizler | Kullanıcı kilitlenmesi | Yüksek |
| EC-004 | Aynı proje iki kez kaydedilir | Tek kayıt/idempotency veya buton kilidi | Çift veri | Yüksek |
| EC-005 | Türkçe küçük/büyük `i/İ/ı` araması | Normalizasyonlu doğru sonuç | Sonuç kaçırma | Orta |

## 8. Tıklanabilirlik ve Çalışabilirlik Kontrolü

| Alan | Kontrol | Beklenen | Durum |
| --- | --- | --- | --- |
| Giriş yap | Tek gönderim, loading, hata | Pending'de disabled; hata görünür | Kodda mevcut; görsel doğrulama gerekli |
| Çıkış | Token/rol/kullanıcı temizliği | Ana ekran login durumuna döner | Kodda mevcut; manuel doğrulama gerekli |
| Menü linkleri | Doğru route ve active state | Role uygun görünürlük | Kodda mevcut; doğrudan URL RBAC ayrıca test edilmeli |
| Harita ilçeleri | Click/touch/keyboard | İlçe detayına gider | Manuel doğrulama gerekli |
| GES/RES | Tüm bağlı veriyi yenileme | Seçim ve içerik tutarlı | Manuel doğrulama gerekli |

## 9. Form ve Input Validasyon Testleri

| Alan | Geçerli | Geçersiz | Boş davranışı | Sınır | Beklenen uyarı | Öncelik |
| --- | --- | --- | --- | --- | --- | --- |
| Kullanıcı adı | `analyst` | uzun/Unicode/SQL-XSS dizileri | Şu an API 401 | Tanımlı değil | Alan bazlı, veri sızdırmayan mesaj | Yüksek |
| Parola | Doğru parola | yanlış/çok uzun | Şu an API 401 | Tanımlı değil | Genel auth mesajı | Yüksek |
| İlçe arama | 2+ karakter | kontrol karakteri/çok uzun | 422 | min 2; max ek bilgi gerekir | UI'da açıklayıcı mesaj | Orta |
| Proje adı | Normal ad | boş/yalnız boşluk/çok uzun | Şema ile doğrulanmalı | Kaynak sözleşmesi doğrulanmalı | Alan bazlı uyarı | Yüksek |
| Senaryo override | İzinli ve aralık içi | bilinmeyen alan/NaN/aralık dışı | Sözleşmeye göre | Güneş 0–12, rüzgâr 0–25 vb. | 422 ve alan adı | Yüksek |

## 10. Navigasyon ve Kullanıcı Akışı Testleri

| ID | Akış | Beklenen | Risk | Öncelik |
| --- | --- | --- | --- | --- |
| NAV-001 | Login → Projeler → geri | Oturum ve liste korunur | State kaybı | Yüksek |
| NAV-002 | Analyst doğrudan `/admin` | Sayfa/API erişimi reddedilir | UI route guard belirsiz | Kritik |
| NAV-003 | Süresi dolmuş tokenla `/reports` | Login'e dön, niyet korunsun | UI sonsuz hata hali | Yüksek |
| NAV-004 | İlçe detayında yenileme | Aynı ilçe verisi açılır | Dynamic route/404 | Yüksek |

## 11. UI/UX Değerlendirmesi

| Gözlem/Risk | Kullanıcı etkisi | Öneri | Öncelik |
| --- | --- | --- | --- |
| Demo kullanıcı/parolaları ekranda ve varsayılan dolu | Yanlış ortamda hesapların kötüye kullanımı | Yalnız açık demo flag'iyle göster; production build'de kaldır | Kritik |
| Login hatası `role=alert`/live region değil | Ekran okuyucu hatayı kaçırabilir | `aria-live="assertive"` veya `role="alert"` | Orta |
| Inputlarda `autocomplete` yok | Parola yöneticisi ve mobil klavye deneyimi zayıf | `username` ve `current-password` ekle | Düşük |
| Session expiry UI yönetimi görünmüyor | Kullanıcı giriş yapmış görünür fakat işlemler 401 olur | Global 401 interceptor ve kontrollü logout | Yüksek |
| Rol bilgisi localStorage'dan okunuyor | Manipüle edilince yanlış menü görünür; backend reddetse de kafa karıştırır | `/me` ile sunucu doğrulaması veya token claim doğrulama | Orta |

Görsel hiyerarşi, kontrast, loading/empty state, mobil taşma ve harita erişilebilirliği için gerçek tarayıcıda manuel doğrulama gereklidir.

## 12. Responsive ve Cross-Browser Testleri

| ID | Cihaz/Tarayıcı | Alan | Beklenen | Durum |
| --- | --- | --- | --- | --- |
| RB-001 | 360×800 Chrome | Login, menü, harita, tablo | Yatay taşma yok; dokunma hedefi ≥44px | Manuel gerekli |
| RB-002 | 768×1024 Safari | Harita ve dashboard grid | Kartlar düzenli kırılır | Manuel gerekli |
| RB-003 | 1280×720 Edge/Chrome | Tüm ana ekran | İçerik 1180px alanda okunur | Manuel gerekli |
| RB-004 | Firefox güncel | Harita ve indirme | Aynı fonksiyon ve dosya adı | Manuel gerekli |

## 13. Güvenlik Testleri

| ID | Risk | Test | Beklenen güvenli davranış | Sonuç | Öncelik |
| --- | --- | --- | --- | --- | --- |
| SEC-001 | Yetkisiz proje erişimi | Tokensız `GET /projects` | 401 | 200 — **Kaldı** | Kritik |
| SEC-002 | Kimlik sahteciliği | İstemci kontrollü `X-User-Id` | Production'da reddedilmeli | Kod kabul ediyor | Kritik |
| SEC-003 | JWT sahteciliği | Varsayılan `change-me` secret | Uygulama güvenli secret olmadan başlamamalı | Güvensiz varsayılan var | Kritik |
| SEC-004 | Token hırsızlığı | XSS sonrası localStorage okuma | HttpOnly/SameSite cookie veya güçlü CSP | Token localStorage'da | Yüksek |
| SEC-005 | Brute force | Ardışık login denemeleri | Rate limit/lockout/audit | Kontrol görünmüyor | Yüksek |
| SEC-006 | Rol yükseltme | Analyst JWT ile admin | 403 | **Geçti** | Kritik |
| SEC-007 | Hassas debug yüzeyi | `/docs`, OpenAPI ve hata çıktıları | Ortama göre kapalı/sınırlı | Ek bilgi gerekli | Orta |

XSS, SQL injection, CSRF ve dosya yükleme için dinamik DAST uygulanmadı. SQLAlchemy/Pydantic kullanımı riski azaltır ancak penetrasyon testi yerine geçmez.

## 14. Performans ve Stabilite Testleri

| ID | Senaryo | Beklenen | Durum/Risk | Öncelik |
| --- | --- | --- | --- | --- |
| PERF-001 | Production build | Başarılı optimizasyon | **Geçti**, ana shared JS 102 kB | Orta |
| PERF-002 | İlçe detay bundle | Makul ilk yük | 224 kB; ölçüm ve bütçe önerilir | Orta |
| PERF-003 | 957 geometri render | Akıcı pan/zoom | Manuel profil gerekli | Yüksek |
| PERF-004 | 100 eşzamanlı arama | SLA içinde, hata oranı düşük | Yük testi yapılmadı | Yüksek |
| PERF-005 | Hızlı enerji toggle | Eski istek sonucu yeni state'i ezmez | Manuel/otomasyon gerekli | Yüksek |

## 15. API Testleri

| ID | Endpoint | Durum | Beklenen status | Gerçek | Öncelik |
| --- | --- | --- | --- | --- | --- |
| API-001 | `POST /auth/login` | Geçerli | 200 | 200 | Kritik |
| API-002 | `POST /auth/login` | Hatalı parola | 401 | 401 | Yüksek |
| API-003 | `GET /districts/search` | Ankara, limit 3 | 200 | 200/3 kayıt | Yüksek |
| API-004 | `GET /districts/search` | Boş q | 422 | 422 | Orta |
| API-005 | `GET /admin/dataset/active` | Analyst token | 403 | 403 | Kritik |
| API-006 | `GET /projects` | Token yok | 401 | 200 | Kritik |

Öneri: OpenAPI contract testi, Schemathesis/Dredd benzeri negatif üretim, Postman/Newman smoke koleksiyonu, 401/403 standardı ve correlation-id sözleşmesi.

## 16. Veri Doğruluğu ve Veritabanı Kontrolleri

| ID | Kontrol | Beklenen | Durum | Öncelik |
| --- | --- | --- | --- | --- |
| DATA-001 | Alembic repository tabloları | Temiz DB'de oluşur | Otomasyon geçti | Yüksek |
| DATA-002 | Skor golden/pipeline testleri | Deterministik sonuç | ML 5/5 geçti | Kritik |
| DATA-003 | Proje owner izolasyonu | Başkası okuyamaz | Test mevcut ve geçti; header spoof riski var | Kritik |
| DATA-004 | 957 ilçe ve aylık kayıt bütünlüğü | Eksik/duplicate yok | Hazırlık endpointi ve DB sorgusuyla ayrıca doğrulanmalı | Yüksek |
| DATA-005 | Yerelleştirme | Tarih/sayı/ondalık Türkçe tutarlı | Manuel gerekli | Orta |

## 17. Erişilebilirlik Testleri

| ID | Kontrol | Beklenen | Durum | Öncelik |
| --- | --- | --- | --- | --- |
| ACC-001 | Klavye gezintisi | Tüm aksiyonlar erişilebilir | Manuel gerekli | Yüksek |
| ACC-002 | Kontrast | WCAG AA | Manuel/axe gerekli | Yüksek |
| ACC-003 | Ekran okuyucu | Başlık, landmark ve canlı mesajlar doğru | `lang=tr`, nav/section label var; hata live region eksik | Orta |
| ACC-004 | Focus state | Her kontrolde görünür | Manuel gerekli | Yüksek |
| ACC-005 | Harita alternatifi | Klavye ve tablo alternatifi | Sıralama var; ilçe seçiminin eşdeğeri doğrulanmalı | Yüksek |

## 18. Hata Yönetimi ve Sistem Tepkileri

| ID | Hata | Beklenen tepki | Kullanıcı mesajı | Öncelik |
| --- | --- | --- | --- | --- |
| ERR-001 | Bağlantı kesildi | Retry ve son güvenli state | “Bağlantı kurulamadı, tekrar deneyin” | Yüksek |
| ERR-002 | API 5xx | Kontrollü empty/error state | Teknik stack göstermeyen mesaj | Yüksek |
| ERR-003 | Session expired | Token temizle, login'e yönlendir | “Oturumunuz sona erdi” | Kritik |
| ERR-004 | 403 | Ekranı/aksiyonu kapat | “Bu işlem için yetkiniz yok” | Yüksek |
| ERR-005 | Frontend dev artifact çakışması | Temiz build/start prosedürü | Operasyon logu; son kullanıcı 500 görmemeli | Orta |

## 19. Regression Test Önerileri

| ID | Alan | Neden | Öncelik |
| --- | --- | --- | --- |
| REG-001 | Auth principal ve tüm korumalı endpointler | SEC-001/002 düzeltmesi geniş etki yapar | Kritik |
| REG-002 | Proje/senaryo CRUD ve IDOR | Sahiplik/veri kaybı riski | Kritik |
| REG-003 | Admin/ML RBAC | Model/veri yayınlama riski | Kritik |
| REG-004 | Skor/SHAP/sıralama | Karar verisi doğruluğu | Kritik |
| REG-005 | Harita–toggle–detay | Ana kullanıcı akışı | Yüksek |

## 20. Smoke ve Sanity Test Önerileri

| Tür | Kritik kontroller | Beklenen |
| --- | --- | --- |
| Smoke | `/healthz`, `/readyz`, ana sayfa, login, arama, harita, ranking | 2xx; kritik içerik görünür |
| Sanity | Değişen auth sonrası 401/403, rol menüsü, proje CRUD, rapor | Yetki ve veri izolasyonu korunur |

## 21. Potansiyel Bug Raporları

### BUG-001 — Tokensız kullanıcı proje API'sine erişebiliyor

- **Öncelik/Şiddet:** Kritik / Kritik
- **Modül/Rol/Ortam:** Backend Auth + Projects / Anonim / Local mevcut çalışma ağacı
- **Adımlar:** Authorization olmadan `GET /api/v1/projects` çağır.
- **Beklenen:** 401 Unauthorized.
- **Gerçek:** 200 ve anonim kullanıcıya ait boş liste.
- **Etki:** Anonim kullanıcı kayıt oluşturabilir; kullanıcı sınırı kimlik doğrulama yerine `anon` değerine dayanır.
- **Tekrar:** Her zaman.
- **Kanıt:** Gerçek HTTP testi; `current_user()` anonim principal'ı kabul ediyor.
- **Çözüm:** `current_user` geçerli kimlik yoksa 401 üretmeli; public endpointler ayrı bağımlılık kullanmalı.

### BUG-002 — `X-User-Id` ile kullanıcı kimliği taklit edilebiliyor

- **Öncelik/Şiddet:** Kritik / Kritik
- **Modül:** `backend/app/core/auth.py`
- **Adımlar:** Kurban kullanıcı adını `X-User-Id` başlığına koyarak proje endpointini çağır.
- **Beklenen:** İstemci başlığı kimlik doğrulama sağlamamalı.
- **Olası gerçek:** Sunucu başlığı analyst principal olarak kabul eder; kurbanın kayıtlarına erişim sağlanabilir.
- **Kanıt:** Kaynak kod doğrulaması; saldırı üretim verisine karşı çalıştırılmadı.
- **Çözüm:** Demo header desteğini tamamen kaldır veya yalnız test fixture/app flag altında ve loopback'te etkinleştir.

### BUG-003 — Varsayılan JWT secret ile token üretilebiliyor

- **Öncelik/Şiddet:** Kritik / Kritik
- **Modül:** Configuration/JWT
- **Ön koşul:** Ortam secret vermeden başlatılmış.
- **Beklenen:** Uygulama güvenli secret yoksa başlamamalı.
- **Gerçek/Olası:** `app_secret_key="change-me"`; saldırgan admin claim'li token imzalayabilir.
- **Çözüm:** Development dışı ortamda minimum entropi kontrolü ve fail-fast; secret manager kullanımı; mevcut tokenları invalidate et.

### BUG-004 — Süresi dolan token istemci oturumunu temizlemiyor

- **Öncelik/Şiddet:** Yüksek / Orta
- **Modül:** Frontend API/session
- **Beklenen:** 401'de merkezi logout ve yeniden giriş akışı.
- **Olası gerçek:** `parseError` yalnız hata döndürüyor; localStorage ve role UI kalıyor.
- **Etki:** Kullanıcı giriş yapmış görünürken tüm korumalı işlemler başarısız olur.
- **Çözüm:** Merkezi fetch wrapper'da 401 yönetimi, session temizleme ve dönüş URL'li login.

### BUG-005 — Login brute-force koruması görünmüyor

- **Öncelik/Şiddet:** Yüksek / Yüksek
- **Modül:** Auth API
- **Beklenen:** IP/kullanıcı bazlı rate limit, audit ve geçici gecikme/lockout.
- **Gözlem:** Endpoint doğrudan parola doğruluyor; limiter/lockout bulunmadı.
- **Çözüm:** Proxy ve uygulama katmanında limit; başarısız deneme metriği ve alarmı.

### BUG-006 — Build ve dev sunucusunun aynı `.next` çıktısını kullanması HTTP 500 üretti

- **Öncelik/Şiddet:** Orta / Yüksek (geliştirme/CI kararlılığı)
- **Adımlar:** Dev sunucu açıkken/çıktısı varken production build çalıştır; ana sayfayı dev sunucudan çağır.
- **Gerçek:** 500, `__webpack_modules__[moduleId] is not a function`.
- **Çözüm:** Build ve dev süreçlerini paralel aynı çalışma dizininde çalıştırma; CI'da temiz çalışma alanı; ayrı `distDir` veya süreç kilidi.

## 22. Risk Analizi

| Alan | Açıklama | Etki | Olasılık | Öncelik | Öneri |
| --- | --- | --- | --- | --- | --- |
| Fonksiyonel | Tarayıcı E2E kapsamı yok | Yüksek | Orta | Yüksek | Playwright E2E ekle |
| UI/UX | Responsive/harita manuel doğrulanmadı | Orta | Orta | Orta | Cihaz matrisiyle test |
| Güvenlik | Anon principal, spoof header, default JWT secret | Kritik | Yüksek | Kritik | Yayından önce kapat |
| Performans | Harita ve büyük veri yük testi yok | Yüksek | Orta | Yüksek | k6 + browser profiling |
| Veri | Pipeline testleri iyi, production bütünlük kanıtı eksik | Yüksek | Düşük-Orta | Yüksek | Ready/audit ve checksum |
| Erişilebilirlik | Harita/odak/canlı hata test edilmedi | Orta | Yüksek | Yüksek | axe + manuel SR testi |

## 23. Test Otomasyonu Önerileri

| Alan | Uygun | Tür | Açıklama |
| --- | --- | --- | --- |
| Auth/RBAC | Evet | API + integration | Her route için anonim/analyst/developer/admin matrisi |
| Proje sahipliği | Evet | API + DB | IDOR, spoof header, çift kayıt, rollback |
| Ana kullanıcı akışı | Evet | UI/E2E | Login, arama, enerji toggle, ilçe detay, proje, rapor |
| Skor/ML | Evet | Unit/golden | Mevcut golden suite genişletilmeli |
| Görsel kalite | Kısmen | Visual regression + manuel | Masaüstü/tablet/mobil snapshot; harita manuel keşif |
| Performans | Evet | k6/Lighthouse | Search/ranking/geojson ve Web Vitals bütçesi |

Kritik regression suite her PR'da backend 32, ML 5, lint, type-check, build ve auth matrisi çalıştırmalıdır. Test verisinde en az iki kullanıcı, üç rol, sınır ilçeler ve bozuk/eksik model artefaktı bulunmalıdır.

## 24. Önceliklendirilmiş Test Checklist

| Sıra | Test/Kontrol | Öncelik | Neden |
| --- | --- | --- | --- |
| 1 | Anonim ve `X-User-Id` erişimini kapat/doğrula | Kritik | Hesap/veri izolasyonu |
| 2 | Production JWT secret fail-fast testi | Kritik | Admin token sahteciliği |
| 3 | Tüm endpointlerde RBAC matrisi | Kritik | Model/veri yayınlama güvenliği |
| 4 | Login–arama–detay–proje–rapor E2E | Yüksek | Ana kullanıcı değeri |
| 5 | Session expiry ve bağlantı hatası | Yüksek | Hata toleransı |
| 6 | Mobil/klavye/harita erişilebilirliği | Yüksek | Kullanılabilirlik ve WCAG |
| 7 | 957 ilçe veri bütünlüğü ve skor golden | Yüksek | Karar doğruluğu |

## 25. Genel Kalite Değerlendirmesi

- **Fonksiyonel kalite:** Otomasyon ve build güçlü; 37 test geçti.
- **Kullanılabilirlik:** Temel yapı anlaşılır; gerçek tarayıcı doğrulaması eksik.
- **Görsel kalite:** Sonuç verilemez; manuel doğrulama gerekli.
- **Hata toleransı:** API validasyonu mevcut; session expiry ve global hata UX'i eksik.
- **Güvenlik:** Production için uygun değil; üç kritik auth/JWT riski var.
- **Performans:** Build makul; yük ve harita profil testi yok.
- **Erişilebilirlik:** Bazı semantik etiketler mevcut; tam WCAG doğrulaması yok.
- **Test edilebilirlik:** Backend/ML iyi; frontend E2E/component testleri eksik.
- **Genel risk:** **Yüksek**.

**Yayın Durumu: Uygun değil**

**Gerekçe:** Anonim proje erişimi, istemci başlığıyla kimlik taklidi ve güvenli olmayan varsayılan JWT secret yayın engelidir.  
**Kritik engeller:** BUG-001, BUG-002, BUG-003.  
**Yayından önce:** Auth düzeltmeleri, tüm-route RBAC matrisi, production secret doğrulaması, tarayıcı E2E, mobil/erişilebilirlik smoke.  
**Yayından sonra:** 401/403/5xx, başarısız login, p95 API süreleri, rapor hataları, veri/model sürüm değişimleri izlenmelidir.

## 26. Sonuç ve Öneriler

En güçlü alan, backend/ML otomasyonları ile başarılı lint–type–production build hattıdır. En riskli alan kimlik doğrulamadır: korumalı proje işlemleri gerçekte kimlik doğrulaması gerektirmiyor; demo `X-User-Id` başlığı kimlik taklidine izin veriyor; JWT varsayılan secret ile başlayabiliyor.

- **Ürün ekibi:** Demo ve production modlarını net ayırmalı; desteklenen platformları ve anonim erişim politikasını kabul kriterine çevirmeli.
- **Geliştirici ekibi:** Auth bağımlılığını fail-closed yapmalı, demo header'ını kaldırmalı, secret validation ve merkezi 401 yönetimi eklemeli.
- **QA ekibi:** RBAC route matrisi, iki kullanıcılı IDOR suite, frontend E2E, axe ve k6 testlerini CI'a eklemeli.
- **Eksik bilgi:** Production topolojisi, secret yönetimi, CSP/WAF, SLA, cihaz/tarayıcı matrisi ve veri toleransları.
- **Sonraki adım:** Kritik güvenlik düzeltmelerinden sonra tam regression ve gerçek tarayıcıda masaüstü/tablet/mobil kabul testi.
