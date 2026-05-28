"""Realtime endpoints.

- POST /internal/notify  — execution_engine pushes events (notification + position update)
- WS   /ws/positions    — frontend subscribes for live position / order updates
- WS   /ws/notifications — frontend subscribes for in-app toasts
"""
from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.config import get_settings
from app.core.security import decode_token

log = logging.getLogger(__name__)
router = APIRouter()


# ───────────────────────────────────────────────────────────────────────
# In-process pub/sub hub
# (Production should swap to Redis pub/sub for multi-worker fanout.)
# ───────────────────────────────────────────────────────────────────────
class Hub:
    def __init__(self) -> None:
        # user_id -> set of asyncio.Queue (one queue per ws connection)
        self._subs: dict[int, set[asyncio.Queue]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, user_id: int) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        async with self._lock:
            self._subs[user_id].add(q)
        return q

    async def unsubscribe(self, user_id: int, q: asyncio.Queue) -> None:
        async with self._lock:
            self._subs[user_id].discard(q)
            if not self._subs[user_id]:
                del self._subs[user_id]

    async def publish(self, user_id: int, event: dict[str, Any]) -> int:
        delivered = 0
        async with self._lock:
            queues = list(self._subs.get(user_id, ()))
        for q in queues:
            try:
                q.put_nowait(event)
                delivered += 1
            except asyncio.QueueFull:
                pass  # drop on overflow — better than blocking the publisher
        return delivered


hub = Hub()


# ───────────────────────────────────────────────────────────────────────
# Internal endpoint (execution_engine → backend)
# ───────────────────────────────────────────────────────────────────────
class InternalNotify(BaseModel):
    user_id: int
    type: str  # open_ok / open_fail / risk / tp_sl / margin_change / position_update
    channels: list[str] = Field(default_factory=list)  # ['tg','email','wechat','sms']
    payload: dict[str, Any] = Field(default_factory=dict)


def _require_internal_token(x_internal_token: str | None = Header(default=None)) -> None:
    settings = get_settings()
    expected = settings.internal_token
    if not expected:
        # If unset, treat as misconfiguration and refuse rather than open up.
        raise HTTPException(status_code=503, detail="internal_token not configured")
    if x_internal_token != expected:
        raise HTTPException(status_code=401, detail="invalid internal token")


@router.post("/internal/notify", dependencies=[Depends(_require_internal_token)])
async def internal_notify(body: InternalNotify) -> dict[str, Any]:
    delivered = await hub.publish(
        body.user_id,
        {"type": body.type, "channels": body.channels, "payload": body.payload},
    )
    # TODO: persist into notifications_log + dispatch to TG/email per body.channels
    return {"delivered": delivered}


# ───────────────────────────────────────────────────────────────────────
# WebSocket endpoints
# ───────────────────────────────────────────────────────────────────────
async def _ws_auth(ws: WebSocket) -> int:
    """Authenticate WS via ?token= query param.

    Closes the socket with 4401 if invalid.
    """
    token = ws.query_params.get("token")
    if not token:
        await ws.close(code=4401)
        raise WebSocketDisconnect(code=4401)
    try:
        payload = decode_token(token)
        return int(payload["sub"])
    except Exception:  # noqa: BLE001
        await ws.close(code=4401)
        raise WebSocketDisconnect(code=4401)


async def _ws_stream(ws: WebSocket, channel_filter: set[str] | None = None) -> None:
    user_id = await _ws_auth(ws)
    await ws.accept()
    q = await hub.subscribe(user_id)
    try:
        await ws.send_json({"type": "hello", "user_id": user_id})
        # heartbeat task to keep proxies alive + detect dead connections
        async def _heartbeat():
            while True:
                await asyncio.sleep(20)
                await ws.send_json({"type": "ping"})

        hb = asyncio.create_task(_heartbeat())
        try:
            while True:
                event = await q.get()
                if channel_filter and event.get("type") not in channel_filter:
                    continue
                await ws.send_json(event)
        finally:
            hb.cancel()
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # noqa: BLE001
        log.warning("ws stream error user_id=%s: %s", user_id, exc)
    finally:
        await hub.unsubscribe(user_id, q)


@router.websocket("/ws/positions")
async def ws_positions(ws: WebSocket) -> None:
    await _ws_stream(ws, channel_filter={"position_update", "open_ok", "open_fail", "tp_sl"})


@router.websocket("/ws/notifications")
async def ws_notifications(ws: WebSocket) -> None:
    await _ws_stream(ws, channel_filter=None)  # all event types
