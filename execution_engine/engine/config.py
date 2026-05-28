"""Execution engine settings (pydantic v2)."""
from __future__ import annotations

import base64
import os
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EngineSettings(BaseSettings):
    """Settings for the execution engine."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Identity ───────────────────────────────────────────────────────
    app_name: str = "copy-trader-execution-engine"
    app_env: str = Field(default="dev")
    instance_id: str = Field(default_factory=lambda: os.environ.get("HOSTNAME", "runner-1"))

    # ── Infra ──────────────────────────────────────────────────────────
    database_url: str | None = None
    redis_url: str = "redis://localhost:6379/0"

    # ── Crypto: must match backend AES_KEY ─────────────────────────────
    aes_key: str = base64.b64encode(b"0" * 32).decode("ascii")

    @field_validator("aes_key")
    @classmethod
    def _aes_key_must_decode_to_32_bytes(cls, v: str) -> str:
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
        if self.database_url:
            return self.database_url
        return "sqlite+aiosqlite:///./engine_dev.db"

    # ── Redis consumer group ───────────────────────────────────────────
    consumer_group: str = "execution_engine"

    # ── Concurrency / rate limits ──────────────────────────────────────
    # global semaphore for in-flight orders across all runners
    max_concurrent_orders: int = 100

    # token bucket: requests per second by exchange (defensive defaults)
    exchange_rps: dict[str, float] = Field(
        default_factory=lambda: {
            "binance": 20.0,    # ~1200/min
            "okx": 30.0,        # ~60/2s safety
            "gate": 10.0,
            "bitget": 10.0,
            "hyperliquid": 100.0,
        }
    )

    # ── Scheduler ──────────────────────────────────────────────────────
    enable_scheduler: bool = True
    snapshot_interval_sec: int = 60
    nav_interval_sec: int = 3600
    refill_scan_interval_sec: int = 10
    config_reload_interval_sec: int = 10

    # ── Notifier ───────────────────────────────────────────────────────
    backend_internal_url: str = "http://backend:8000/api/v1/internal/notify"
    backend_internal_token: str = "internal-only"

    # ── Prometheus ─────────────────────────────────────────────────────
    metrics_port: int = 9100

    # ── Behaviour ──────────────────────────────────────────────────────
    dry_run: bool = False  # if True, don't actually call exchange APIs


@lru_cache(maxsize=1)
def get_settings() -> EngineSettings:
    return EngineSettings()


settings = get_settings()
