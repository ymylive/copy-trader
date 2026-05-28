"""Copy-config endpoint tests."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.fixture()
async def setup_ctx(authed_client: tuple[AsyncClient, dict]):
    """Create one exchange account + one trader so a copy_config can be created."""
    import secrets

    client, user = authed_client
    suffix = secrets.token_hex(4)
    # Account
    r = await client.post(
        "/api/v1/accounts/",
        json={
            "alias": f"main_acc_{suffix}",
            "tier": "standard",
            "exchange": "okx",
            "leverage_default": 10,
        },
    )
    assert r.status_code == 201
    acc_id = r.json()["id"]
    # Seed a trader directly via DB (no public POST for catalogue).
    from app.db.base import session_scope
    from app.db.models import Trader

    async with session_scope() as db:
        tr = Trader(
            source="hyperliquid",
            external_id=f"0x{suffix}{suffix}",
            display_name="DemoTrader",
            exchange="hyperliquid",
            listed=True,
        )
        db.add(tr)
        await db.commit()
        trader_id = tr.id
    return client, user, acc_id, trader_id


@pytest.mark.asyncio
async def test_create_pause_resume_delete(setup_ctx) -> None:
    client, _, acc_id, trader_id = setup_ctx

    create_payload = {
        "exchange_account_id": acc_id,
        "trader_id": trader_id,
        "reverse": False,
        "name": "配置1",
        "money_mode": "fixed",
        "money_param": {"amount": 100.0},
        "multiplier": 1.5,
        "initial_strategy": "none",
        "direction_limit": "both",
        "open_trigger": {"kind": "market"},
        "add_trigger": {"kind": "avg_limit", "edge_pct": 0.5},
        "tp": {"enabled": True, "cycle": True, "qty_pct": 50.0},
        "sl": {"enabled": False},
        "loss_threshold": {"usdt": 200.0, "action": "pause_and_close"},
        "safety_cushion": {"nav_drop": 10.0, "decay_factor": 0.5},
        "refill": {"refill_on_back_to_avg": True, "allow_re_tp": True},
        "symbol_blacklist": ["DOGE-USDT-SWAP"],
        "symbol_whitelist": [],
        "notify_channels": ["tg"],
        "notify_types": ["open_ok", "open_fail"],
    }
    r = await client.post("/api/v1/copy-configs/", json=create_payload)
    assert r.status_code == 201, r.text
    cfg = r.json()
    cid = cfg["id"]
    assert cfg["status"] == "running"
    assert cfg["multiplier"] == 1.5
    assert cfg["trader"]["id"] == trader_id

    # List
    r = await client.get("/api/v1/copy-configs/")
    assert r.status_code == 200
    assert any(c["id"] == cid for c in r.json())

    # Patch
    r = await client.patch(f"/api/v1/copy-configs/{cid}", json={"multiplier": 2.0, "reverse": True})
    assert r.status_code == 200
    assert r.json()["multiplier"] == 2.0
    assert r.json()["reverse"] is True

    # Pause / resume
    r = await client.post(f"/api/v1/copy-configs/{cid}/pause")
    assert r.json()["status"] == "paused"
    r = await client.post(f"/api/v1/copy-configs/{cid}/resume")
    assert r.json()["status"] == "running"

    # Close-all (status → stopped)
    r = await client.post(f"/api/v1/copy-configs/{cid}/close-all")
    assert r.status_code == 200

    # Orders endpoint returns []
    r = await client.get(f"/api/v1/copy-configs/{cid}/orders")
    assert r.status_code == 200
    assert r.json() == []

    # Delete
    r = await client.delete(f"/api/v1/copy-configs/{cid}")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_create_rejects_bad_money_param(setup_ctx) -> None:
    client, _, acc_id, trader_id = setup_ctx
    r = await client.post(
        "/api/v1/copy-configs/",
        json={
            "exchange_account_id": acc_id,
            "trader_id": trader_id,
            "money_mode": "fixed",
            "money_param": {},  # missing amount
        },
    )
    assert r.status_code == 400
    assert r.json()["code"] == "bad_money_param"


@pytest.mark.asyncio
async def test_create_rejects_other_users_account(client: AsyncClient, setup_ctx) -> None:
    _, _, acc_id, trader_id = setup_ctx
    # Register a fresh user B
    await client.post("/api/v1/auth/register", json={"username": "intruder", "password": "pwpw1234"})
    r = await client.post(
        "/api/v1/auth/login", json={"username": "intruder", "password": "pwpw1234"}
    )
    token = r.json()["access_token"]
    r = await client.post(
        "/api/v1/copy-configs/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "exchange_account_id": acc_id,
            "trader_id": trader_id,
            "money_mode": "fixed",
            "money_param": {"amount": 50.0},
        },
    )
    assert r.status_code == 404
    assert r.json()["code"] == "account_not_found"
