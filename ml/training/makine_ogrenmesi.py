import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import numpy as np
import os

# Betiğin bulunduğu dizini al
script_dir = os.path.dirname(os.path.abspath(__file__))

print("1. Makine Öğrenmesi Veri Seti Yükleniyor...")
df = pd.read_csv(os.path.join(script_dir, "XGBoost_Egitim_Veriseti_Final.csv"))

# 2. X (Özellikler) ve Y (Hedef) Değişkenlerinin Ayrılması
# Drop'ta hata oluşmasını engellemek için sadece var olan sütunları sil
drop_cols = ['il', 'ilce', 'YATIRIM_SKORU_Y']
# 'tarih' vardıysa ekle
if 'tarih' in df.columns:
    drop_cols.append('tarih')
X = df.drop(columns=drop_cols)
y = df['YATIRIM_SKORU_Y']

print("2. Veri Eğitim (%80) ve Test (%20) Olarak Bölünüyor...")
# random_state=42: Her çalıştırdığımızda aynı rastgelelikte bölmesi için standart bir değerdir
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

print(f"-> Eğitim verisi: {X_train.shape[0]} satır")
print(f"-> Test verisi: {X_test.shape[0]} satır")

print("\n3. XGBoost Yapay Zeka Modeli Eğitiliyor (Bu işlem 1-2 dakika sürebilir)...")
# Tahmin edeceğimiz şey 0-100 arası sürekli bir puan olduğu için XGBRegressor kullanıyoruz
model = xgb.XGBRegressor(
    objective='reg:squarederror', 
    n_estimators=150,      # Ağaç sayısı
    learning_rate=0.1,     # Öğrenme hızı
    max_depth=7,           # Ağaç derinliği
    random_state=42,
    n_jobs=-1              # Bilgisayarın tüm işlemci çekirdeklerini kullan (Hızlandırır)
)

model.fit(X_train, y_train)

print("4. Test Verisi Üzerinde Sınav (Tahminler) Yapılıyor...")
y_pred = model.predict(X_test)

print("\n=========================================")
print("     MODEL BAŞARI METRİKLERİ (KARNE)     ")
print("=========================================")
# Hata metrikleri ve R-Kare değeri hesaplanıyor
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print(f"Ortalama Mutlak Hata (MAE)    : {mae:.2f} Puan")
print(f"Kök Ortalama Kare Hata (RMSE) : {rmse:.2f} Puan")
print(f"Model Açıklayıcılığı (R²)     : %{r2*100:.2f}")

# Modelin kalıcı olarak kaydedilmesi
model_path = os.path.join(script_dir, "Yenilenebilir_Enerji_XGBoost_Modeli.json")
model.save_model(model_path)
print(f"\n-> Model '{os.path.basename(model_path)}' adyyla kaydedildi!")

print("\n5. Model İçin En Önemli Veriler Çizdiriliyor...")
# Hangi verinin yatırım kararına daha çok etki ettiğini grafik olarak görelim
plt.figure(figsize=(10, 6))
xgb.plot_importance(model, max_num_features=10, height=0.5, title="Yatırım Skorunu Etkileyen En Önemli 10 Faktör")
plt.tight_layout()
# Grafiği dosya olarak kaydet
graph_path = os.path.join(script_dir, "onem_graigi.png")
plt.savefig(graph_path, dpi=300, bbox_inches='tight')
print(f"-> Grafik '{os.path.basename(graph_path)}' adıyla kaydedildi!")
# plt.show() # Eğer görmek istersen cmd açıp çalıştır