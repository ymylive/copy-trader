"""Pytest fixtures: in-process SQLite + httpx AsyncClient."""
from __future__ import annotations

import asyncio
import base64
import os
from pathlib import Path
from typing import AsyncIterator

# Force test config BEFORE anything imports app.config
TEST_DB_FILE = Path(__file__).parent / "_test.sqlite"
if TEST_DB_FILE.exists():
    TEST_DB_FILE.unlink()

os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{TEST_DB_FILE}")
os.environ.setdefault("AES_KEY", base64.b64encode(b"X" * 32).decode("ascii"))
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("SKIP_DB_STARTUP_CHECK", "true")
os.environ.setdefault("ENABLE_SCHEDULER", "false")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _init_db():
    """Create tables once per test session."""
    from app.db.base import drop_db_for_tests, init_db_for_tests, reset_engine_for_tests

    reset_engine_for_tests()
    await init_db_for_tests()
    yield
    await drop_db_for_tests()


@pytest_asyncio.fixture()
async def client() -> AsyncIterator[AsyncClient]:
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture()
async def authed_client(client: AsyncClient) -> AsyncIterator[tuple[AsyncClient, dict]]:
    """Register + login and return (client_with_auth_header, user_dict)."""
    import secrets

    username = "u_" + secrets.token_hex(4)
    password = "Passw0rd!"
    r = await client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": password},
    )
    assert r.status_code == 201, r.text
    user = r.json()
    r = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    yield client, user
    client.headers.pop("Authorization", None)
