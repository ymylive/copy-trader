"""Auth endpoint tests."""
from __future__ import annotations

import secrets

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_happy_path(client: AsyncClient) -> None:
    username = "alice_" + secrets.token_hex(3)
    r = await client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": "Hunter2!", "email": "alice@example.com"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["username"] == username
    assert body["invite_code"]
    assert body["referral_rate"] == 0.10
    assert body["referred_by"] is None

    # Login → token
    r = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "Hunter2!"},
    )
    assert r.status_code == 200
    tok = r.json()
    assert tok["access_token"]
    assert tok["refresh_token"]
    assert tok["token_type"] == "bearer"

    # /me with token
    headers = {"Authorization": f"Bearer {tok['access_token']}"}
    r = await client.get("/api/v1/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["username"] == username


@pytest.mark.asyncio
async def test_register_invite_chain(client: AsyncClient) -> None:
    """Inviter → invitee referral linkage."""
    inviter_name = "bob_" + secrets.token_hex(3)
    r = await client.post(
        "/api/v1/auth/register",
        json={"username": inviter_name, "password": "pw1234"},
    )
    invite_code = r.json()["invite_code"]
    assert invite_code

    invitee_name = "charlie_" + secrets.token_hex(3)
    r = await client.post(
        "/api/v1/auth/register",
        json={"username": invitee_name, "password": "pw1234", "invite_code": invite_code},
    )
    assert r.status_code == 201
    assert r.json()["referred_by"] is not None


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient) -> None:
    """Wrong password yields 401 with our standard error envelope."""
    name = "dave_" + secrets.token_hex(3)
    await client.post(
        "/api/v1/auth/register",
        json={"username": name, "password": "right_pw_99"},
    )
    r = await client.post(
        "/api/v1/auth/login",
        json={"username": name, "password": "WRONG"},
    )
    assert r.status_code == 401
    assert r.json()["code"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_me_requires_token(client: AsyncClient) -> None:
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_password_change_flow(client: AsyncClient) -> None:
    name = "eve_" + secrets.token_hex(3)
    await client.post("/api/v1/auth/register", json={"username": name, "password": "old_pw_123"})
    r = await client.post("/api/v1/auth/login", json={"username": name, "password": "old_pw_123"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = await client.post(
        "/api/v1/auth/password",
        headers=headers,
        json={"old_password": "old_pw_123", "new_password": "new_pw_456"},
    )
    assert r.status_code == 200

    # Old password should now fail
    r = await client.post(
        "/api/v1/auth/login", json={"username": name, "password": "old_pw_123"}
    )
    assert r.status_code == 401
    # New password works
    r = await client.post(
        "/api/v1/auth/login", json={"username": name, "password": "new_pw_456"}
    )
    assert r.status_code == 200
