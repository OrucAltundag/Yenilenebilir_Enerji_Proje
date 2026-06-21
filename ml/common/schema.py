"""Veri seti ve model için tek doğruluk kaynağı (single source of truth) şema sabitleri.

Gerçek veri seti (XGBoost_Egitim_Veriseti_Guncel.csv) ve eğitilmiş model
JSON dosyalarındaki feature_names ile birebir uyumludur.
"""

from __future__ import annotations

# Kimlik / metin sütunları (modele verilmez)
ID_COLUMNS: tuple[str, ...] = ("tarih", "il", "ilce")

# Hedef skor sütunları
TARGET_COLUMNS: tuple[str, ...] = ("GES_YATIRIM_SKORU", "RES_YATIRIM_SKORU")

# Arazi tipi one-hot sütunları (CORINE tabanlı baskın yüzey sınıfı)
LAND_ONE_HOT: tuple[str, ...] = (
    "yuzey_Orman_ve_Doğa",
    "yuzey_Su_Yüzeyi",
    "yuzey_Sulak_Alan",
    "yuzey_Tarım_Arazisi",
    "yuzey_Şehir_Yerleşimi",
)

# Modelin beklediği 12 özellik — SIRA ÖNEMLİDİR (model feature_names ile aynı)
FEATURE_ORDER: tuple[str, ...] = (
    "T2M",
    "RH2M",
    "WS10M",
    "ALLSKY_SFC_SW_DWN",
    "arazi_egimi_yuzde",
    "yuzey_alani_km2",
    *LAND_ONE_HOT,
    "tesvik_bolgesi",
)

# Deterministik skor formülünde normalize edilen sütunlar (calculate_scores.py ile aynı)
SCORE_NORM_COLUMNS: tuple[str, ...] = (
    "ALLSKY_SFC_SW_DWN",
    "WS10M",
    "arazi_egimi_yuzde",
    "tesvik_bolgesi",
)

# Skor formülü ağırlıkları (2026-06-21 revizyonu: üretim potansiyeli baskın,
# teşvik bölgesi etkisi minimalize edildi).
# Eski: %60 üretim, %30 teşvik, -%10 eğim
# Yeni: %80 üretim, %10 teşvik, -%10 eğim
WEIGHT_PRODUCTION = 80.0
WEIGHT_INCENTIVE = 10.0
WEIGHT_SLOPE_PENALTY = 10.0

# İl bazlı teşvik bölgesi (1 = en gelişmiş, 6 = en az gelişmiş)
TESVIK_BOLGELERI: dict[str, int] = {
    "İSTANBUL": 1, "ANKARA": 1, "İZMİR": 1, "BURSA": 1, "ANTALYA": 1,
    "ESKİŞEHİR": 1, "KOCAELİ": 1, "MUĞLA": 1,
    "ADANA": 2, "AYDIN": 2, "BOLU": 2, "ÇANAKKALE": 2, "DENİZLİ": 2,
    "EDİRNE": 2, "ISPARTA": 2, "KAYSERİ": 2, "KIRKLARELİ": 2, "KONYA": 2,
    "SAKARYA": 2, "TEKİRDAĞ": 2, "YALOVA": 2,
    "BALIKESİR": 3, "BİLECİK": 3, "BURDUR": 3, "GAZİANTEP": 3, "KARABÜK": 3,
    "KARAMAN": 3, "MANİSA": 3, "MERSİN": 3, "SAMSUN": 3, "TRABZON": 3,
    "UŞAK": 3, "ZONGULDAK": 3,
    "AMASYA": 4, "ARTVİN": 4, "BARTIN": 4, "ÇORUM": 4, "DÜZCE": 4,
    "ELAZIĞ": 4, "ERZİNCAN": 4, "HATAY": 4, "KASTAMONU": 4, "KIRIKKALE": 4,
    "KIRŞEHİR": 4, "KÜTAHYA": 4, "MALATYA": 4, "NEVŞEHİR": 4, "RİZE": 4,
    "SİVAS": 4,
    "ADIYAMAN": 5, "AKSARAY": 5, "BAYBURT": 5, "ÇANKIRI": 5, "ERZURUM": 5,
    "GİRESUN": 5, "GÜMÜŞHANE": 5, "KAHRAMANMARAŞ": 5, "KİLİS": 5, "NİĞDE": 5,
    "ORDU": 5, "OSMANİYE": 5, "SİNOP": 5, "TOKAT": 5, "TUNCELİ": 5, "YOZGAT": 5,
    "AĞRI": 6, "ARDAHAN": 6, "BATMAN": 6, "BİNGÖL": 6, "BİTLİS": 6,
    "DİYARBAKIR": 6, "HAKKARİ": 6, "IĞDIR": 6, "KARS": 6, "MARDİN": 6,
    "MUŞ": 6, "SİİRT": 6, "ŞANLIURFA": 6, "ŞIRNAK": 6, "VAN": 6,
}

TESVIK_DEFAULT = 3
