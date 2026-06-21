"""Kimlik ve yetki bağımlılıkları.

Yetkilendirme önceliği:
    1. Authorization: Bearer <JWT>
    2. X-User-Id başlığı — yalnız ``settings.allow_demo_user_header=True`` ise
       (development/test için).
    3. Aksi halde principal anon olarak işaretlenir; korumalı endpointler
       ``require_authenticated`` veya ``require_role`` ile bunu reddeder.

QA raporu BUG-001/BUG-002: korumalı endpointler anon erişimi reddetmeli ve
demo header'ı production'da kabul edilmemelidir.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException

from app.core.config import settings
from app.core.security import decode_token

ANON_ROLE = "anon"


@dataclass(frozen=True)
class Principal:
    user_id: str
    role: str

    @property
    def is_authenticated(self) -> bool:
        return self.role != ANON_ROLE and self.user_id != "anon"


def get_principal(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
) -> Principal:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            claims = decode_token(token)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        return Principal(user_id=claims["sub"], role=claims.get("role", "analyst"))
    if x_user_id and settings.allow_demo_user_header:
        return Principal(user_id=x_user_id, role="analyst")
    return Principal(user_id="anon", role=ANON_ROLE)


def require_authenticated(
    principal: Principal = Depends(get_principal),
) -> Principal:
    """Anon principal'ı 401 ile reddeder; rol kontrolü yapmaz."""
    if not principal.is_authenticated:
        raise HTTPException(status_code=401, detail="Kimlik doğrulama gerekli")
    return principal


def current_user(
    principal: Principal = Depends(require_authenticated),
) -> str:
    return principal.user_id


def require_role(*roles: str):
    def checker(principal: Principal = Depends(get_principal)) -> Principal:
        if not principal.is_authenticated:
            raise HTTPException(status_code=401, detail="Kimlik doğrulama gerekli")
        if principal.role not in roles:
            raise HTTPException(status_code=403, detail="Yetki yetersiz")
        return principal

    return checker
