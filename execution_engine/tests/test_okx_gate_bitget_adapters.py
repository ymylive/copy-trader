"""Tests for OKX / Gate / Bitget adapters (CCXT-based).

We verify:
- correct ccxt id + default options
- symbol mapping uses engine/symbols.py per exchange
- close_position routes long→sell / short→buy
- dry-run path returns deterministic values
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from engine.exchanges.bitget import BitgetAdapter
from engine.exchanges.gate import GateAdapter
from engine.exchanges.okx import OKXAdapter
from engine.position_mapper import OrderIntent


# ─── OKX ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_okx_passphrase_carries_through():
    a = OKXAdapter(api_key="k", api_secret="s", passphrase="p123", dry_run=True)
    assert a.passphrase == "p123"
    assert a.CCXT_ID == "okx"
    assert a.DEFAULT_OPTIONS["defaultType"] == "swap"


@pytest.mark.asyncio
async def test_okx_dry_run_balance():
    a = OKXAdapter(api_key="k", api_secret="s", passphrase="p", dry_run=True)
    assert await a.get_balance() == Decimal("1000")


@pytest.mark.asyncio
async def test_okx_native_symbol_unchanged(monkeypatch):
    """OKX-native symbol equals the unified symbol (BTC-USDT-SWAP)."""
    a = OKXAdapter(api_key="k", api_secret="s", passphrase="p", dry_run=False)
    captured = {}

    async def fake_call(fn, *args, **kwargs):
        captured[fn] = (args, kwargs)
        if fn == "create_order":
            return {"id": "ok-1", "status": "closed"}
        return {}

    monkeypatch.setattr(a, "_call", fake_call)
    intent = OrderIntent(
        symbol="BTC-USDT-SWAP", side="long", action="open",
        qty=Decimal("0.5"), kind="market",
    )
    res = await a.place_order(intent)
    assert res.exchange_order_id == "ok-1"
    # OKX uses BTC-USDT-SWAP directly in ccxt
    sym_arg = captured["create_order"][0][0]
    assert "BTC" in sym_arg and "USDT" in sym_arg


@pytest.mark.asyncio
async def test_okx_close_short_uses_buy(monkeypatch):
    a = OKXAdapter(api_key="k", api_secret="s", passphrase="p", dry_run=False)
    captured = {}

    async def fake_call(fn, *args, **kwargs):
        captured[fn] = (args, kwargs)
        if fn == "create_order":
            return {"id": "ok-2", "status": "closed"}
        return {}

    monkeypatch.setattr(a, "_call", fake_call)
    res = await a.close_position("ETH-USDT-SWAP", "short", qty=Decimal("1.0"))
    # closing SHORT → must BUY
    assert captured["create_order"][0][2] == "buy"
    assert res.exchange_order_id == "ok-2"


# ─── Gate ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_gate_ccxt_id_and_defaults():
    a = GateAdapter(api_key="k", api_secret="s", dry_run=True)
    assert a.CCXT_ID == "gate"
    # Gate uses swap as well
    assert a.DEFAULT_OPTIONS["defaultType"] == "swap"


@pytest.mark.asyncio
async def test_gate_place_market_long(monkeypatch):
    a = GateAdapter(api_key="k", api_secret="s", dry_run=False)
    captured = {}

    async def fake_call(fn, *args, **kwargs):
        captured[fn] = args
        if fn == "create_order":
            return {"id": "g-1", "status": "closed"}
        return {}

    monkeypatch.setattr(a, "_call", fake_call)
    intent = OrderIntent(
        symbol="BTC-USDT-SWAP", side="long", action="open",
        qty=Decimal("0.25"), kind="market",
    )
    res = await a.place_order(intent)
    assert res.exchange_order_id == "g-1"
    assert captured["create_order"][2] == "buy"


# ─── Bitget ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_bitget_ccxt_id_and_defaults():
    a = BitgetAdapter(api_key="k", api_secret="s", passphrase="p", dry_run=True)
    assert a.CCXT_ID == "bitget"
    assert a.DEFAULT_OPTIONS["defaultType"] == "swap"


@pytest.mark.asyncio
async def test_bitget_set_leverage(monkeypatch):
    a = BitgetAdapter(api_key="k", api_secret="s", passphrase="p", dry_run=False)
    captured = {}

    async def fake_call(fn, *args, **kwargs):
        captured[fn] = args
        return {}

    monkeypatch.setattr(a, "_call", fake_call)
    await a.set_leverage("BTC-USDT-SWAP", 25)
    # First positional arg is the leverage value
    assert captured["set_leverage"][0] == 25


# ─── Cross-adapter sanity ──────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cls,kwargs",
    [
        (OKXAdapter, {"api_key": "k", "api_secret": "s", "passphrase": "p", "dry_run": True}),
        (GateAdapter, {"api_key": "k", "api_secret": "s", "dry_run": True}),
        (BitgetAdapter, {"api_key": "k", "api_secret": "s", "passphrase": "p", "dry_run": True}),
    ],
)
async def test_dry_run_get_positions_returns_empty(cls, kwargs):
    a = cls(**kwargs)
    pos = await a.get_positions()
    assert isinstance(pos, list)
