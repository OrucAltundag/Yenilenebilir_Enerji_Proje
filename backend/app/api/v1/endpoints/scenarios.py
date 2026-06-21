from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.data.repository import get_repository
from app.ml.scoring_engine import ScoringConfig, score_record
from app.schemas.scenario import ScenarioRequest, ScenarioResult

router = APIRouter()

# İzin verilen senaryo girdileri ve fiziksel aralıkları
ALLOWED_OVERRIDES: dict[str, tuple[float, float]] = {
    "ALLSKY_SFC_SW_DWN": (0.0, 12.0),
    "WS10M": (0.0, 25.0),
    "arazi_egimi_yuzde": (0.0, 90.0),
    "tesvik_bolgesi": (1.0, 6.0),
}


def _full_feature_vector(row: dict) -> dict[str, float]:
    return {
        "ALLSKY_SFC_SW_DWN": row["ALLSKY_SFC_SW_DWN"],
        "WS10M": row["WS10M"],
        "arazi_egimi_yuzde": row["arazi_egimi_yuzde"],
        "tesvik_bolgesi": row["tesvik_bolgesi"],
    }


@router.post("/simulate", response_model=ScenarioResult)
def simulate(payload: ScenarioRequest):
    """Kullanıcı girdilerini değiştirerek senaryo skoru hesaplar.

    Yalnız izinli alanlar değiştirilebilir; fiziksel aralık dışı değerler reddedilir.
    Gözlem verisi değiştirilmez (simülasyon).
    """
    repo = get_repository()
    row = repo.get_summary(payload.district_id, payload.year)
    if row is None:
        raise HTTPException(status_code=404, detail="İlçe bulunamadı")

    config = ScoringConfig.load(settings.scoring_config_path)
    baseline_features = _full_feature_vector(row)
    baseline = score_record(baseline_features, config)

    scenario_features = dict(baseline_features)
    for key, value in payload.overrides.items():
        if key not in ALLOWED_OVERRIDES:
            raise HTTPException(status_code=422, detail=f"İzin verilmeyen alan: {key}")
        lo, hi = ALLOWED_OVERRIDES[key]
        if not (lo <= value <= hi):
            raise HTTPException(
                status_code=422,
                detail=f"{key} aralık dışı ({lo}–{hi}): {value}",
            )
        scenario_features[key] = value

    scenario = score_record(scenario_features, config)

    return ScenarioResult(
        district_id=payload.district_id,
        baseline_ges=baseline["ges"],
        baseline_res=baseline["res"],
        scenario_ges=scenario["ges"],
        scenario_res=scenario["res"],
        delta_ges=round(scenario["ges"] - baseline["ges"], 2),
        delta_res=round(scenario["res"] - baseline["res"], 2),
        scoring_version=config.version,
    )
