import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import MinMaxScaler

# Betiğin bulunduğu dizini al
script_dir = os.path.dirname(os.path.abspath(__file__))

print("1. Bağımsız Değişkenler (X) Veri Seti Yükleniyor...")
df = pd.read_csv(os.path.join(script_dir, "ML_Egitime_Hazir_X_Veriseti.csv"))

# 2. T.C. Sanayi Bakanlığı İl Teşvik Bölgeleri (1'den 6'ya kadar)
# 6. Bölge en yüksek devlet desteğini alır (Vergi indirimi, SGK vb.)
tesvik_bolgeleri = {
    'İSTANBUL': 1, 'ANKARA': 1, 'İZMİR': 1, 'BURSA': 1, 'ANTALYA': 1, 'ESKİŞEHİR': 1, 'KOCAELİ': 1, 'MUĞLA': 1,
    'ADANA': 2, 'AYDIN': 2, 'BOLU': 2, 'ÇANAKKALE': 2, 'DENİZLİ': 2, 'EDİRNE': 2, 'ISPARTA': 2, 'KAYSERİ': 2, 'KIRKLARELİ': 2, 'KONYA': 2, 'SAKARYA': 2, 'TEKİRDAĞ': 2, 'YALOVA': 2,
    'BALIKESİR': 3, 'BİLECİK': 3, 'BURDUR': 3, 'GAZİANTEP': 3, 'KARABÜK': 3, 'KARAMAN': 3, 'MANİSA': 3, 'MERSİN': 3, 'SAMSUN': 3, 'TRABZON': 3, 'UŞAK': 3, 'ZONGULDAK': 3,
    'AMASYA': 4, 'ARTVİN': 4, 'BARTIN': 4, 'ÇORUM': 4, 'DÜZCE': 4, 'ELAZIĞ': 4, 'ERZİNCAN': 4, 'HATAY': 4, 'KASTAMONU': 4, 'KIRIKKALE': 4, 'KIRŞEHİR': 4, 'KÜTAHYA': 4, 'MALATYA': 4, 'NEVŞEHİR': 4, 'RİZE': 4, 'SİVAS': 4,
    'ADIYAMAN': 5, 'AKSARAY': 5, 'BAYBURT': 5, 'ÇANKIRI': 5, 'ERZURUM': 5, 'GİRESUN': 5, 'GÜMÜŞHANE': 5, 'KAHRAMANMARAŞ': 5, 'KİLİS': 5, 'NİĞDE': 5, 'ORDU': 5, 'OSMANİYE': 5, 'SİNOP': 5, 'TOKAT': 5, 'TUNCELİ': 5, 'YOZGAT': 5,
    'AĞRI': 6, 'ARDAHAN': 6, 'BATMAN': 6, 'BİNGÖL': 6, 'BİTLİS': 6, 'DİYARBAKIR': 6, 'HAKKARİ': 6, 'IĞDIR': 6, 'KARS': 6, 'MARDİN': 6, 'MUŞ': 6, 'SİİRT': 6, 'ŞANLIURFA': 6, 'ŞIRNAK': 6, 'VAN': 6
}

print("2. Teşvik Bölgeleri Veri Setine İşleniyor...")
# İllerin yanındaki boşlukları temizleyip büyük harfe çevirerek eşleştiriyoruz
df['il'] = df['il'].str.strip().str.upper()
df['tesvik_bolgesi'] = df['il'].map(tesvik_bolgeleri)

# Eşleşmeyen varsa (Yazım hatası vb.) ortalama bir değer olan 3'ü ata
df['tesvik_bolgesi'] = df['tesvik_bolgesi'].fillna(3) 

print("3. Veriler Formül İçin Normalize Ediliyor (0-1 Arasına Çekiliyor)...")
scaler = MinMaxScaler()

# Güneş ışınımı (ALLSKY_SFC_SW_DWN), Rüzgar hızı (WS10M), Eğim ve Teşvik değerlerini aynı birime getiriyoruz
norm_cols = ['ALLSKY_SFC_SW_DWN', 'WS10M', 'arazi_egimi_yuzde', 'tesvik_bolgesi']

# Eğim verisinde eksik (NA) varsa ortalama ile doldur
df['arazi_egimi_yuzde'] = df['arazi_egimi_yuzde'].fillna(df['arazi_egimi_yuzde'].mean())

df_norm = pd.DataFrame(scaler.fit_transform(df[norm_cols]), columns=norm_cols)

print("4. Nihai 'Yatırım Skoru' (Hedef Değişken - Y) Hesaplanıyor...")
# Formül Ağırlıkları: %40 Güneş, %30 Rüzgar, %20 Teşvik, -%10 Eğim Ceza Puanı
skor = (
    (df_norm['ALLSKY_SFC_SW_DWN'] * 40) + 
    (df_norm['WS10M'] * 30) + 
    (df_norm['tesvik_bolgesi'] * 20) - 
    (df_norm['arazi_egimi_yuzde'] * 10)
)

# Negatif skor oluşmasını engellemek için en düşük skoru 0'a çekip tekrar 0-100 arasına oturtuyoruz
skor_min = skor.min()
skor_max = skor.max()
df['YATIRIM_SKORU_Y'] = ((skor - skor_min) / (skor_max - skor_min)) * 100

# Skoru virgülden sonra 2 basamağa yuvarla
df['YATIRIM_SKORU_Y'] = df['YATIRIM_SKORU_Y'].round(2)

print("5. Tüm Hazırlıklar Tamam! Model Eğitimi İçin Final Dosyası Kaydediliyor...")
final_dosya = os.path.join(script_dir, "XGBoost_Egitim_Veriseti_Final.csv")
df.to_csv(final_dosya, index=False, encoding='utf-8-sig')

print(f"\nTEBRİKLER! 🎉 Dosya oluşturuldu: '{final_dosya}'")
print("\nOluşan Skora Bir Bakış (İlk 5 Satır):")
print(df[['il', 'ilce', 'ALLSKY_SFC_SW_DWN', 'WS10M', 'tesvik_bolgesi', 'YATIRIM_SKORU_Y']].head())