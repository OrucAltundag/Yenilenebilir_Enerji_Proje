from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import current_user
from app.core.config import settings
from app.data.repository import get_repository
from app.db.models import SavedProject, SavedScenario
from app.db.session import get_db
from app.ml.scoring_engine import ScoringConfig, score_record
from app.schemas.project import (
    ProjectCreate,
    ProjectOut,
    ScenarioOut,
    ScenarioSaveRequest,
)

router = APIRouter()

ALLOWED_OVERRIDES: dict[str, tuple[float, float]] = {
    "ALLSKY_SFC_SW_DWN": (0.0, 12.0),
    "WS10M": (0.0, 25.0),
    "arazi_egimi_yuzde": (0.0, 90.0),
    "tesvik_bolgesi": (1.0, 6.0),
}


# --- Projeler ---
@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    user: str = Depends(current_user),
):
    repo = get_repository()
    district_ids = list(dict.fromkeys(payload.district_ids))
    invalid = [district_id for district_id in district_ids if repo.get_summary(district_id) is None]
    if invalid:
        raise HTTPException(
            status_code=422,
            detail=f"Geçersiz ilçe kimliği: {', '.join(invalid)}",
        )
    project = SavedProject(
        owner_id=user,
        name=payload.name,
        note=payload.note,
        district_ids=district_ids,
        energy=payload.energy,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(
    db: Session = Depends(get_db), user: str = Depends(current_user)
):
    return (
        db.query(SavedProject)
        .filter(SavedProject.owner_id == user)
        .order_by(SavedProject.created_at.desc())
        .all()
    )


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: str = Depends(current_user),
):
    project = db.get(SavedProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proje bulunamadı")
    if project.owner_id != user:  # owner kontrolü (IDOR koruması)
        raise HTTPException(status_code=403, detail="Bu projeye erişim yok")
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: str = Depends(current_user),
):
    project = db.get(SavedProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proje bulunamadı")
    if project.owner_id != user:
        raise HTTPException(status_code=403, detail="Bu projeye erişim yok")
    db.delete(project)
    db.commit()


# --- Kaydedilen senaryolar ---
@router.post("/scenarios", response_model=ScenarioOut, status_code=201)
def save_scenario(
    payload: ScenarioSaveRequest,
    db: Session = Depends(get_db),
    user: str = Depends(current_user),
):
    if payload.project_id is not None:
        project = db.get(SavedProject, payload.project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Proje bulunamadı")
        if project.owner_id != user:
            raise HTTPException(status_code=403, detail="Bu projeye erişim yok")

    repo = get_repository()
    row = repo.get_summary(payload.district_id)
    if row is None:
        raise HTTPException(status_code=404, detail="İlçe bulunamadı")

    config = ScoringConfig.load(settings.scoring_config_path)
    snapshot = {
        "ALLSKY_SFC_SW_DWN": row["ALLSKY_SFC_SW_DWN"],
        "WS10M": row["WS10M"],
        "arazi_egimi_yuzde": row["arazi_egimi_yuzde"],
        "tesvik_bolgesi": row["tesvik_bolgesi"],
    }
    scenario_features = dict(snapshot)
    for key, value in payload.overrides.items():
        if key not in ALLOWED_OVERRIDES:
            raise HTTPException(status_code=422, detail=f"İzin verilmeyen alan: {key}")
        lo, hi = ALLOWED_OVERRIDES[key]
        if not (lo <= value <= hi):
            raise HTTPException(status_code=422, detail=f"{key} aralık dışı: {value}")
        scenario_features[key] = value

    baseline = score_record(snapshot, config)
    scenario = score_record(scenario_features, config)
    result = {
        "baseline": baseline,
        "scenario": scenario,
        "delta_ges": round(scenario["ges"] - baseline["ges"], 2),
        "delta_res": round(scenario["res"] - baseline["res"], 2),
    }

    record = SavedScenario(
        owner_id=user,
        project_id=payload.project_id,
        district_id=payload.district_id,
        overrides=payload.overrides,
        input_snapshot=snapshot,
        result=result,
        scoring_version=config.version,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/scenarios/list", response_model=list[ScenarioOut])
def list_scenarios(
    db: Session = Depends(get_db), user: str = Depends(current_user)
):
    return (
        db.query(SavedScenario)
        .filter(SavedScenario.owner_id == user)
        .order_by(SavedScenario.created_at.desc())
        .all()
    )
