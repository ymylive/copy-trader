"""AES-GCM decryption of API keys; format identical to backend/app/core/security.py.

Layout of the base64 blob ::

    nonce(12 bytes) || ciphertext(N) || tag(16 bytes)
"""
from __future__ import annotations

import base64
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .config import get_settings


def _aes() -> AESGCM:
    return AESGCM(get_settings().aes_key_bytes)


def encrypt_secret(plaintext: str) -> str:
    """Used in tests / utilities — mirrors backend implementation."""
    import os

    aes = _aes()
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)
    return base64.b64encode(nonce + ct).decode("ascii")


def decrypt_secret(blob: Optional[str]) -> Optional[str]:
    if not blob:
        return None
    raw = base64.b64decode(blob)
    nonce, ct = raw[:12], raw[12:]
    return _aes().decrypt(nonce, ct, associated_data=None).decode("utf-8")
