"""Model/veri şeması sabitleri (ml/common/schema.py ile uyumlu).

Backend bağımsız çalışabilsin diye özellik sırası burada da tutulur; ml tarafı
ile aynı olmalıdır.
"""

from __future__ import annotations

LAND_ONE_HOT: tuple[str, ...] = (
    "yuzey_Orman_ve_Doğa",
    "yuzey_Su_Yüzeyi",
    "yuzey_Sulak_Alan",
    "yuzey_Tarım_Arazisi",
    "yuzey_Şehir_Yerleşimi",
)

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

# 2026-06-21: teşvik etkisi minimalize edildi (eski %30 → %10), üretim %80'e çekildi.
WEIGHT_PRODUCTION = 80.0
WEIGHT_INCENTIVE = 10.0
WEIGHT_SLOPE_PENALTY = 10.0
