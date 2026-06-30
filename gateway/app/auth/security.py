"""Password hashing (bcrypt) and JWT helpers (HS256 via python-jose)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

# bcrypt has a 72-byte input limit; we hash a fixed-length digest-free truncation
# guard by encoding and slicing defensively (passwords beyond 72 bytes are rare).
_BCRYPT_MAX = 72


def hash_password(password: str) -> str:
    raw = password.encode("utf-8")[:_BCRYPT_MAX]
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:_BCRYPT_MAX], password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(
    subject: str, *, secret: str, algorithm: str, expire_minutes: int, extra: dict | None = None
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expire_minutes)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_token(token: str, *, secret: str, algorithm: str) -> dict | None:
    try:
        return jwt.decode(token, secret, algorithms=[algorithm])
    except JWTError:
        return None
