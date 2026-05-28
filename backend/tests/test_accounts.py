"""Exchange-account endpoint tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_account_lifecycle(authed_client: tuple[AsyncClient, dict]) -> None:
    client, _ = authed_client
    # Create
    r = await client.post(
        "/api/v1/accounts/",
        json={
            "alias": "账户1",
            "tier": "standard",
            "exchange": "binance",
            "leverage_default": 20,
        },
    )
    assert r.status_code == 201, r.text
    acc = r.json()
    aid = acc["id"]
    assert acc["status"] == "inactive"
    assert acc["has_api_key"] is False

    # List
    r = await client.get("/api/v1/accounts/")
    assert r.status_code == 200
    assert any(a["id"] == aid for a in r.json())

    # Patch
    r = await client.patch(f"/api/v1/accounts/{aid}", json={"leverage_default": 50})
    assert r.status_code == 200
    assert r.json()["leverage_default"] == 50

    # Activate without API key fails
    r = await client.post(f"/api/v1/accounts/{aid}/activate")
    assert r.status_code == 400
    assert r.json()["code"] == "api_key_missing"

    # Set API key
    r = await client.post(
        f"/api/v1/accounts/{aid}/apikey",
        json={"api_key": "k_test", "api_secret": "s_test", "uid": "999"},
    )
    assert r.status_code == 200
    assert r.json()["has_api_key"] is True
    assert r.json()["uid"] == "999"

    # Activate succeeds (egress IP allocated)
    r = await client.post(f"/api/v1/accounts/{aid}/activate")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "active"
    assert len(body["egress_ips"]) >= 1

    # Balance returns stub (no Redis available in test)
    r = await client.get(f"/api/v1/accounts/{aid}/balance")
    assert r.status_code == 200
    assert r.json()["account_id"] == aid

    # Positions empty list
    r = await client.get(f"/api/v1/accounts/{aid}/positions")
    assert r.status_code == 200
    assert r.json() == []

    # Delete
    r = await client.delete(f"/api/v1/accounts/{aid}")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_account_duplicate_alias_409(authed_client: tuple[AsyncClient, dict]) -> None:
    client, _ = authed_client
    payload = {
        "alias": "dup_alias",
        "tier": "standard",
        "exchange": "okx",
        "leverage_default": 10,
    }
    r = await client.post("/api/v1/accounts/", json=payload)
    assert r.status_code == 201
    r = await client.post("/api/v1/accounts/", json=payload)
    assert r.status_code == 409
    assert r.json()["code"] == "alias_taken"


@pytest.mark.asyncio
async def test_account_not_found_for_other_user(client: AsyncClient) -> None:
    """User A creates an account; user B should get 404 when asking for it."""
    # Create user A and a private account
    await client.post("/api/v1/auth/register", json={"username": "userA", "password": "pwA1234"})
    r = await client.post(
        "/api/v1/auth/login", json={"username": "userA", "password": "pwA1234"}
    )
    a_token = r.json()["access_token"]
    r = await client.post(
        "/api/v1/accounts/",
        headers={"Authorization": f"Bearer {a_token}"},
        json={
            "alias": "isolation_acc",
            "tier": "standard",
            "exchange": "okx",
            "leverage_default": 5,
        },
    )
    assert r.status_code == 201
    a_acc_id = r.json()["id"]

    # User B
    await client.post("/api/v1/auth/register", json={"username": "userB", "password": "pwB1234"})
    r = await client.post(
        "/api/v1/auth/login", json={"username": "userB", "password": "pwB1234"}
    )
    b_token = r.json()["access_token"]
    r = await client.get(
        f"/api/v1/accounts/{a_acc_id}",
        headers={"Authorization": f"Bearer {b_token}"},
    )
    # GET /{id} not defined — try positions which uses get_account
    r = await client.get(
        f"/api/v1/accounts/{a_acc_id}/positions",
        headers={"Authorization": f"Bearer {b_token}"},
    )
    assert r.status_code == 404
    assert r.json()["code"] == "account_not_found"
