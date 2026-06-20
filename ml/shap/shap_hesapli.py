import pandas as pd
import xgboost as xgb
import shap
import matplotlib.pyplot as plt
import pickle
import os

# 1. Dosya Yollarını Tanımlayalım (Hata almamak için tam yol kullanabilirsin)
dosya_yolu = r"C:\Users\brkba\OneDrive\Desktop\8.YARIYIL\BİTİRME PROJESİ\metveri"
csv_adi = "XGBoost_Egitim_Veriseti_Guncel.csv"
model_adi = "Yapay_Zeka_GES_Modeli.json"
pkl_adi = "shap_degerleri.pkl"

print("1. Veriler ve Model Yükleniyor...")
df = pd.read_csv(os.path.join(dosya_yolu, csv_adi))
X = df.drop(columns=['tarih', 'il', 'ilce', 'GES_YATIRIM_SKORU', 'RES_YATIRIM_SKORU'])

model_ges = xgb.XGBRegressor()
model_ges.load_model(os.path.join(dosya_yolu, model_adi))

# 2. Kayıtlı SHAP Değerlerini Yükleyelim
print(f"2. {pkl_adi} dosyası yükleniyor (Hesaplama yapılmıyor, çok hızlı sürecek)...")
try:
    with open(os.path.join(dosya_yolu, pkl_adi), "rb") as f:
        shap_values = pickle.load(f)
    print("✅ SHAP değerleri başarıyla yüklendi!")
except FileNotFoundError:
    print(f"❌ HATA: {pkl_adi} dosyası bulunamadı. Lütfen dosyanın klasörde olduğundan emin ol.")
    exit()

# 3. Görselleştirme Hazırlığı (Explainer objesi grafikler için gerekli)
explainer = shap.Explainer(model_ges, X)

print("\n--- GRAFİK 1: BAĞIMLILIK (DEPENDENCE) ---")
fig, ax = plt.subplots(figsize=(10, 6))
# 350 bin satırı çizmek bilgisayarı dondurduğu için sadece 5000 örneklem alıyoruz
orneklem = 5000 
shap.plots.scatter(shap_values[:orneklem, "ALLSKY_SFC_SW_DWN"], 
                   color=shap_values[:orneklem, "tesvik_bolgesi"], 
                   ax=ax, 
                   show=False)
plt.title("Güneş Işınımı ve Teşvik Bölgesi Etkileşimi (5000 Örneklem)", fontsize=12, fontweight='bold')
plt.tight_layout()
plt.show()

print("\n--- GRAFİK 2: EN İYİ 5 İLÇE KARAR YOLU ---")
en_iyi_5_index = df['GES_YATIRIM_SKORU'].nlargest(5).index.to_list()
shap_values_top5 = shap_values.values[en_iyi_5_index]
X_top5 = X.iloc[en_iyi_5_index]

plt.figure(figsize=(10, 6))
shap.decision_plot(explainer.expected_value, shap_values_top5, X_top5, 
                   feature_names=X.columns.tolist(),
                   title="En İyi 5 GES İlçesinin Karar Kıyaslaması")
plt.show()

print("\n--- GRAFİK 3: İNTERAKTİF HTML RAPORU ---")
html_dosya = os.path.join(dosya_yolu, "SHAP_Interaktif_Rapor.html")

# Force plot objesini oluşturuyoruz (Sadece ilk 100 ilçe)
html_plot = shap.force_plot(explainer.expected_value, shap_values.values[:100], X.iloc[:100])

# SHAP'IN KENDİ RESMİ HTML KAYDETME FONKSİYONUNU KULLANIYORUZ
shap.save_html(html_dosya, html_plot)

print(f"✅ İşlem Tamam! HTML raporun şuraya kaydedildi: {html_dosya}")

print("\n--- GRAFİK 4: RAPOR İÇİN TEKİL ŞELALE (WATERFALL) GRAFİĞİ ---")

# Veri setimizde en yüksek GES skoruna sahip (1. olan) ilçenin satır numarasını buluyoruz
birinci_ilce_index = df['GES_YATIRIM_SKORU'].idxmax()
il_adi = df.loc[birinci_ilce_index, 'il']
ilce_adi = df.loc[birinci_ilce_index, 'ilce']

print(f"📍 Raporlanacak Şampiyon İlçe: {il_adi} - {ilce_adi}")

# Sadece o spesifik ilçe için Waterfall grafiğini çizdiriyoruz
fig, ax = plt.subplots(figsize=(8, 6))
shap.plots.waterfall(shap_values[birinci_ilce_index], show=False)
plt.title(f"{il_adi} / {ilce_adi} İlçesi Yapay Zeka Karar Raporu", pad=20, fontweight='bold')
plt.tight_layout()
plt.show()