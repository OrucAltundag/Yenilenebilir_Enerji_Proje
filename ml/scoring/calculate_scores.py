import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

script_dir = os.path.dirname(os.path.abspath(__file__))
print("1. Bağımsız Değişkenler (X) Yükleniyor...")
# Önceden hazırladığımız saf X verisetini okuyoruz
input_csv = os.path.join(script_dir, "ML_Egitime_Hazir_X_Veriseti.csv")
df = pd.read_csv(input_csv)

# 2. Teşvik Bölgeleri (Öncekiyle aynı)
tesvik_bolgeleri = {
    'İSTANBUL': 1, 'ANKARA': 1, 'İZMİR': 1, 'BURSA': 1, 'ANTALYA': 1, 'ESKİŞEHİR': 1, 'KOCAELİ': 1, 'MUĞLA': 1,
    'ADANA': 2, 'AYDIN': 2, 'BOLU': 2, 'ÇANAKKALE': 2, 'DENİZLİ': 2, 'EDİRNE': 2, 'ISPARTA': 2, 'KAYSERİ': 2, 'KIRKLARELİ': 2, 'KONYA': 2, 'SAKARYA': 2, 'TEKİRDAĞ': 2, 'YALOVA': 2,
    'BALIKESİR': 3, 'BİLECİK': 3, 'BURDUR': 3, 'GAZİANTEP': 3, 'KARABÜK': 3, 'KARAMAN': 3, 'MANİSA': 3, 'MERSİN': 3, 'SAMSUN': 3, 'TRABZON': 3, 'UŞAK': 3, 'ZONGULDAK': 3,
    'AMASYA': 4, 'ARTVİN': 4, 'BARTIN': 4, 'ÇORUM': 4, 'DÜZCE': 4, 'ELAZIĞ': 4, 'ERZİNCAN': 4, 'HATAY': 4, 'KASTAMONU': 4, 'KIRIKKALE': 4, 'KIRŞEHİR': 4, 'KÜTAHYA': 4, 'MALATYA': 4, 'NEVŞEHİR': 4, 'RİZE': 4, 'SİVAS': 4,
    'ADIYAMAN': 5, 'AKSARAY': 5, 'BAYBURT': 5, 'ÇANKIRI': 5, 'ERZURUM': 5, 'GİRESUN': 5, 'GÜMÜŞHANE': 5, 'KAHRAMANMARAŞ': 5, 'KİLİS': 5, 'NİĞDE': 5, 'ORDU': 5, 'OSMANİYE': 5, 'SİNOP': 5, 'TOKAT': 5, 'TUNCELİ': 5, 'YOZGAT': 5,
    'AĞRI': 6, 'ARDAHAN': 6, 'BATMAN': 6, 'BİNGÖL': 6, 'BİTLİS': 6, 'DİYARBAKIR': 6, 'HAKKARİ': 6, 'IĞDIR': 6, 'KARS': 6, 'MARDİN': 6, 'MUŞ': 6, 'SİİRT': 6, 'ŞANLIURFA': 6, 'ŞIRNAK': 6, 'VAN': 6
}

df['il'] = df['il'].str.strip().str.upper()
df['tesvik_bolgesi'] = df['il'].map(tesvik_bolgeleri).fillna(3) 

print("3. Veriler Normalize Ediliyor...")
scaler = MinMaxScaler()
norm_cols = ['ALLSKY_SFC_SW_DWN', 'WS10M', 'arazi_egimi_yuzde', 'tesvik_bolgesi']
df['arazi_egimi_yuzde'] = df['arazi_egimi_yuzde'].fillna(df['arazi_egimi_yuzde'].mean())
df_norm = pd.DataFrame(scaler.fit_transform(df[norm_cols]), columns=norm_cols)

print("4. GES ve RES İçin AYRI AYRI Skolar Hesaplanıyor...")

# --- GES (Güneş) FORMÜLÜ ---
# %60 Güneş, %30 Teşvik, -%10 Eğim Ceza Puanı (Rüzgarı formülden tamamen çıkardık!)
ges_skor = (df_norm['ALLSKY_SFC_SW_DWN'] * 60) + (df_norm['tesvik_bolgesi'] * 30) - (df_norm['arazi_egimi_yuzde'] * 10)
df['GES_YATIRIM_SKORU'] = ((ges_skor - ges_skor.min()) / (ges_skor.max() - ges_skor.min())) * 100
df['GES_YATIRIM_SKORU'] = df['GES_YATIRIM_SKORU'].round(2)

# --- RES (Rüzgar) FORMÜLÜ ---
# %60 Rüzgar, %30 Teşvik, -%10 Eğim Ceza Puanı (Güneşi formülden tamamen çıkardık!)
res_skor = (df_norm['WS10M'] * 60) + (df_norm['tesvik_bolgesi'] * 30) - (df_norm['arazi_egimi_yuzde'] * 10)
df['RES_YATIRIM_SKORU'] = ((res_skor - res_skor.min()) / (res_skor.max() - res_skor.min())) * 100
df['RES_YATIRIM_SKORU'] = df['RES_YATIRIM_SKORU'].round(2)

print("5. İki Yeni Skorla Final Dosyası Kaydediliyor...")
final_dosya = os.path.join(script_dir, "XGBoost_Egitim_Veriseti_Guncel.csv")
df.to_csv(final_dosya, index=False, encoding='utf-8-sig')

print(f"\nTEBRİKLER! Dosya '{final_dosya}' adıyla oluşturuldu.")
print("\nYeni Mantıktaki GES ve RES Farklarına Bir Bakış (İlk 5 Satır):")
print(df[['il', 'ilce', 'ALLSKY_SFC_SW_DWN', 'WS10M', 'GES_YATIRIM_SKORU', 'RES_YATIRIM_SKORU']].head())