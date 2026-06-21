"""Auth endpointleri.

QA BUG-005: basit per-IP+kullanıcı sliding window rate limit (in-memory).
Üretim için Redis/RFC tabanlı bir limiter'a taşınmalı; ancak demo kullanım
seviyesinde brute force'a karşı gözle görülür koruma sağlar.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.core.users import get_user

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


_attempts: dict[str, deque[float]] = defaultdict(deque)
_attempts_lock = threading.Lock()


def _rate_limit_key(request: Request, username: str) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{host}|{username.lower()}"


def _check_rate_limit(key: str) -> None:
    window = settings.login_rate_window_seconds
    limit = settings.login_rate_max_attempts
    now = time.monotonic()
    with _attempts_lock:
        bucket = _attempts[key]
        while bucket and now - bucket[0] > window:
            bucket.popleft()
        if len(bucket) >= limit:
            retry = int(window - (now - bucket[0]))
            raise HTTPException(
                status_code=429,
                detail=f"Çok fazla deneme; {max(retry, 1)} saniye bekleyin",
            )


def _record_failure(key: str) -> None:
    with _attempts_lock:
        _attempts[key].append(time.monotonic())


def _reset_attempts(key: str) -> None:
    with _attempts_lock:
        _attempts.pop(key, None)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request):
    key = _rate_limit_key(request, payload.username)
    _check_rate_limit(key)
    user = get_user(payload.username)
    if user is None or not verify_password(payload.password, user.password_hash):
        _record_failure(key)
        raise HTTPException(status_code=401, detail="Kullanıcı adı veya parola hatalı")
    _reset_attempts(key)
    token = create_access_token(subject=user.username, role=user.role)
    return TokenResponse(access_token=token, role=user.role)
