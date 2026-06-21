from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Proje kök dizini: backend/app/core/config.py -> parents[3] = proje kökü
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_secret_key: str = "change-me"

    # QA BUG-002: demo X-User-Id başlığı yalnız dev/test'te kabul edilir.
    # APP_ENV=production iken default False (üretimde kapalı).
    allow_demo_user_header: bool = True

    # QA BUG-005: login için saniye/limit eşikleri (kullanıcı + IP başına).
    login_rate_window_seconds: int = 60
    login_rate_max_attempts: int = 5

    # Dev varsayılanı SQLite (sunucusuz); docker-compose DATABASE_URL ile Postgres'e geçer
    database_url: str = f"sqlite:///{(PROJECT_ROOT / 'data' / 'buraki_dev.db').as_posix()}"
    data_repository: str = "auto"  # auto|csv|database
    redis_url: str = "redis://localhost:6379/0"

    jwt_algorithm: str = "HS256"
    jwt_access_token_ttl_min: int = 30

    project_root: Path = PROJECT_ROOT
    data_dir: Path = PROJECT_ROOT / "data"
    model_registry_dir: Path = PROJECT_ROOT / "data" / "models"
    ges_model_file: str = "Yapay_Zeka_GES_Modeli.json"
    res_model_file: str = "Yapay_Zeka_RES_Modeli.json"
    scoring_config_path: Path = PROJECT_ROOT / "ml" / "scoring" / "scoring_config.json"

    # Dosya tabanlı veri kaynakları (MVP — Postgres yerine)
    summary_csv: Path = PROJECT_ROOT / "data" / "processed" / "district_score_summary.csv"
    monthly_csv: Path = PROJECT_ROOT / "data" / "processed" / "district_monthly_profile.csv"
    master_csv: Path = PROJECT_ROOT / "data" / "reference" / "district_master.csv"
    district_geometry_path: Path = (
        PROJECT_ROOT / "data" / "reference" / "district_boundaries.geojson"
    )
    global_shap_path: Path = PROJECT_ROOT / "data" / "shap" / "global_shap_summary.json"

    data_version: str = "2023.1"

    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
    ]


def _load_settings() -> Settings:
    s = Settings()
    # QA BUG-003: production'da default secret ile başlamayı engelle
    if s.app_env.lower() in {"production", "prod"}:
        if s.app_secret_key == "change-me" or len(s.app_secret_key) < 32:
            raise RuntimeError(
                "APP_SECRET_KEY production'da varsayılan/zayıf değerle kullanılamaz "
                "(en az 32 karakter, 'change-me' kabul edilmez)."
            )
        # production'da demo header otomatik kapalı
        s.allow_demo_user_header = False
    return s


settings = _load_settings()
