"""Tüm veri/geometri/skor/SHAP artefaktlarını sırayla yeniden üretir.

Sıra:
    1. district_master   (canonical ilçe kimliği + alias)
    2. build_district_geojson (973 güncel sınır -> canonical district_id)
    3. fix_zero_area      (117 sıfır yüzölçümü düzeltmesi -> Temiz veri seti)
    4. data_quality       (kalite raporu)
    5. build_config       (scoring_config.json)
    6. build_summary      (district_score_summary + aylık profil)
    7. build_global_shap  (global SHAP özeti)

Çalıştırma (backend venv ile):
    python scripts/build_all.py
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEPS = [
    ("Canonical district master", "ml/pipelines/district_master.py"),
    ("İlçe sınır geometrileri", "scripts/build_district_geojson.py"),
    ("Sıfır yüzölçümü düzeltmesi", "ml/pipelines/fix_zero_area.py"),
    ("Veri kalite raporu", "ml/pipelines/data_quality.py"),
    ("Scoring config", "ml/scoring/build_config.py"),
    ("İlçe özet tablosu", "ml/scoring/build_summary.py"),
    ("Global SHAP özeti", "ml/shap/build_global_shap.py"),
]


def main() -> None:
    for i, (label, rel) in enumerate(STEPS, 1):
        print(
            f"\n{'=' * 60}\n[{i}/{len(STEPS)}] {label}\n{'=' * 60}",
            flush=True,
        )
        start = time.time()
        subprocess.run(
            [sys.executable, str(ROOT / rel)],
            cwd=ROOT,
            check=True,
        )
        print(f"... {time.time() - start:.1f}s", flush=True)
    print("\nTüm artefaktlar üretildi.", flush=True)


if __name__ == "__main__":
    main()
