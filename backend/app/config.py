"""Application configuration via pydantic-settings."""
from __future__ import annotations

import base64
import os
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised application settings.

    All values can be overridden by environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── App ────────────────────────────────────────────────────────────
    app_name: str = "copy-trader-backend"
    app_env: str = Field(default="dev", description="dev/staging/prod")
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # ── Database ───────────────────────────────────────────────────────
    # Examples:
    #   postgresql+asyncpg://user:pass@localhost:5432/copy_trader
    #   sqlite+aiosqlite:///./dev.db
    database_url: str | None = None
    db_echo: bool = False

    # ── Redis ──────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Security ───────────────────────────────────────────────────────
    # JWT
    jwt_secret: str = "dev-insecure-jwt-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_min: int = 60 * 6        # 6 h
    refresh_token_ttl_min: int = 60 * 24 * 14  # 14 d

    # AES-GCM (32 bytes, base64 encoded). Default key generated for dev only.
    aes_key: str = base64.b64encode(b"0" * 32).decode("ascii")

    # bcrypt rounds
    bcrypt_rounds: int = 12

    # ── Egress IP pool (stub) ──────────────────────────────────────────
    egress_ip_pool: List[str] = Field(
        default_factory=lambda: [
            "203.0.113.10",
            "203.0.113.11",
            "203.0.113.12",
            "203.0.113.13",
        ]
    )

    # ── Pricing ────────────────────────────────────────────────────────
    referral_half_price: float = 0.5
    coupon_default_discount: float = 0.85

    # ── Internal service-to-service auth ───────────────────────────────
    # Shared secret between execution_engine and backend for POST /internal/*
    internal_token: str = "dev-internal-token-change-me"

    # ── Feature flags ──────────────────────────────────────────────────
    skip_db_startup_check: bool = True   # allow dev start without DB
    enable_scheduler: bool = False        # APScheduler off in tests

    @field_validator("aes_key")
    @classmethod
    def _aes_key_must_be_32_bytes(cls, v: str) -> str:
        try:
            raw = base64.b64decode(v)
        except Exception as exc:  # noqa: BLE001
            raise ValueError("AES_KEY must be base64") from exc
        if len(raw) != 32:
            raise ValueError("AES_KEY must decode to 32 bytes (AES-256)")
        return v

    @property
    def aes_key_bytes(self) -> bytes:
        return base64.b64decode(self.aes_key)

    @property
    def effective_database_url(self) -> str:
        """Return DB URL, defaulting to an in-memory SQLite for tests/dev."""
        if self.database_url:
            return self.database_url
        # In-memory SQLite shared across an async engine instance.
        return "sqlite+aiosqlite:///./copy_trader_dev.db"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Convenience
settings = get_settings()
