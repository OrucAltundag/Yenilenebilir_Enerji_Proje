"""Kimlik ve yetki bağımlılıkları.

Öncelik: Authorization Bearer (JWT) → X-User-Id başlığı (demo) → "anon".
RBAC için require_role kullanılır.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException

from app.core.security import decode_token


@dataclass(frozen=True)
class Principal:
    user_id: str
    role: str


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
    if x_user_id:
        return Principal(user_id=x_user_id, role="analyst")
    return Principal(user_id="anon", role="anon")


def current_user(principal: Principal = Depends(get_principal)) -> str:
    return principal.user_id


def require_role(*roles: str):
    def checker(principal: Principal = Depends(get_principal)) -> Principal:
        if principal.role not in roles:
            raise HTTPException(status_code=403, detail="Yetki yetersiz")
        return principal

    return checker
