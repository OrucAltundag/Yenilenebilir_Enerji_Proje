"""JWT üretimi/doğrulaması ve parola hashleme (Faz 8).

Basit kullanıcı deposu (in-memory) ile demo amaçlı; üretimde OIDC sağlayıcısı
ve gerçek kullanıcı tablosu kullanılır. RBAC rolleri token claim'inde taşınır.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# pbkdf2_sha256: saf Python, harici bcrypt sürüm uyumsuzluğundan etkilenmez
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_token_ttl_min),
    }
    return jwt.encode(payload, settings.app_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token, settings.app_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError as exc:
        raise ValueError("Geçersiz veya süresi dolmuş token") from exc
