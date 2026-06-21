# Buraki Makine Öğrenmesi Eğitim Planı

## 1. Amaç ve doğru problem tanımı

İki ayrı regresyon modeli üretilecek:

- GES modeli: `GES_YATIRIM_SKORU`
- RES modeli: `RES_YATIRIM_SKORU`

Mevcut hedef skorlar gerçek yatırım sonucu değildir. Güneş/rüzgâr potansiyeli,
teşvik bölgesi ve eğimden tanımlanmış deterministik formülle üretilmiştir.
Bu nedenle XGBoost burada formülü yaklaşık öğrenen bir **surrogate model** olur.
Yüksek R², gerçek yatırım başarısının doğrulandığı anlamına gelmez. Gerçek bir
tahmin modeli için kurulu güç, kapasite faktörü, üretim, bağlantı kapasitesi,
yatırım/işletme maliyeti ve gerçekleşen proje sonucu gibi bağımsız hedefler
toplanmalıdır.

## 2. Veri sözleşmesi

Ana aday veri:
`data/processed/XGBoost_Egitim_Veriseti_Duzeltilmis.csv`

- 349.305 satır, 957 ilçe, ilçe başına 365 günlük kayıt
- 12 model özelliği: `ml/common/schema.py` içindeki `FEATURE_ORDER`
- `tesvik_bolgesi`: 1–6 arası tamsayı; 1 en düşük, 6 en yüksek bölgesel
  destek düzeyi
- Teşvik kaynağı: `data/reference/tesvik_bolgeleri.csv`
- Kimlik alanları (`tarih`, `il`, `ilce`) doğrudan modele verilmez
- Hedefler 0–100 aralığında ve iki ondalık basamaklıdır

Veri kalite kapıları:

1. Satır sayısı 349.305 olmalı.
2. İl sayısı 81, ilçe sayısı 957 olmalı.
3. Her ilçede 365 benzersiz tarih bulunmalı.
4. Eksik değer ve yinelenen `(tarih, il, ilce)` olmamalı.
5. Beş arazi sütunu yalnızca 0/1 içermeli ve satır toplamı 1 olmalı.
6. `tesvik_bolgesi` 1–6 arasında tamsayı olmalı ve her il için sabit kalmalı.
7. Skorlar 0–100 aralığında olmalı.

## 3. Veri bölme stratejisi

Mevcut `train_test_split` satırları rastgele böldüğü için aynı ilçenin farklı
günleri hem eğitimde hem testte yer alır. Bu coğrafi veri sızıntısı oluşturur.

Önerilen yapı:

- Son test: ilçelerin %20'sini tamamen ayıran `GroupShuffleSplit`, grup=`il|ilce`
- Model seçimi: eğitim bölümünde 5 katlı `GroupKFold`
- Ek sağlamlık testi: bir veya birkaç ili tamamen dışarıda bırakan il-bazlı test
- Zamansal genelleme iddiası kurulacaksa 2024 gibi ayrı bir yıl dış test olmalı;
  tek yıllık veriyle böyle bir iddia kurulmaz

GES ve RES aynı satır indekslerini kullanan tek bölme manifestini paylaşmalıdır.
Manifest sürümlenmeli; böylece iki model doğrudan karşılaştırılabilir.

## 4. Özellik hazırlama

- Sayısal ağaç modelleri için ölçekleme zorunlu değildir.
- `tesvik_bolgesi` sıralı politika değişkeni olarak tamsayı tutulur.
- Günlük mevsimsellik kullanılacaksa `tarih` içinden ay/gün sinüs-kosinüs
  özellikleri türetilir; ham tarih modele verilmez.
- İl ve ilçe adları model girdisi yapılmaz. Aksi halde model konumu ezberler.
- Aynı ilçe için sabit olan eğim, alan, arazi ve teşvik alanları bölme işleminden
  önce değil, bölme manifesti üzerinden kontrol edilmelidir.

## 5. Deney sırası

1. Deterministik skor motoru: beklenen referans ve açıklanabilir baseline.
2. Basit baseline: ortalama tahmin ve doğrusal regresyon.
3. XGBoost başlangıç modeli.
4. Grup tabanlı çapraz doğrulamada sınırlı hiperparametre araması.
5. Seçilen tek yapı ile eğitim+doğrulama verisinde yeniden eğitim.
6. Dokunulmamış grup testinde bir kez nihai ölçüm.

