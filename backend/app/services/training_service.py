"""ML eğitim servis katmanı.

Developer panelinden tetiklenen eğitim job'larını yürütür. Senkron çalışmamak
için arka planda (FastAPI BackgroundTasks veya threading) çağrılır. Küçük veri
seti olduğunda hızlı (quick) modda küçük bir XGBoost modeli eğitir, metrikleri
hesaplar ve model_registry içine yeni bir kayıt düşer.
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import threading
import traceback
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import AuditLog, ModelMetric, ModelRegistry, TrainingJob
from app.db.session import SessionLocal
from app.ml.schema import FEATURE_ORDER
from app.schemas.ml import TrainingJobCreate

logger = logging.getLogger(__name__)


_TARGET_COLS = {
    "ges": "GES_YATIRIM_SKORU",
    "res": "RES_YATIRIM_SKORU",
}


def _audit(db: Session, actor: str, action: str, detail: dict) -> None:
    db.add(AuditLog(actor=actor, action=action, detail=detail))


def _dataset_path(version: str | None) -> Path:
    if version:
        candidate = settings.data_dir / "processed" / f"{version}.csv"
        if candidate.exists():
            return candidate
    return settings.data_dir / "processed" / "XGBoost_Egitim_Veriseti_Duzeltilmis.csv"


def _make_version(job_id: int) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha1(f"{job_id}-{ts}".encode()).hexdigest()[:7]
    return f"{ts}_{suffix}_job{job_id}"


def create_job(
    db: Session, actor: str, payload: TrainingJobCreate
) -> TrainingJob:
    job = TrainingJob(
        status="queued",
        requested_by=actor,
        dataset_version=payload.dataset_version,
        energy_targets=list(payload.energy_targets),
        parameters=payload.model_dump(),
        note=payload.note,
    )
    db.add(job)
    _audit(
        db,
        actor,
        "ml.training.queued",
        {"targets": list(payload.energy_targets), "quick": payload.quick_mode},
    )
    db.commit()
    db.refresh(job)
    return job


def run_job_async(job_id: int) -> None:
    """Job'u arka plan thread'inde çalıştır (FastAPI bağlamından bağımsız)."""
    thread = threading.Thread(
        target=_run_job_isolated, args=(job_id,), daemon=True
    )
    thread.start()


def _run_job_isolated(job_id: int) -> None:
    """Yeni bir Session ile job'u yürütür."""
    db = SessionLocal()
    try:
        execute_job(db, job_id)
    except Exception:  # pragma: no cover - defansif
        logger.exception("Training job %s failed top-level", job_id)
    finally:
        db.close()


def execute_job(db: Session, job_id: int) -> TrainingJob:
    job = db.get(TrainingJob, job_id)
    if job is None:
        raise ValueError(f"Job {job_id} bulunamadı")

    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    db.commit()

    log_buffer = io.StringIO()
    started_at = datetime.now(timezone.utc)
    try:
        params: dict[str, Any] = dict(job.parameters or {})
        targets = list(job.energy_targets or ["ges", "res"])
        with redirect_stdout(log_buffer):
            print(f"Job {job_id} başlatıldı: targets={targets}")
            result_models = _train_models(
                db=db,
                job=job,
                targets=targets,
                params=params,
            )
        job.result_models = result_models
        job.status = "completed"
        job.log_text = log_buffer.getvalue()
    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)
        job.log_text = log_buffer.getvalue() + "\n" + traceback.format_exc()
    finally:
        finished = datetime.now(timezone.utc)
        job.finished_at = finished
        job.duration_seconds = (finished - started_at).total_seconds()
        _audit(
            db,
            job.requested_by,
            f"ml.training.{job.status}",
            {"job_id": job.id, "targets": list(job.energy_targets or [])},
        )
        db.commit()
        db.refresh(job)
    return job


def _train_models(
    *,
    db: Session,
    job: TrainingJob,
    targets: list[str],
    params: dict[str, Any],
) -> dict[str, Any]:
    """Verilen targetler için ayrı XGBoost modelleri eğitir."""

    import numpy as np
    import pandas as pd
    import xgboost as xgb
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.model_selection import train_test_split

    dataset_path = _dataset_path(job.dataset_version)
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Eğitim veri seti bulunamadı: {dataset_path}"
        )
    print(f"Veri seti: {dataset_path}")
    df = pd.read_csv(dataset_path)
    if params.get("quick_mode", True) and len(df) > 5000:
        df = df.sample(n=5000, random_state=params.get("random_state", 42))
        print(f"Quick mode: {len(df)} satıra örnek alındı")

    feature_cols = [c for c in FEATURE_ORDER if c in df.columns]
    if not feature_cols:
        raise ValueError("Veri setinde beklenen feature kolonları yok")
    print(f"Özellikler: {feature_cols}")

    X = df[feature_cols].astype(float)
    version = _make_version(job.id)
    out_dir = settings.model_registry_dir / version
    out_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {}
    for energy in targets:
        target_col = _TARGET_COLS.get(energy)
        if target_col is None or target_col not in df.columns:
            print(f"{energy} hedefi atlandı (kolon yok): {target_col}")
            continue
        y = df[target_col].astype(float)
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=params.get("test_size", 0.2),
            random_state=params.get("random_state", 42),
        )
        booster_params = {
            "objective": "reg:squarederror",
            "learning_rate": params.get("learning_rate", 0.05),
            "max_depth": params.get("max_depth", 6),
            "seed": params.get("random_state", 42),
        }
        dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=feature_cols)
        dtest = xgb.DMatrix(X_test, label=y_test, feature_names=feature_cols)
        booster = xgb.train(
            booster_params,
            dtrain,
            num_boost_round=params.get("n_estimators", 400),
        )
        preds = booster.predict(dtest)
        mae = float(mean_absolute_error(y_test, preds))
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        r2 = float(r2_score(y_test, preds))
        print(f"{energy}: MAE={mae:.4f} RMSE={rmse:.4f} R2={r2:.4f}")

        artifact_rel = f"{version}/Yapay_Zeka_{energy.upper()}_Modeli.json"
        artifact_path = settings.model_registry_dir / artifact_rel
        booster.save_model(str(artifact_path))

        importance = booster.get_score(importance_type="gain")

        model = ModelRegistry(
            model_version=version,
            energy_type=energy,
            artifact_path=artifact_rel,
            dataset_version=job.dataset_version or dataset_path.stem,
            scoring_version=settings.data_version,
            status="completed",
            metrics={"mae": mae, "rmse": rmse, "r2": r2, "test_size": len(X_test)},
            feature_names=feature_cols,
            feature_importance={k: float(v) for k, v in importance.items()},
            parameters=booster_params | {"n_estimators": params.get("n_estimators", 400)},
            training_job_id=job.id,
            created_by=job.requested_by,
        )
        db.add(model)
        db.flush()
        db.add(
            ModelMetric(
                model_id=model.id,
                energy_type=energy,
                mae=mae,
                rmse=rmse,
                r2=r2,
                test_size=float(params.get("test_size", 0.2)),
                sample_count=len(df),
            )
        )
        result[energy] = {
            "model_id": model.id,
            "model_version": version,
            "metrics": model.metrics,
            "artifact": artifact_rel,
        }
    if not result:
        raise ValueError("Hiçbir hedef için model eğitilemedi")

    summary_path = out_dir / "training_summary.json"
    summary_path.write_text(
        json.dumps(
            {"job_id": job.id, "result": result, "params": params},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return result
