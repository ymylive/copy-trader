"""Tests for Hyperliquid adapter (dry-run + mocked SDK) and Notifier (respx)."""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
import respx
from httpx import Response

from engine.exchanges.base import AuthError, InsufficientBalance
from engine.exchanges.hyperliquid import HyperliquidAdapter
from engine.notifier import Notifier
from engine.position_mapper import OrderIntent


# ─── Hyperliquid · dry-run fallbacks ──────────────────────────────────


@pytest.mark.asyncio
async def test_hl_dry_run_balance_default():
    a = HyperliquidAdapter(dry_run=True)
    assert await a.get_balance() == Decimal("1000")
    assert await a.get_total_assets() == Decimal("1000")


@pytest.mark.asyncio
async def test_hl_dry_run_get_positions_returns_empty():
    a = HyperliquidAdapter(dry_run=True)
    assert await a.get_positions() == []


@pytest.mark.asyncio
async def test_hl_dry_run_place_order_returns_stub():
    a = HyperliquidAdapter(dry_run=True)
    intent = OrderIntent(
        symbol="BTC-USD-SWAP", side="long", action="open",
        qty=Decimal("0.5"), kind="market",
    )
    res = await a.place_order(intent)
    assert res.exchange_order_id.startswith("hl-dryrun")
    assert res.symbol == "BTC-USD-SWAP"


@pytest.mark.asyncio
async def test_hl_no_key_raises_on_private_action(monkeypatch):
    """Without a private key, the exchange property should raise AuthError."""
    a = HyperliquidAdapter(wallet_address="0xabc", dry_run=False)
    # Stub _init_sdk to return (info, None) — i.e., no Exchange (no key)
    monkeypatch.setattr(a, "_init_sdk", lambda: (MagicMock(), None))

    with pytest.raises(AuthError):
        _ = a.exchange


@pytest.mark.asyncio
async def test_hl_set_dual_position_mode_is_noop():
    """Hyperliquid is one-way only — should not raise."""
    a = HyperliquidAdapter(dry_run=True)
    await a.set_dual_position_mode(True)
    await a.set_dual_position_mode(False)


@pytest.mark.asyncio
async def test_hl_get_positions_parses_real_payload(monkeypatch):
    """When user_state returns a real-shape payload, get_positions transforms it correctly."""
    a = HyperliquidAdapter(wallet_address="0xabcdef", dry_run=False)

    fake_state = {
        "crossMarginSummary": {"accountValue": "1234.56", "totalMarginUsed": "200.00"},
        "assetPositions": [
            {
                "position": {
                    "coin": "BTC",
                    "szi": "0.1",            # > 0 → long
                    "entryPx": "65000",
                    "leverage": {"value": "10"},
                    "marginUsed": "650",
                    "unrealizedPnl": "12.5",
                }
            },
            {
                "position": {
                    "coin": "ETH",
                    "szi": "-2.0",           # < 0 → short
                    "entryPx": "3300",
                    "leverage": {"value": "5"},
                    "marginUsed": "1320",
                    "unrealizedPnl": "-30.0",
                }
            },
            # zero-size position must be filtered out
            {"position": {"coin": "SOL", "szi": "0", "entryPx": "0"}},
        ],
    }

    async def fake_run(fn, *args, **kwargs):
        return fake_state

    monkeypatch.setattr(a, "_run", fake_run)
    monkeypatch.setattr(a, "_init_sdk", lambda: (MagicMock(), MagicMock()))

    positions = await a.get_positions()
    assert len(positions) == 2
    btc, eth = positions
    assert btc.side == "long" and btc.qty == Decimal("0.1")
    assert btc.entry_px == Decimal("65000")
    assert eth.side == "short" and eth.qty == Decimal("2.0")
    assert eth.unrealized_pnl == Decimal("-30.0")


@pytest.mark.asyncio
async def test_hl_get_balance_subtracts_used_margin(monkeypatch):
    a = HyperliquidAdapter(wallet_address="0xabcdef", dry_run=False)

    async def fake_run(fn, *args, **kwargs):
        return {"crossMarginSummary": {"accountValue": "5000", "totalMarginUsed": "800"}}

    monkeypatch.setattr(a, "_run", fake_run)
    monkeypatch.setattr(a, "_init_sdk", lambda: (MagicMock(), MagicMock()))

    free = await a.get_balance()
    assert free == Decimal("4200")


# ─── Notifier · HTTP push to backend internal endpoint ─────────────────


@pytest.mark.asyncio
@respx.mock
async def test_notifier_sends_internal_token_header():
    url = "http://backend.local/api/v1/internal/notify"
    route = respx.post(url).mock(return_value=Response(200, json={"delivered": 1}))

    n = Notifier(url=url, token="t0psekret")
    ok = await n.notify(
        user_id=42, notify_type="open_ok", channels=["tg"],
        payload={"symbol": "BTC-USDT-SWAP", "qty": "0.5"},
    )
    await n.close()

    assert ok is True
    assert route.called
    req = route.calls[0].request
    assert req.headers["x-internal-token"] == "t0psekret"
    body = req.read()
    assert b"open_ok" in body
    assert b"\"user_id\":42" in body or b'"user_id": 42' in body


@pytest.mark.asyncio
@respx.mock
async def test_notifier_returns_false_on_500():
    url = "http://backend.local/api/v1/internal/notify"
    respx.post(url).mock(return_value=Response(500))

    n = Notifier(url=url, token="t")
    ok = await n.notify(
        user_id=1, notify_type="risk", channels=[], payload={"reason": "loss"},
    )
    await n.close()
    assert ok is False


@pytest.mark.asyncio
@respx.mock
async def test_notifier_returns_false_on_network_error():
    url = "http://backend.unreachable/api/v1/internal/notify"
    respx.post(url).mock(side_effect=Exception("conn refused"))

    n = Notifier(url=url, token="t")
    ok = await n.notify(
        user_id=1, notify_type="margin_change", channels=[], payload={},
    )
    await n.close()
    assert ok is False


@pytest.mark.asyncio
@respx.mock
async def test_notifier_payload_includes_all_fields():
    url = "http://backend.local/api/v1/internal/notify"
    route = respx.post(url).mock(return_value=Response(200, json={"delivered": 2}))

    n = Notifier(url=url, token="abc")
    await n.notify(
        user_id=7, notify_type="tp_sl", channels=["email", "tg"],
        payload={"action": "partial_close", "qty_pct": 50},
    )
    await n.close()

    body = route.calls[0].request.read().decode()
    for needle in ("\"user_id\"", "\"type\"", "\"tp_sl\"", "email", "tg", "partial_close"):
        assert needle in body
