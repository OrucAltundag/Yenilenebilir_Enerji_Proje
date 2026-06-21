"""QA test raporundan üretilen regression testleri.

Kapsam:
    - BUG-001: Tokensız korumalı endpoint 401 dönmeli.
    - BUG-002: Demo X-User-Id başlığı yalnız flag açıkken kabul edilmeli.
    - BUG-003: Production secret guard'ı fail-fast üretmeli.
    - BUG-005: Login rate limit ardışık başarısız denemelerde 429 üretmeli.
"""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

from app.core import auth, config
from app.main import app

client = TestClient(app)


def _login(username: str, password: str) -> dict[str, str]:
    res = client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


# ---------- BUG-001 ----------


def test_projects_without_token_returns_401():
    r = client.get("/api/v1/projects")
    assert r.status_code == 401


def test_scenarios_list_without_token_returns_401():
    r = client.get("/api/v1/projects/scenarios/list")
    assert r.status_code == 401


# ---------- BUG-002 ----------


def test_demo_header_accepted_when_flag_enabled(monkeypatch):
    monkeypatch.setattr(config.settings, "allow_demo_user_header", True)
    r = client.get("/api/v1/projects", headers={"X-User-Id": "alice"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_demo_header_rejected_when_flag_disabled(monkeypatch):
    monkeypatch.setattr(config.settings, "allow_demo_user_header", False)
    r = client.get("/api/v1/projects", headers={"X-User-Id": "alice"})
    assert r.status_code == 401


# ---------- BUG-003 ----------


def test_production_with_default_secret_fails(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_SECRET_KEY", "change-me")
    with pytest.raises(RuntimeError):
        importlib.reload(config)


def test_production_with_strong_secret_disables_demo_header(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_SECRET_KEY", "x" * 64)
    fresh = importlib.reload(config)
    assert fresh.settings.allow_demo_user_header is False
    # Diğer testleri etkilemeyelim diye varsayılan modülü geri yükle
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("APP_SECRET_KEY", raising=False)
    importlib.reload(config)


# ---------- BUG-005 ----------


def test_login_rate_limit_after_repeated_failures(monkeypatch):
    # `app.api.v1.endpoints.auth` modülü `settings`'i bağladığı andan itibaren
    # aynı referansı kullanır; reload yapan testler bu referansı değiştirdiği
    # için doğrudan endpoint modülünün gördüğü settings'i monkeypatch ediyoruz.
    from app.api.v1.endpoints import auth as auth_endpoint

    monkeypatch.setattr(auth_endpoint.settings, "login_rate_max_attempts", 3)
    monkeypatch.setattr(auth_endpoint.settings, "login_rate_window_seconds", 60)
    auth_endpoint._attempts.clear()
    for _ in range(3):
        r = client.post(
            "/api/v1/auth/login",
            json={"username": "ratelimituser", "password": "nope"},
        )
        assert r.status_code == 401
    r = client.post(
        "/api/v1/auth/login",
        json={"username": "ratelimituser", "password": "nope"},
    )
    assert r.status_code == 429


# ---------- require_role anon → 401 ----------


def test_ml_endpoint_anonymous_returns_401():
    r = client.get("/api/v1/ml/training-jobs")
    assert r.status_code == 401


def test_admin_endpoint_anonymous_returns_401():
    r = client.get("/api/v1/admin/dataset/active")
    assert r.status_code == 401


def test_admin_endpoint_analyst_returns_403():
    headers = _login("analyst", "analyst123")
    r = client.get("/api/v1/admin/dataset/active", headers=headers)
    assert r.status_code == 403


# Auth core unit'ı
def test_auth_principal_anon_flag():
    p = auth.Principal(user_id="anon", role=auth.ANON_ROLE)
    assert p.is_authenticated is False
    p2 = auth.Principal(user_id="alice", role="analyst")
    assert p2.is_authenticated is True
