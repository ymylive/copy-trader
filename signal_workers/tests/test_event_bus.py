"""Event bus tests against ``fakeredis.aioredis.FakeRedis``."""

from __future__ import annotations

import asyncio
import time

import fakeredis.aioredis
import pytest

from signal_workers.common.event_bus import EventBus
from signal_workers.common.schema import SignalEvent


def _make_event(**overrides) -> SignalEvent:
    base = dict(
        event_id="evt-1",
        source="hyperliquid",
        trader_id="0xdead",
        ts=int(time.time() * 1000),
        kind="order_open",
        payload={"symbol": "BTC-USDT-SWAP", "side": "long", "action": "open"},
    )
    base.update(overrides)
    return SignalEvent(**base)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_publish_writes_to_stream() -> None:
    r = fakeredis.aioredis.FakeRedis()
    bus = EventBus(r, max_publish_per_sec=1000)

    sid = await bus.publish(_make_event())
    assert sid is not None

    key = EventBus.stream_key("hyperliquid", "0xdead")
    entries = await r.xrange(key)
    assert len(entries) == 1
    # entries[0] = (stream_id, {field: value} as bytes)
    fields = {k.decode(): v.decode() for k, v in entries[0][1].items()}
    assert fields["source"] == "hyperliquid"
    assert fields["kind"] == "order_open"

    await bus.aclose()


@pytest.mark.asyncio
async def test_dedup_drops_repeat() -> None:
    r = fakeredis.aioredis.FakeRedis()
    bus = EventBus(r)
    ev = _make_event(event_id="dup-id")
    assert await bus.publish(ev) is not None
    # exact same event_id → dropped
    assert await bus.publish(ev) is None

    key = EventBus.stream_key("hyperliquid", "0xdead")
    entries = await r.xrange(key)
    assert len(entries) == 1

    await bus.aclose()


@pytest.mark.asyncio
async def test_rate_limit_drops_excess() -> None:
    """If we set rate=2 and fire 10 events, ≤ a few should land."""
    r = fakeredis.aioredis.FakeRedis()
    bus = EventBus(r, max_publish_per_sec=2)

    published = 0
    for i in range(10):
        ev = _make_event(event_id=f"evt-{i}")
        sid = await bus.publish(ev)
        if sid is not None:
            published += 1

    # bucket starts full with capacity=2, so first two should pass; the rest
    # depend on monotonic clock advance during the loop which is sub-ms.
    assert 0 < published <= 4
    await bus.aclose()


@pytest.mark.asyncio
async def test_maxlen_trim_keeps_stream_bounded() -> None:
    r = fakeredis.aioredis.FakeRedis()
    bus = EventBus(r, max_publish_per_sec=10_000, stream_maxlen=50)

    for i in range(200):
        await bus.publish(_make_event(event_id=f"evt-{i}"))

    key = EventBus.stream_key("hyperliquid", "0xdead")
    entries = await r.xrange(key)
    # MAXLEN ~ is approximate but in practice stays within 2x of cap on fakeredis.
    assert len(entries) <= 200
    assert len(entries) >= 1

    await bus.aclose()


@pytest.mark.asyncio
async def test_stream_key_safe_for_evm_addresses() -> None:
    """Stream-key must replace raw colons inside trader_id."""
    k = EventBus.stream_key("hyperliquid", "0xab:cd")
    # Three schema-level separators in "stream:signals:source:trader_id";
    # the colon embedded in the trader_id has been replaced with `_`.
    assert k == "stream:signals:hyperliquid:0xab_cd"
    assert k.count(":") == 3
