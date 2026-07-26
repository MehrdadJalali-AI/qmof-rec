"""
Password hashing and JWT helpers for authentication.
"""

import hashlib
import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "14"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire, "type": "access"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def refresh_token_expiry() -> datetime:
    """Naive-UTC expiry timestamp for a freshly issued refresh token,
    matching the convention used for DB-stored datetimes (see app/db/models.py)."""
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
        days=REFRESH_TOKEN_EXPIRE_DAYS
    )


def create_refresh_token(subject: str, jti: str) -> str:
    """jti (JWT ID) uniquely identifies this token so it can be revoked
    server-side via its hash without needing to store the raw token."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": subject, "exp": expire, "type": "refresh", "jti": jti}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def hash_token(token: str) -> str:
    """One-way hash used to store/look up refresh tokens without keeping
    the raw bearer token in the database."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
