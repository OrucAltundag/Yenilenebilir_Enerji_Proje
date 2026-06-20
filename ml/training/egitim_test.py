import os
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

script_dir = os.path.dirname(os.path.abspath(__file__))
print("1. Makine Öğrenmesi Veri Seti Yükleniyor...")
# Çift skorlu (GES ve RES) güncel veri setimizi okuyoruz
input_csv = os.path.join(script_dir, "XGBoost_Egitim_Veriseti_Guncel.csv")
df = pd.read_csv(input_csv)

# 2. X (Özellikler) ve Y (Hedefler) Değişkenlerinin Ayrılması
# Modelin kopya çekmemesi için metinleri ve sonuçları X'ten (Girdi) çıkarıyoruz.
X = df.drop(columns=['tarih', 'il', 'ilce', 'GES_YATIRIM_SKORU', 'RES_YATIRIM_SKORU'])

# İki farklı hedefimiz (Y) var
y_ges = df['GES_YATIRIM_SKORU']
y_res = df['RES_YATIRIM_SKORU']

print("2. Veriler Eğitim (%80) ve Test (%20) Olarak Bölünüyor...")
# GES için veri bölme
X_train_g, X_test_g, y_train_g, y_test_g = train_test_split(X, y_ges, test_size=0.20, random_state=42)
# RES için veri bölme
X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(X, y_res, test_size=0.20, random_state=42)

print("\n3. XGBoost Yapay Zeka Modelleri Eğitiliyor (Bu işlem kısa sürecektir)...")
# Algoritma Ayarları (Hiperparametreler)
model_ayarlari = {
    'objective': 'reg:squarederror', 
    'n_estimators': 150,      # Ağaç sayısı
    'learning_rate': 0.1,     # Öğrenme hızı
    'max_depth': 7,           # Ağaç derinliği
    'random_state': 42,
    'n_jobs': -1              # Tüm işlemci çekirdeklerini kullan
}

# GES Modelini Kur ve Eğit
model_ges = xgb.XGBRegressor(**model_ayarlari)
model_ges.fit(X_train_g, y_train_g)

# RES Modelini Kur ve Eğit
model_res = xgb.XGBRegressor(**model_ayarlari)
model_res.fit(X_train_r, y_train_r)

print("\n4. Test Verisi Üzerinde Sınav (Tahminler) Yapılıyor...")
ges_tahminler = model_ges.predict(X_test_g)
res_tahminler = model_res.predict(X_test_r)

print("\n=========================================")
print("  ☀️ GES MODELİ BAŞARI METRİKLERİ (KARNE) ")
print("=========================================")
ges_mae = mean_absolute_error(y_test_g, ges_tahminler)
ges_r2 = r2_score(y_test_g, ges_tahminler)
print(f"Ortalama Mutlak Hata (MAE)    : {ges_mae:.2f} Puan")
print(f"Model Açıklayıcılığı (R²)     : %{ges_r2*100:.2f}")

print("\n=========================================")
print("  🌬️ RES MODELİ BAŞARI METRİKLERİ (KARNE) ")
print("=========================================")
res_mae = mean_absolute_error(y_test_r, res_tahminler)
res_r2 = r2_score(y_test_r, res_tahminler)
print(f"Ortalama Mutlak Hata (MAE)    : {res_mae:.2f} Puan")
print(f"Model Açıklayıcılığı (R²)     : %{res_r2*100:.2f}")

# 5. Modellerin Kalıcı Olarak Kaydedilmesi
ges_model_path = os.path.join(script_dir, "Yapay_Zeka_GES_Modeli.json")
res_model_path = os.path.join(script_dir, "Yapay_Zeka_RES_Modeli.json")
model_ges.save_model(ges_model_path)
model_res.save_model(res_model_path)
print(f"\n✅ Modeller '{ges_model_path}' ve '{res_model_path}' olarak kaydedildi!")