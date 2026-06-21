from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    auth,
    districts,
    meta,
    ml,
    projects,
    reports,
    scenarios,
    scores,
    shap,
)

api_router = APIRouter()
api_router.include_router(meta.router, tags=["meta"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(districts.router, prefix="/districts", tags=["districts"])
api_router.include_router(scores.router, prefix="/scores", tags=["scores"])
api_router.include_router(shap.router, prefix="/shap", tags=["shap"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(ml.router, prefix="/ml", tags=["ml"])
