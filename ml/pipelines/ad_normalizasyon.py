import pandas as pd
import os

# Betiğin bulunduğu dizini al
script_dir = os.path.dirname(os.path.abspath(__file__))

# 1. Dosyayı okuma (İlk 5 satırdaki gereksiz açıklamaları atlıyoruz)
dosya_yolu = os.path.join(script_dir, 'il_ilce_alanlari.xlsx - Sayfa1.csv')
df = pd.read_csv(dosya_yolu, header=None, skiprows=5) 

islenmis_veri = []
guncel_il = None

print("Veriler taranıyor ve ilçeler illerine göre eşleştiriliyor...")

# 2. Satır satır dolaşarak İl ve İlçe ayrımını yapma
for index, row in df.iterrows():
    # Sütun 0 boşsa bu bir 'İL' satırıdır, doluysa 'İLÇE' satırıdır.
    sutun0 = str(row[0]).strip()
    isim = str(row[2]).strip() # İl veya İlçe adı
    alan = row[3] # Yüzölçümü (km2)
    
    # Eğer ilk sütun boşsa (nan) ve isim kısmı doluysa, yeni bir İl'e geçtik demektir
    if pd.isna(row[0]) or sutun0 == 'nan' or sutun0 == '':
        if isim != 'nan' and isim != '' and isim != 'İL / İLÇE':
            guncel_il = isim
    else:
        # Eğer ilk sütunda bir numara varsa, bu bir ilçedir. 
        # Hemen onu o an hafızada tuttuğumuz İl'e kaydediyoruz.
        if guncel_il and isim != 'nan' and isim != '':
            islenmis_veri.append({
                'il': guncel_il, 
                'ilce': isim, 
                'yuzey_alani_km2': alan
            })

# 3. Listeyi bir DataFrame'e çevir ve kaydet
final_df = pd.DataFrame(islenmis_veri)

kayit_adi = os.path.join(script_dir, 'ilce_yuzolcumu.csv')
final_df.to_csv(kayit_adi, index=False, encoding='utf-8-sig')

print(f"\nİşlem Başarılı! Toplam {len(final_df)} ilçe çıkarıldı.")
print(f"Tertemiz veriniz '{kayit_adi}' adıyla kaydedildi.")
print("\nÖrnek Veri (İlk 5 Satır):")
print(final_df.head(5))