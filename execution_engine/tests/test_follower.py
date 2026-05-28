"""End-to-end FollowerRunner test using fakeredis + in-memory SQLite.

We stand up the full pipeline:
    fakeredis stream → FollowerRunner → dry-run adapter → copy_orders row

This is a smoke / integration test more than a strict unit test.
"""
from __future__ import annotations

import asyncio
import json
from decimal import Decimal
from typing import Any

import fakeredis.aioredis  # type: ignore
import pytest
from sqlalchemy import select

from engine.db import (
    drop_db_for_tests,
    get_engine,
    init_db_for_tests,
    reset_engine_for_tests,
    session_scope,
)
from engine.events import SignalEvent
from engine.exchanges.base import OrderResult, Position
from engine.follower import FollowerEngine, FollowerRunner, _RunnerCtx
from engine.models import CopyConfig, CopyOrder, ExchangeAccount, Trader
from engine.notifier import Notifier
from engine.position_mapper import MapperConfig, PositionMapper
from engine.risk import RiskGuard
from engine.secrets import encrypt_secret


@pytest.fixture(autouse=True)
async def _db():
    """Fresh in-memory DB per test."""
    reset_engine_for_tests()
    await init_db_for_tests()
    yield
    try:
        await drop_db_for_tests()
    except Exception:  # noqa: BLE001
        pass
    eng = get_engine()
    await eng.dispose()
    reset_engine_for_tests()


class _StubAdapter:
    """Minimal in-memory adapter that records intents."""

    name = "binance"

    def __init__(self) -> None:
        self.placed: list[Any] = []

    async def set_leverage(self, symbol: str, leverage: int) -> None:
        return None

    async def set_dual_position_mode(self, on: bool) -> None:
        return None

    async def get_balance(self) -> Decimal:
        return Decimal("1000")

    async def get_total_assets(self) -> Decimal:
        return Decimal("1200")

    async def get_positions(self) -> list[Position]:
        return []

    async def place_order(self, intent: Any) -> OrderResult:
        self.placed.append(intent)
        return OrderResult(
            exchange_order_id=f"stub-{len(self.placed)}",
            symbol=intent.symbol,
            side=intent.side,
            qty=intent.qty,
            px=intent.px,
            status="filled",
        )

    async def cancel_order(self, order_id: str, symbol: str) -> None:
        return None

    async def close_position(self, symbol, side, qty=None) -> OrderResult:
        return OrderResult(
            exchange_order_id="stub-close",
            symbol=symbol,
            side=side,
            qty=qty or Decimal("0"),
            px=None,
            status="closed",
        )

    async def get_mark_price(self, symbol: str) -> Decimal:
        return Decimal("65000")

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_runner_consumes_signal_and_writes_copy_order():
    redis = fakeredis.aioredis.FakeRedis(decode_responses=False)
    adapter = _StubAdapter()

    # seed PG: trader + exchange_account + copy_config
    async with session_scope() as ses:
        trader = Trader(source="binance_lead", external_id="42", display_name="x")
        acct = ExchangeAccount(
            user_id=1,
            alias="acct1",
            exchange="binance",
            status="active",
            api_key_enc=encrypt_secret("k"),
            api_secret_enc=encrypt_secret("s"),
        )
        ses.add_all([trader, acct])
        await ses.commit()
        await ses.refresh(trader)
        await ses.refresh(acct)
        cfg = CopyConfig(
            user_id=1,
            exchange_account_id=acct.id,
            trader_id=trader.id,
            money_mode="fixed",
            money_param={"amount": "100"},
            multiplier=Decimal("1"),
            initial_strategy="none",
            direction_limit="both",
            open_trigger={"kind": "market"},
            add_trigger={"kind": "market"},
            tp={},
            sl={},
            loss_threshold={},
            safety_cushion={},
            refill={},
            status="running",
        )
        ses.add(cfg)
        await ses.commit()
        await ses.refresh(cfg)
        cfg_id = cfg.id
        trader_ext = trader.external_id
        acct_id = acct.id

    mc = MapperConfig(
        id=cfg_id,
        user_id=1,
        exchange_account_id=acct_id,
        trader_id=trader.id,
        money_mode="fixed",
        money_param={"amount": "100"},
        multiplier=Decimal("1"),
        initial_strategy="none",
        direction_limit="both",
        open_trigger={"kind": "market"},
        add_trigger={"kind": "market"},
    )
    ctx = _RunnerCtx(
        config_id=cfg_id,
        exchange_account_id=acct_id,
        trader_id=trader.id,
        source="binance_lead",
        external_trader_id=trader_ext,
        exchange="binance",
        api_key="k",
        api_secret="s",
        passphrase=None,
        user_id=1,
        mapper_cfg=mc,
    )
    runner = FollowerRunner(
        ctx=ctx,
        redis=redis,
        adapter=adapter,             # type: ignore[arg-type]
        mapper=PositionMapper(),
        risk=RiskGuard(),
        notifier=Notifier(),
        global_sema=asyncio.Semaphore(10),
    )

    # publish a signal directly to the stream
    event = SignalEvent(
        schema="signal.v1",
        event_id="evt-test-1",
        source="binance_lead",
        trader_id=trader_ext,
        ts=0,
        kind="order_open",
        payload={
            "symbol": "BTC-USDT-SWAP",
            "side": "long",
            "action": "open",
            "qty_delta": "1",
            "px": "65000",
        },
    )
    await redis.xadd(
        runner.stream_key,
        {"data": event.model_dump_json(by_alias=True)},
    )

    runner.start()
    # give the loop time to process
    for _ in range(50):
        if adapter.placed:
            break
        await asyncio.sleep(0.05)
    await runner.stop()
    await redis.aclose()

    assert adapter.placed, "expected at least one order to be placed"
    assert adapter.placed[0].symbol == "BTC-USDT-SWAP"
    assert adapter.placed[0].side == "long"
    # qty = 100 / 65000
    assert adapter.placed[0].qty == Decimal("100") / Decimal("65000")

    # ensure copy_orders row created
    async with session_scope() as ses:
        rows = (
            await ses.execute(select(CopyOrder).where(CopyOrder.copy_config_id == cfg_id))
        ).scalars().all()
        assert rows
        assert rows[0].status in ("filled", "open", "closed")


