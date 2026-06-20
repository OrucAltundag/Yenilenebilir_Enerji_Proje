import os
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))
print("1. Güncel Veri Seti Okunuyor...")
# Bir önceki adımda ürettiğimiz çift skorlu final dosyamızı açıyoruz
input_csv = os.path.join(script_dir, "XGBoost_Egitim_Veriseti_Guncel.csv")
df = pd.read_csv(input_csv)

print("\n=======================================================")
print("  🏆 GES (GÜNEŞ ENERJİSİ) İÇİN TÜRKİYE'NİN EN İYİ 5 İLÇESİ  ")
print("=======================================================")
# GES skoruna göre büyükten küçüğe sıralayıp (ascending=False) ilk 5'i alıyoruz
en_iyi_ges = df.sort_values(by='GES_YATIRIM_SKORU', ascending=False).head(10)

# Sadece jürinin ve yatırımcının görmek isteyeceği kritik sütunları ekrana yazdırıyoruz
print(en_iyi_ges[['il', 'ilce', 'ALLSKY_SFC_SW_DWN', 'tesvik_bolgesi', 'arazi_egimi_yuzde', 'GES_YATIRIM_SKORU']].to_string(index=False))


print("\n=======================================================")
print("  🌬️ RES (RÜZGAR ENERJİSİ) İÇİN TÜRKİYE'NİN EN İYİ 5 İLÇESİ  ")
print("=======================================================")
# RES skoruna göre büyükten küçüğe sıralayıp ilk 5'i alıyoruz
en_iyi_res = df.sort_values(by='RES_YATIRIM_SKORU', ascending=False).head(10)

print(en_iyi_res[['il', 'ilce', 'WS10M', 'tesvik_bolgesi', 'arazi_egimi_yuzde', 'RES_YATIRIM_SKORU']].to_string(index=False))