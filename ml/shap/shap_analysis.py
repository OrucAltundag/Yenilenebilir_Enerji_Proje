import pandas as pd
import xgboost as xgb
import shap
import matplotlib.pyplot as plt
import os

# Script'in bulunduğu dizini al
script_dir = os.path.dirname(os.path.abspath(__file__))

print("1. Veri Seti ve Eğitilmiş XGBoost Modeli Yüklünüyor...")
df = pd.read_csv(os.path.join(script_dir, "XGBoost_Egitim_Veriseti_Final.csv"))

# Sadece yapay zekanın eğitimde gördüğü özellikleri (X) seçiyoruz
X = df.drop(columns=['tarih', 'il', 'ilce', 'YATIRIM_SKORU_Y'])

# Kaydettiğimiz o %99 başarılı modeli geri çağırıyoruz
model = xgb.XGBRegressor()
model.load_model(os.path.join(script_dir, "Yenilenebilir_Enerji_XGBoost_Modeli.json"))

print("2. SHAP Açıklayıcısı (Explainer) Kuruluyor (Bu birkaç saniye sürebilir)...")
# Ağaç tabanlı modeller için en hızlı açıklayıcı olan TreeExplainer'ı kullanıyoruz
explainer = shap.Explainer(model, X)
shap_values = explainer(X)

print("3. Genel Yapay Zeka Mantığı Çizdiriliyor (Summary Plot)...")
# Grafiğin ekranda tam boyutlu ve düzgün görünmesi için bir figür oluşturuyoruz
plt.figure(figsize=(10, 6))
plt.title("Yatırım Skorunu Etkileyen Faktörlerin Yönü ve Şiddeti")
# Bu grafik her bir verinin (Güneş, Rüzgar vb.) skoru artırıp artırmadığını gösterir
shap.summary_plot(shap_values, X, show=False)
plt.tight_layout()
plt.show()

print("\n4. Tek Bir İlçe İçin Özel Yatırım Karar Raporu Çizdiriliyor (Waterfall Plot)...")
# Örnek olarak veri setindeki İLK SATIRDA bulunan ilçeyi inceliyoruz.
# (Buradaki 0 rakamını değiştirerek istediğin satırdaki ilçenin analizini görebilirsin)
ornek_index = 0
il_adi = df.iloc[ornek_index]['il']
ilce_adi = df.iloc[ornek_index]['ilce']
gercek_skor = df.iloc[ornek_index]['YATIRIM_SKORU_Y']

print(f"\n=> {il_adi} / {ilce_adi} ilçesi için karar süreci ekrana yansıtıldı.")
print(f"=> Bu ilçenin nihai yatırım skoru: {gercek_skor}")

# Şelale (Waterfall) grafiği: Modelin taban puandan başlayıp
# hangi veriyle kaç puan ekleyip/çıkardığını adım adım gösterir.
shap.plots.waterfall(shap_values[ornek_index], max_display=10)