from app.core.config import settings
from app.ml.scoring_engine import ScoringConfig, score_record
from app.services.score_service import ScoreService


def test_score_service_delegates_to_versioned_engine():
    config = ScoringConfig.load(settings.scoring_config_path)
    features = {
        "ALLSKY_SFC_SW_DWN": 5.0,
        "WS10M": 4.0,
        "arazi_egimi_yuzde": 8.0,
        "tesvik_bolgesi": 3.0,
    }
    expected = score_record(features, config)
    service = ScoreService(config)

    assert service.compute_ges(features) == expected["ges"]
    assert service.compute_res(features) == expected["res"]
