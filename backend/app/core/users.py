"""Demo kullanıcı deposu (in-memory).

Üretimde gerçek kullanıcı tablosu / OIDC ile değiştirilir. Roller: admin, analyst.
Varsayılan parolalar yalnız geliştirme içindir.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.security import hash_password


@dataclass(frozen=True)
class User:
    username: str
    role: str
    password_hash: str


_USERS: dict[str, User] = {
    "admin": User("admin", "admin", hash_password("admin123")),
    "analyst": User("analyst", "analyst", hash_password("analyst123")),
}


def get_user(username: str) -> User | None:
    return _USERS.get(username)
