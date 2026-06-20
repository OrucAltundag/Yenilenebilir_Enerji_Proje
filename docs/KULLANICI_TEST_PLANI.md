# Buraki — Kullanıcı Test Planı

## Test Ortamı

- Frontend: http://localhost:3000
- API dokümantasyonu: http://localhost:8000/docs
- Demo analyst: `analyst / analyst123`
- Demo admin: `admin / admin123`

> Sistem yatırım tavsiyesi vermez; kullanıcı testleri ön eleme, karşılaştırma,
> açıklanabilirlik ve raporlama akışlarını doğrulamak içindir.

## Senaryo 1 — Ana Sayfa ve Harita

1. http://localhost:3000 adresini aç.
2. “Sistem hazır · 957 ilçe” bilgisini kontrol et.
3. GES/RES geçişini kullan.
4. Haritada renklerin değiştiğini ve sıralama tablosunun güncellendiğini doğrula.

Başarı kriteri: Harita, sıralama ve global model açıklaması hatasız görünür.

## Senaryo 2 — İlçe Arama ve Detay

1. Arama alanına `ankara` yaz.
2. Bir ilçe sonucuna tıkla.
3. İlçe detayında skor, ulusal sıra, aylık profil, SHAP açıklaması ve girdileri kontrol et.

Başarı kriteri: İlçe detay sayfası yüklenir ve grafik/SHAP bölümleri görünür.

## Senaryo 3 — Senaryo Simülasyonu

1. İlçe detayında “Senaryo simülasyonu” alanında güneş ışınımı veya rüzgâr hızını değiştir.
2. “Simüle et” düğmesine bas.
3. Yeni skor ve delta değerini kontrol et.

Başarı kriteri: Skor farkı hesaplanır, sayfa hata vermez.

## Senaryo 4 — PDF Rapor

1. İlçe detayında “PDF raporu indir” düğmesine bas.
2. PDF dosyasının indirildiğini doğrula.

Başarı kriteri: PDF indirme başlar ve API hatası görünmez.

## Senaryo 5 — Proje ve Senaryo Kaydı

1. `analyst / analyst123` ile giriş yap.
2. İlçe detayında “Proje oluştur” ve “Senaryoyu kaydet” işlemlerini yap.
3. `/projects` sayfasına git.
4. Oluşturulan proje ve senaryonun listede göründüğünü kontrol et.

Başarı kriteri: Proje ve senaryo kayıtları kullanıcıya özel şekilde listelenir.

## Senaryo 6 — Admin

1. Çıkış yap.
2. `admin / admin123` ile giriş yap.
3. `/admin` sayfasına git.
4. Aktif veri sürümünü gör.
5. “Yayınla” düğmesine bas.
6. Audit log içinde `dataset.publish` kaydını kontrol et.

Başarı kriteri: Admin işlemi tamamlanır, audit kaydı oluşur.

## Test Sırasında Not Alınacaklar

- Kullanıcı hangi ekranda duraksadı?
- Etiketler yeterince açıklayıcı mı?
- Harita ve grafik performansı kabul edilebilir mi?
- PDF raporu anlaşılır mı?
- Senaryo sonucunda delta değeri kullanıcı için anlamlı mı?
