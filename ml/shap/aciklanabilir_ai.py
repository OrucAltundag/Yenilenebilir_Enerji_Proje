import pandas as pd
import xgboost as xgb
import shap
import matplotlib.pyplot as plt
import pickle
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

print("1. Veriler ve GES Modeli Yükleniyor...")
csv_path = os.path.join(script_dir, "XGBoost_Egitim_Veriseti_Guncel.csv")
df = pd.read_csv(csv_path)
# X (Girdi) verisini hazırlıyoruz
X = df.drop(columns=['tarih', 'il', 'ilce', 'GES_YATIRIM_SKORU', 'RES_YATIRIM_SKORU'])

model_ges = xgb.XGBRegressor()
model_ges.load_model(os.path.join(script_dir, "Yapay_Zeka_GES_Modeli.json"))

print("\n2. SHAP Değerleri Hazırlanıyor...")
explainer = shap.Explainer(model_ges, X)

# --- ZAMAN TASARRUFU: SHAP DEĞERLERİNİ KAYDETME/YÜKLEME ---
kayit_dosyasi = os.path.join(script_dir, "shap_degerleri.pkl")

if os.path.exists(kayit_dosyasi):
    print("Daha önceden hesaplanmış SHAP değerleri bulundu! Hızlıca yükleniyor...")
    with open(kayit_dosyasi, "rb") as f:
        shap_values = pickle.load(f)
else:
    print("SHAP değerleri sıfırdan hesaplanıyor (Bu işlem veri büyüklüğüne göre sürebilir)...")
    shap_values = explainer(X)
    print("Hesaplama bitti! Gelecekte beklememek için harddiske kaydediliyor...")
    with open(kayit_dosyasi, "wb") as f:
        pickle.dump(shap_values, f)

print("\n--- GELİŞTİRME 1: BAĞIMLILIK (DEPENDENCE) GRAFİĞİ ---")
# Matplotlib figürümüzü önceden kontrollü bir şekilde oluşturuyoruz
fig, ax = plt.subplots(figsize=(10, 6))

# Bilgisayarın kilitlenmemesi için 350 bin satırın sadece ilk 5000'ini çizdiriyoruz
orneklem = 5000 

shap.plots.scatter(shap_values[:orneklem, "ALLSKY_SFC_SW_DWN"], 
                   color=shap_values[:orneklem, "tesvik_bolgesi"], 
                   ax=ax, 
                   show=False)

plt.title("Güneş Işınımı ve Teşvik Bölgesi Etkileşimi (5000 Örneklem)", fontsize=14, fontweight='bold', pad=15)
plt.tight_layout()
plt.show()

print("\n--- GELİŞTİRME 2: EN İYİ 5 İLÇE İÇİN KARAR (DECISION) GRAFİĞİ ---")
# En iyi 5 ilçenin indekslerini bulalım
en_iyi_5_index = df['GES_YATIRIM_SKORU'].nlargest(5).index.to_list()

# Bu 5 ilçenin verilerini ve SHAP değerlerini filtreleyelim
shap_values_top5 = shap_values.values[en_iyi_5_index]
X_top5 = X.iloc[en_iyi_5_index]

plt.figure(figsize=(10, 6))
# Jürinin en çok seveceği karşılaştırmalı şelale/ağ grafiği
shap.decision_plot(explainer.expected_value, shap_values_top5, X_top5, 
                   feature_names=X.columns.tolist(),
                   title="Türkiye'nin En İyi 5 GES İlçesinin Karar Yolu Kıyaslaması")
plt.show()

print("\n--- GELİŞTİRME 3: İNTERAKTİF HTML RAPORU OLUŞTURMA ---")
# Tarayıcı kasmadan rahat açılsın diye ilk 100 ilçeyi alıyoruz
shap.initjs()
html_plot = shap.force_plot(explainer.expected_value, shap_values.values[:100], X.iloc[:100])

# HTML olarak kaydetme işlemi
html_dosya_adi = os.path.join(script_dir, "SHAP_Interaktif_Rapor.html")
with open(html_dosya_adi, "w", encoding="utf-8") as f:
    f.write(f"<html><head><script src='https://cdn.jsdelivr.net/npm/shapjs@0.41.0/shap.js'></script></head><body>")
    f.write(f"<h2 style='font-family: Arial; text-align: center; margin-top: 50px;'>TÜBİTAK Projesi - İnteraktif Yatırım Karar Analizi</h2>")
    f.write(f"<p style='font-family: Arial; text-align: center;'>Fare imlecini grafiğin üzerinde gezdirerek ilçe bazlı değişimleri görebilirsiniz.</p>")
    f.write(html_plot.html())
    f.write("</body></html>")

print(f"✅ MUHTEŞEM! '{html_dosya_adi}' dosyası klasörüne kaydedildi.")
print("Lütfen bu HTML dosyasını Google Chrome veya Edge ile çift tıklayarak açın!")