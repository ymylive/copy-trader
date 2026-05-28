"""Tests for /internal/notify HTTP endpoint and WS hub fanout."""
from __future__ import annotations

import asyncio
import pytest
from httpx import AsyncClient

from app.api.v1.realtime import hub
from app.config import get_settings


@pytest.mark.asyncio
async def test_internal_notify_requires_token(client: AsyncClient):
    """Missing X-Internal-Token → 401."""
    r = await client.post(
        "/api/v1/internal/notify",
        json={"user_id": 1, "type": "open_ok", "payload": {}},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_internal_notify_publishes_to_hub(client: AsyncClient):
    settings = get_settings()
    user_id = 12345
    # Subscribe a dummy queue
    q = await hub.subscribe(user_id)
    try:
        r = await client.post(
            "/api/v1/internal/notify",
            headers={"X-Internal-Token": settings.internal_token},
            json={
                "user_id": user_id,
                "type": "open_ok",
                "channels": ["tg"],
                "payload": {"symbol": "BTC-USDT-SWAP", "qty": "0.1"},
            },
        )
        assert r.status_code == 200
        assert r.json()["delivered"] == 1

        # Should have delivered the event into our subscribed queue
        event = await asyncio.wait_for(q.get(), timeout=1.0)
        assert event["type"] == "open_ok"
        assert event["payload"]["symbol"] == "BTC-USDT-SWAP"
    finally:
        await hub.unsubscribe(user_id, q)


@pytest.mark.asyncio
async def test_hub_publish_with_no_subscribers_does_not_error():
    delivered = await hub.publish(99999, {"type": "tp_sl", "payload": {}})
    assert delivered == 0


@pytest.mark.asyncio
async def test_hub_overflow_drops_silently():
    """Slow consumers don't block the publisher."""
    q = await hub.subscribe(424242)
    try:
        # Hub queue maxsize is 200 — fire 250 events
        for i in range(250):
            await hub.publish(424242, {"type": "tp_sl", "payload": {"i": i}})
        # The queue should be full but the publisher never blocked
        assert q.qsize() <= 200
    finally:
        await hub.unsubscribe(424242, q)