@pytest.mark.asyncio
async def test_engine_starts_with_no_configs():
    """The engine must NOT crash when no traders are configured."""
    eng = FollowerEngine()
    try:
        await eng.start()
        await asyncio.sleep(0.05)
        assert eng.runners == {}
    finally:
        await eng.stop()


@pytest.mark.asyncio
async def test_runner_idempotency_dedups_by_event_id():
    """Two identical signals must produce only one copy_orders row."""
    redis = fakeredis.aioredis.FakeRedis(decode_responses=False)
    adapter = _StubAdapter()

    async with session_scope() as ses:
        trader = Trader(source="okx_public", external_id="abc")
        acct = ExchangeAccount(
            user_id=1,
            alias="acct1",
            exchange="binance",
            status="active",
            api_key_enc=encrypt_secret("k"),
            api_secret_enc=encrypt_secret("s"),
        )
        ses.add_all([trader, acct])
        await ses.commit()
        await ses.refresh(trader)
        await ses.refresh(acct)
        cfg = CopyConfig(
            user_id=1,
            exchange_account_id=acct.id,
            trader_id=trader.id,
            money_mode="fixed",
            money_param={"amount": "100"},
            status="running",
        )
        ses.add(cfg)
        await ses.commit()
        await ses.refresh(cfg)
        ctx_args = dict(
            config_id=cfg.id,
            exchange_account_id=acct.id,
            trader_id=trader.id,
            source=trader.source,
            external_trader_id=trader.external_id,
        )
    mc = MapperConfig(
        id=ctx_args["config_id"],
        user_id=1,
        exchange_account_id=ctx_args["exchange_account_id"],
        trader_id=ctx_args["trader_id"],
        money_mode="fixed",
        money_param={"amount": "100"},
    )
    ctx = _RunnerCtx(
        **ctx_args,
        exchange="binance",
        api_key="k",
        api_secret="s",
        passphrase=None,
        user_id=1,
        mapper_cfg=mc,
    )
    runner = FollowerRunner(
        ctx=ctx,
        redis=redis,
        adapter=adapter,                # type: ignore[arg-type]
        mapper=PositionMapper(),
        risk=RiskGuard(),
        notifier=Notifier(),
        global_sema=asyncio.Semaphore(10),
    )

    event_json = json.dumps(
        {
            "schema": "signal.v1",
            "event_id": "dup-1",
            "source": "okx_public",
            "trader_id": "abc",
            "ts": 0,
            "kind": "order_open",
            "payload": {
                "symbol": "BTC-USDT-SWAP",
                "side": "long",
                "action": "open",
                "qty_delta": "1",
                "px": "65000",
            },
        }
    )
    # publish twice with the same event_id
    await redis.xadd(runner.stream_key, {"data": event_json})
    await redis.xadd(runner.stream_key, {"data": event_json})

    runner.start()
    for _ in range(50):
        if len(adapter.placed) >= 1:
            break
        await asyncio.sleep(0.05)
    # let it try the second one
    await asyncio.sleep(0.3)
    await runner.stop()
    await redis.aclose()

    # only one order placed (idempotency)
    assert len(adapter.placed) == 1
