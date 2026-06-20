from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    from app.db.session import init_db

    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Buraki API",
        version="0.1.0",
        description=(
            "Yapay Zekâ Destekli Yenilenebilir Enerji Yatırım Karar Destek Sistemi "
            "için REST API."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/healthz", tags=["meta"])
    def healthz():
        return {"status": "ok"}

    return app


app = create_app()
