"""Sızıntısız, yeniden üretilebilir GES/RES XGBoost eğitim hattı.

Kabul ölçütü, daha önce hiç görülmemiş ilçelerden oluşan test kümesinde her iki
model için R² >= ``--target-r2`` olmasıdır. Model seçimi yalnızca doğrulama
kümesinde yapılır; test kümesi seçilen model için bir kez ölçülür.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))

from common.schema import FEATURE_ORDER, LAND_ONE_HOT, TARGET_COLUMNS  # noqa: E402

DEFAULT_INPUT = (
    ROOT / "data" / "processed" / "XGBoost_Egitim_Veriseti_Duzeltilmis.csv"
)
MODEL_DIR = ROOT / "data" / "models"
ENERGIES = {
    "ges": "GES_YATIRIM_SKORU",
    "res": "RES_YATIRIM_SKORU",
}

# Basitten daha esnek modele doğru. Bir sonraki aday yalnızca doğrulama hedefi
# sağlanmadığında denenir.
CANDIDATES: tuple[dict[str, Any], ...] = (
    {
        "name": "depth4_regularized",
        "max_depth": 4,
        "min_child_weight": 10,
        "learning_rate": 0.05,
        "subsample": 0.9,
        "colsample_bytree": 1.0,
        "reg_alpha": 0.0,
        "reg_lambda": 5.0,
        "num_boost_round": 1200,
    },
    {
        "name": "depth6_balanced",
        "max_depth": 6,
        "min_child_weight": 5,
        "learning_rate": 0.04,
        "subsample": 0.9,
        "colsample_bytree": 1.0,
        "reg_alpha": 0.0,
        "reg_lambda": 3.0,
        "num_boost_round": 1600,
    },
    {
        "name": "depth8_fine",
        "max_depth": 8,
        "min_child_weight": 2,
        "learning_rate": 0.03,
        "subsample": 0.95,
        "colsample_bytree": 1.0,
        "reg_alpha": 0.0,
        "reg_lambda": 2.0,
        "num_boost_round": 2000,
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=MODEL_DIR)
    parser.add_argument("--target-r2", type=float, default=0.96)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-size", type=float, default=0.20)
    parser.add_argument("--validation-size", type=float, default=0.125)
    parser.add_argument("--early-stopping-rounds", type=int, default=75)
    parser.add_argument("--run-id", type=str)
    parser.add_argument(
        "--no-promote",
        action="store_true",
        help="Başarılı modelleri üretim dosya adlarına kopyalama.",
    )
    return parser.parse_args()


def validate_dataset(df: pd.DataFrame) -> None:
    expected = {"tarih", "il", "ilce", *FEATURE_ORDER, *TARGET_COLUMNS}
    missing = sorted(expected.difference(df.columns))
    if missing:
        raise ValueError(f"Eksik sütunlar: {missing}")
    if df.empty:
        raise ValueError("Eğitim veri seti boş")
    if df.duplicated(["tarih", "il", "ilce"]).any():
        raise ValueError("Yinelenen tarih/il/ilçe kaydı var")
    if df[list(FEATURE_ORDER) + list(TARGET_COLUMNS)].isna().any().any():
        raise ValueError("Özellik veya hedef sütunlarında eksik değer var")
    if not df["tesvik_bolgesi"].between(1, 6).all():
        raise ValueError("tesvik_bolgesi 1–6 aralığı dışında")
    land = df[list(LAND_ONE_HOT)]
    if not land.isin([0, 1]).all().all() or not land.sum(axis=1).eq(1).all():
        raise ValueError("Arazi one-hot sütunları geçersiz")
    for target in TARGET_COLUMNS:
        if not df[target].between(0, 100).all():
            raise ValueError(f"{target} 0–100 aralığı dışında")


def make_group_split(
    df: pd.DataFrame,
    *,
    seed: int,
    test_size: float,
    validation_size: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, pd.DataFrame]:
    groups = df["il"].astype(str) + "|" + df["ilce"].astype(str)
    all_idx = np.arange(len(df))
    outer = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_val_idx, test_idx = next(outer.split(all_idx, groups=groups))

    inner_groups = groups.iloc[train_val_idx]
    inner = GroupShuffleSplit(
        n_splits=1, test_size=validation_size, random_state=seed + 1
    )
    train_rel, validation_rel = next(
        inner.split(train_val_idx, groups=inner_groups)
    )
    train_idx = train_val_idx[train_rel]
    validation_idx = train_val_idx[validation_rel]

    assignments: dict[str, str] = {}
    for split, indexes in (
        ("train", train_idx),
        ("validation", validation_idx),
        ("test", test_idx),
    ):
        for group in groups.iloc[indexes].unique():
            if group in assignments:
                raise AssertionError(f"Grup birden fazla bölmede: {group}")
            assignments[group] = split

    manifest = pd.DataFrame(
        (
            (group.split("|", 1)[0], group.split("|", 1)[1], split)
            for group, split in assignments.items()
        ),
        columns=["il", "ilce", "split"],
    ).sort_values(["split", "il", "ilce"])
    return train_idx, validation_idx, test_idx, manifest


def regression_metrics(y_true: pd.Series | np.ndarray, prediction: np.ndarray) -> dict:
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(prediction, dtype=float)
    return {
        "r2": float(r2_score(y, p)),
        "mae": float(mean_absolute_error(y, p)),
        "rmse": float(mean_squared_error(y, p) ** 0.5),
        "prediction_min": float(p.min()),
        "prediction_max": float(p.max()),
        "out_of_range_count": int(((p < 0) | (p > 100)).sum()),
    }


def rank_metrics(
    frame: pd.DataFrame, target: str, prediction: np.ndarray
) -> dict[str, Any]:
    scored = frame[["il", "ilce", target]].copy()
    scored["prediction"] = prediction
    district = scored.groupby(["il", "ilce"], as_index=False)[
        [target, "prediction"]
    ].mean()
    target_rank = district[target].rank(method="average")
    prediction_rank = district["prediction"].rank(method="average")
    spearman = float(target_rank.corr(prediction_rank))
    overlaps: dict[str, float] = {}
    for k in (10, 50, 100):
        size = min(k, len(district))
        expected = set(district.nlargest(size, target).index)
        predicted = set(district.nlargest(size, "prediction").index)
        overlaps[f"top_{k}_overlap"] = len(expected & predicted) / size
    return {"district_spearman": spearman, **overlaps}


def segmented_mae(
    frame: pd.DataFrame, target: str, prediction: np.ndarray
) -> dict[str, dict[str, float]]:
    scored = frame[["il", "tesvik_bolgesi", target]].copy()
    scored["absolute_error"] = np.abs(scored[target].to_numpy() - prediction)
    by_region = (
        scored.groupby("tesvik_bolgesi")["absolute_error"].mean().round(6)
    )
    by_province = scored.groupby("il")["absolute_error"].mean().round(6)
    return {
        "mae_by_incentive_region": {
            str(int(k)): float(v) for k, v in by_region.items()
        },
        "mae_by_province": {str(k): float(v) for k, v in by_province.items()},
    }


def train_candidate(
    X: pd.DataFrame,
    y: pd.Series,
    train_idx: np.ndarray,
    validation_idx: np.ndarray,
    candidate: dict[str, Any],
    *,
    seed: int,
    early_stopping_rounds: int,
) -> tuple[xgb.Booster, dict[str, Any]]:
    dtrain = xgb.DMatrix(
        X.iloc[train_idx], label=y.iloc[train_idx], feature_names=list(FEATURE_ORDER)
    )
    dvalidation = xgb.DMatrix(
        X.iloc[validation_idx],
        label=y.iloc[validation_idx],
        feature_names=list(FEATURE_ORDER),
    )
    params = {
        "objective": "reg:squarederror",
        "eval_metric": "rmse",
        "tree_method": "hist",
        "max_depth": candidate["max_depth"],
        "min_child_weight": candidate["min_child_weight"],
        "eta": candidate["learning_rate"],
        "subsample": candidate["subsample"],
        "colsample_bytree": candidate["colsample_bytree"],
        "alpha": candidate["reg_alpha"],
        "lambda": candidate["reg_lambda"],
        "seed": seed,
        "nthread": -1,
    }
    evals_result: dict[str, dict[str, list[float]]] = {}
    booster = xgb.train(
        params,
        dtrain,
        num_boost_round=candidate["num_boost_round"],
        evals=[(dtrain, "train"), (dvalidation, "validation")],
        early_stopping_rounds=early_stopping_rounds,
        evals_result=evals_result,
        verbose_eval=False,
    )
    best_iteration = int(booster.best_iteration)
    booster = booster[: best_iteration + 1]
    validation_prediction = booster.predict(dvalidation)
    result = {
        "candidate": candidate["name"],
        "best_iteration": best_iteration,
        "validation": regression_metrics(y.iloc[validation_idx], validation_prediction),
        "last_train_rmse": float(evals_result["train"]["rmse"][best_iteration]),
        "last_validation_rmse": float(
            evals_result["validation"]["rmse"][best_iteration]
        ),
    }
    return booster, result


def git_revision() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return "nogit"


def save_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def promote_model(source: Path, destination: Path) -> None:
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_bytes(source.read_bytes())
    temporary.replace(destination)


def main() -> None:
    args = parse_args()
    if not 0 < args.target_r2 <= 1:
        raise SystemExit("--target-r2 0 ile 1 arasında olmalı")

    print(f"Veri yükleniyor: {args.input}", flush=True)
    df = pd.read_csv(args.input)
    validate_dataset(df)
    X = df[list(FEATURE_ORDER)].astype(float)
    train_idx, validation_idx, test_idx, manifest = make_group_split(
        df,
        seed=args.seed,
        test_size=args.test_size,
        validation_size=args.validation_size,
    )

    run_id = args.run_id or (
        datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + git_revision()
    )
    run_dir = args.output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    manifest.to_csv(run_dir / "split_manifest.csv", index=False, encoding="utf-8")

    config = {
        "run_id": run_id,
        "input": str(args.input.resolve()),
        "seed": args.seed,
        "target_r2": args.target_r2,
        "test_size": args.test_size,
        "validation_size_within_train": args.validation_size,
        "early_stopping_rounds": args.early_stopping_rounds,
        "candidates": list(CANDIDATES),
        "row_counts": {
            "train": len(train_idx),
            "validation": len(validation_idx),
            "test": len(test_idx),
        },
        "group_counts": manifest["split"].value_counts().sort_index().to_dict(),
    }
    save_json(run_dir / "training_config.json", config)
    save_json(
        run_dir / "feature_schema.json",
        {"features": list(FEATURE_ORDER), "targets": list(TARGET_COLUMNS)},
    )

    all_metrics: dict[str, Any] = {
        "run_id": run_id,
        "acceptance": {"metric": "test_r2", "threshold": args.target_r2},
        "models": {},
    }
    trained_models: dict[str, Path] = {}

    for offset, (energy, target) in enumerate(ENERGIES.items()):
        print(f"\n{energy.upper()} modeli eğitiliyor", flush=True)
        candidate_results: list[dict[str, Any]] = []
        selected_booster: xgb.Booster | None = None
        selected_result: dict[str, Any] | None = None
        for candidate in CANDIDATES:
            booster, result = train_candidate(
                X,
                df[target],
                train_idx,
                validation_idx,
                candidate,
                seed=args.seed + offset,
                early_stopping_rounds=args.early_stopping_rounds,
            )
            candidate_results.append(result)
            print(
                f"  {candidate['name']}: doğrulama R²="
                f"{result['validation']['r2']:.6f}, "
                f"MAE={result['validation']['mae']:.4f}",
                flush=True,
            )
            if (
                selected_result is None
                or result["validation"]["r2"]
                > selected_result["validation"]["r2"]
            ):
                selected_booster = booster
                selected_result = result
            if result["validation"]["r2"] >= args.target_r2:
                break

        assert selected_booster is not None and selected_result is not None
        dtrain = xgb.DMatrix(X.iloc[train_idx], feature_names=list(FEATURE_ORDER))
        dvalidation = xgb.DMatrix(
            X.iloc[validation_idx], feature_names=list(FEATURE_ORDER)
        )
        dtest = xgb.DMatrix(X.iloc[test_idx], feature_names=list(FEATURE_ORDER))
        predictions = {
            "train": selected_booster.predict(dtrain),
            "validation": selected_booster.predict(dvalidation),
            "test": selected_booster.predict(dtest),
        }
        model_metrics = {
            "selected_candidate": selected_result["candidate"],
            "best_iteration": selected_result["best_iteration"],
            "candidate_results": candidate_results,
            "train": regression_metrics(df[target].iloc[train_idx], predictions["train"]),
            "validation": regression_metrics(
                df[target].iloc[validation_idx], predictions["validation"]
            ),
            "test": regression_metrics(df[target].iloc[test_idx], predictions["test"]),
            "ranking": rank_metrics(
                df.iloc[test_idx], target, predictions["test"]
            ),
            "segments": segmented_mae(
                df.iloc[test_idx], target, predictions["test"]
            ),
        }
        all_metrics["models"][energy] = model_metrics

        model_path = run_dir / f"{energy}_model.json"
        selected_booster.save_model(model_path)
        trained_models[energy] = model_path
        print(
            f"  TEST R²={model_metrics['test']['r2']:.6f}, "
            f"MAE={model_metrics['test']['mae']:.4f}, "
            f"RMSE={model_metrics['test']['rmse']:.4f}",
            flush=True,
        )

    passed = all(
        metrics["test"]["r2"] >= args.target_r2
        for metrics in all_metrics["models"].values()
    )
    all_metrics["acceptance"]["passed"] = passed
    save_json(run_dir / "metrics.json", all_metrics)

    card_lines = [
        f"# Buraki model kartı — {run_id}",
        "",
        "Bu modeller gerçek yatırım sonucunu değil, deterministik GES/RES skorunu ",
        "yaklaştırır. Test kümesi eğitimde görülmemiş ilçelerden oluşur.",
        "",
        f"Kabul eşiği: test R² ≥ {args.target_r2:.2%}",
        "",
        "| Model | Test R² | Test MAE | Test RMSE | İlçe Spearman |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for energy, metrics in all_metrics["models"].items():
        card_lines.append(
            f"| {energy.upper()} | {metrics['test']['r2']:.6f} | "
            f"{metrics['test']['mae']:.4f} | {metrics['test']['rmse']:.4f} | "
            f"{metrics['ranking']['district_spearman']:.6f} |"
        )
    card_lines.extend(["", f"Kabul sonucu: {'GEÇTİ' if passed else 'KALDI'}", ""])
    (run_dir / "model_card.md").write_text("\n".join(card_lines), encoding="utf-8")

    if not passed:
        raise SystemExit(
            f"Kabul eşiği sağlanmadı. Ayrıntılar: {run_dir / 'metrics.json'}"
        )

    if not args.no_promote:
        promote_model(
            trained_models["ges"], args.output_dir / "Yapay_Zeka_GES_Modeli.json"
        )
        promote_model(
            trained_models["res"], args.output_dir / "Yapay_Zeka_RES_Modeli.json"
        )
    print(f"\nKabul eşiği sağlandı. Artefaktlar: {run_dir}", flush=True)


if __name__ == "__main__":
    main()