Başlangıç XGBoost arama alanı:

- `n_estimators`: 300–1500; early stopping kullanılmalı
- `learning_rate`: 0.02–0.10
- `max_depth`: 3–8
- `min_child_weight`: 1–10
- `subsample`: 0.7–1.0
- `colsample_bytree`: 0.7–1.0
- `reg_alpha`: 0–1
- `reg_lambda`: 1–20

## 6. Değerlendirme

Her model için aşağıdakiler raporlanmalı:

- MAE (birincil metrik)
- RMSE
- R²
- Spearman sıra korelasyonu
- İlk 10/50/100 ilçe örtüşmesi
- Teşvik bölgesi ve il bazında MAE
- Tahmin-hata grafiği ve artık dağılımı
- SHAP global önem ve en az 10 yerel açıklama

Test kabul koşulları, rastgele satır bölmesinde değil grup testinde sağlanmalıdır:

- Baseline MAE'den anlamlı biçimde düşük MAE
- Eğitim/doğrulama/test farkında belirgin aşırı öğrenme olmaması
- Tahminlerin 0–100 sınırları dışında kalmaması veya açıkça kırpılması
- Özellik sırasının `FEATURE_ORDER` ile birebir eşleşmesi

## 7. Artefakt ve sürümleme

Her eğitim çalışması şu çıktıları üretmelidir:

```text
data/models/<run_id>/
  ges_model.json
  res_model.json
  metrics.json
  feature_schema.json
  split_manifest.csv
  training_config.json
  model_card.md
```

`run_id`, UTC zaman damgası ve kısa Git commit kimliğinden oluşturulmalıdır.
Üretime alınan iki model ayrıca mevcut adlara kopyalanır:

- `data/models/Yapay_Zeka_GES_Modeli.json`
- `data/models/Yapay_Zeka_RES_Modeli.json`

## 8. Uygulama sırası

1. Kalite kontrol komutunu düzeltilmiş CSV üzerinde çalıştır.
2. Grup bölme manifestini bir kez üret ve sabitle.
3. Baseline sonuçlarını kaydet.
4. XGBoost deneylerini aynı manifest ile çalıştır.
5. En iyi modeli test setinde tek sefer değerlendir.
6. SHAP özetlerini ve model kartını üret.
7. Backend şema/model uyumluluk testlerini çalıştır.
8. Yeni model ve skor özetleriyle uygulamayı yeniden oluşturup uçtan uca doğrula.

## 9. Kritik karar

Projenin iddiası “tanımlı yatırım skorunu hızlı ve açıklanabilir biçimde
yaklaştırmak” ise mevcut hedefler kullanılabilir. İddia “gerçek yatırım
başarısını tahmin etmek” ise bu hedefler yeterli değildir; model eğitiminden önce
bağımsız, gerçekleşmiş sonuç verisi toplanmalıdır.

## 10. Uygulanan eğitim hattı

Plan `ml/training/train_models.py` ile uygulanmıştır. Komut:

```bash
python ml/training/train_models.py --target-r2 0.96
```

Hat aşağıdaki işlemleri otomatik yapar:

- veri sözleşmesi ve kalite kontrolü,
- ilçe bazlı eğitim/doğrulama/test ayrımı,
- doğrulama kümesinde kademeli model seçimi ve early stopping,
- R², MAE, RMSE, sıralama ve segment metrikleri,
- model kartı, bölme manifesti, şema ve konfigürasyon üretimi,
- yalnızca her iki model test eşiğini geçerse üretim modellerini güncelleme.

İlk sızıntısız kabul koşusu (`20260620T211538Z_b1b7a50`) sonuçları:

| Model | Test R² | Test MAE | Test RMSE | İlçe Spearman |
| --- | ---: | ---: | ---: | ---: |
| GES | 0.999901 | 0.1382 | 0.1881 | 0.999859 |
| RES | 0.999527 | 0.1502 | 0.2763 | 0.999839 |

Her iki model de ilçe-gruplu, dokunulmamış test kümesinde %96 R² kabul eşiğini
geçmiştir. Sonuç hâlâ Bölüm 1 ve Bölüm 9'daki surrogate-model sınırı içinde
yorumlanmalıdır.
