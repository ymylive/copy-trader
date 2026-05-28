"""JWT, bcrypt and AES-GCM primitives."""
from __future__ import annotations

import base64
import os
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import JWTError, jwt

from app.config import get_settings


_settings = get_settings()

# ── Password hashing ──────────────────────────────────────────────────


def hash_password(plain: str) -> str:
    """bcrypt hash; returns utf-8 string."""
    salt = bcrypt.gensalt(rounds=_settings.bcrypt_rounds)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ── JWT ───────────────────────────────────────────────────────────────


def _create_token(sub: str, ttl_min: int, *, typ: str, extra: dict[str, Any] | None = None) -> str:
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ttl_min)).timestamp()),
        "typ": typ,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, _settings.jwt_secret, algorithm=_settings.jwt_algorithm)


def create_access_token(sub: str, extra: dict[str, Any] | None = None) -> str:
    return _create_token(sub, _settings.access_token_ttl_min, typ="access", extra=extra)


def create_refresh_token(sub: str) -> str:
    return _create_token(sub, _settings.refresh_token_ttl_min, typ="refresh")


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, _settings.jwt_secret, algorithms=[_settings.jwt_algorithm])
    except JWTError as exc:  # noqa: BLE001
        raise ValueError(f"invalid token: {exc}") from exc


# ── AES-GCM for API key/secret ────────────────────────────────────────


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a sensitive value with AES-256-GCM; returns base64(nonce|ct)."""
    if plaintext is None:
        return None  # type: ignore[return-value]
    aes = AESGCM(_settings.aes_key_bytes)
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)
    return base64.b64encode(nonce + ct).decode("ascii")


def decrypt_secret(blob: str | None) -> str | None:
    if not blob:
        return None
    raw = base64.b64decode(blob)
    nonce, ct = raw[:12], raw[12:]
    aes = AESGCM(_settings.aes_key_bytes)
    return aes.decrypt(nonce, ct, associated_data=None).decode("utf-8")


# ── Invite code / random tokens ───────────────────────────────────────


_ALPHABET = string.ascii_uppercase + string.digits


def generate_invite_code(length: int = 8) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


def generate_random_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)
