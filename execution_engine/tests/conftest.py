"""Pytest fixtures for the execution engine test suite."""
from __future__ import annotations

import base64
import os

# Use a deterministic AES key for all tests (must be set BEFORE importing engine).
os.environ.setdefault("AES_KEY", base64.b64encode(b"k" * 32).decode("ascii"))
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("ENABLE_SCHEDULER", "false")
os.environ.setdefault("DRY_RUN", "true")

import pytest
from engine.config import get_settings


@pytest.fixture(scope="session")
def settings():
    return get_settings()
