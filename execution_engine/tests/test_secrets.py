"""AES-GCM round-trip parity with the backend."""
from __future__ import annotations

from engine.secrets import decrypt_secret, encrypt_secret


def test_aes_roundtrip():
    msg = "secret_api_key_!@#$"
    blob = encrypt_secret(msg)
    assert isinstance(blob, str) and blob != msg
    assert decrypt_secret(blob) == msg


def test_decrypt_empty():
    assert decrypt_secret(None) is None
    assert decrypt_secret("") is None
