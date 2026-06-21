import numpy as np
import pandas as pd

from common.schema import FEATURE_ORDER, LAND_ONE_HOT, TARGET_COLUMNS
from training.train_models import make_group_split, regression_metrics, validate_dataset


def _frame() -> pd.DataFrame:
    rows = []
    for province in ("A", "B", "C"):
        for district in range(4):
            for day in range(3):
                row = {feature: 1.0 for feature in FEATURE_ORDER}
                for feature in LAND_ONE_HOT:
                    row[feature] = 0
                row[LAND_ONE_HOT[0]] = 1
                row.update(
                    {
                        "tarih": 20230101 + day,
                        "il": province,
                        "ilce": str(district),
                        "tesvik_bolgesi": district % 6 + 1,
                        TARGET_COLUMNS[0]: 50.0,
                        TARGET_COLUMNS[1]: 40.0,
                    }
                )
                rows.append(row)
    return pd.DataFrame(rows)


def test_group_split_has_no_district_leakage():
    df = _frame()
    train, validation, test, manifest = make_group_split(
        df, seed=42, test_size=0.25, validation_size=0.25
    )
    groups = df["il"] + "|" + df["ilce"]
    assert set(groups.iloc[train]).isdisjoint(groups.iloc[validation])
    assert set(groups.iloc[train]).isdisjoint(groups.iloc[test])
    assert set(groups.iloc[validation]).isdisjoint(groups.iloc[test])
    assert len(manifest) == groups.nunique()


def test_validation_and_metrics():
    df = _frame()
    validate_dataset(df)
    metrics = regression_metrics(np.array([1.0, 2.0]), np.array([1.0, 2.0]))
    assert metrics["r2"] == 1.0
    assert metrics["mae"] == 0.0
    assert metrics["out_of_range_count"] == 0
