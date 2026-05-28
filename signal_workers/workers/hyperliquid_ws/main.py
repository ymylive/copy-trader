"""Hyperliquid real-time WebSocket worker.

Design summary
--------------
* Reads target addresses from PG ``traders`` table where ``source='hyperliquid'``.
* Connects to ``wss://api.hyperliquid.xyz/ws``.
* Per address subscribes to three channels in parallel:

  - ``userEvents``  — fills + liquidation + funding
  - ``userFills``   — snapshot + fills (redundant with userEvents for fills but
    gives us an ``isSnapshot`` cold-start frame)
  - ``webData2``    — aggregate state used for ``position_snapshot`` emission

* Each connection holds at most :data:`MAX_SUBS_PER_CONN` (=300) address-channel
  subscriptions; we shard transparently with a list of :class:`HLConnection`.
* Reconnect with exponential backoff up to :data:`MAX_BACKOFF_SEC` and emit
  ``WS_RECONNECTS_TOTAL``.
* Trader list refresh every 60 s — diff vs current shard map and add/remove
  subscriptions on the fly.
* Optional ``positions_snapshots`` write-back (gated by env
  ``WRITE_POSITION_SNAPSHOTS``) — disabled by default so a fresh deployment
  without DB does not crash.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import random
from typing import Any

import orjson
import structlog
import websockets
from websockets.client import WebSocketClientProtocol

from signal_workers.common.event_bus import EventBus
from signal_workers.common.metrics import (
    WS_ACTIVE_CONNECTIONS,
    WS_RECONNECTS_TOTAL,
    WS_SUBSCRIPTIONS,
)
from signal_workers.common.redis_helper import get_redis
from signal_workers.common.trader_registry import TraderRegistry

from .parser import (
    parse_user_events_frame,
    parse_user_fill,
    parse_web_data2,
)

log = structlog.get_logger(__name__)

HL_WS_URL = os.environ.get("HL_WS_URL", "wss://api.hyperliquid.xyz/ws")
MAX_SUBS_PER_CONN = 300  # spec: ≤300 channel-subscriptions per connection
RECONNECT_DELAY_BASE = 1.0  # seconds
MAX_BACKOFF_SEC = 30.0
REGISTRY_REFRESH_SEC = 60
PING_INTERVAL_SEC = 30


class HLConnection:
    """One physical WebSocket carrying up to ``MAX_SUBS_PER_CONN`` subs."""

    def __init__(self, idx: int, bus: EventBus, registry: TraderRegistry) -> None:
        self.idx = idx
        self.bus = bus
        self.registry = registry
        self.addresses: set[str] = set()  # user addresses we currently subscribe
        self._ws: WebSocketClientProtocol | None = None
        self._lock = asyncio.Lock()
        self._stop = asyncio.Event()

    # ------------------------------------------------------------------
    # Public mutation API
    # ------------------------------------------------------------------
    async def add_address(self, addr: str) -> None:
        if addr in self.addresses:
            return
        self.addresses.add(addr)
        WS_SUBSCRIPTIONS.labels(source="hyperliquid").set(len(self.addresses) * 3)
        if self._ws is not None and not self._ws.closed:
            await self._send_subscribe(addr)

    async def remove_address(self, addr: str) -> None:
        if addr not in self.addresses:
            return
        self.addresses.discard(addr)
        WS_SUBSCRIPTIONS.labels(source="hyperliquid").set(len(self.addresses) * 3)
        if self._ws is not None and not self._ws.closed:
            for ch in ("userEvents", "userFills", "webData2"):
                msg = {
                    "method": "unsubscribe",
                    "subscription": {"type": ch, "user": addr},
                }
                try:
                    await self._ws.send(orjson.dumps(msg).decode())
                except Exception as exc:  # noqa: BLE001
                    log.warning("hl.unsub_failed", err=str(exc), addr=addr)

    async def stop(self) -> None:
        self._stop.set()
        if self._ws is not None and not self._ws.closed:
            await self._ws.close()

    # ------------------------------------------------------------------
    # Run loop
    # ------------------------------------------------------------------
    async def run(self) -> None:
        """Connect → subscribe → consume → on-failure reconnect, forever."""
        backoff = RECONNECT_DELAY_BASE
        while not self._stop.is_set():
            try:
                WS_ACTIVE_CONNECTIONS.labels(source="hyperliquid").inc()
                async with websockets.connect(
                    HL_WS_URL,
                    ping_interval=PING_INTERVAL_SEC,
                    ping_timeout=PING_INTERVAL_SEC,
                    close_timeout=5,
                    max_size=2**22,  # 4 MiB; webData2 frames can be big
                ) as ws:
                    self._ws = ws
                    log.info("hl.connected", conn_idx=self.idx, n_addr=len(self.addresses))
                    backoff = RECONNECT_DELAY_BASE
                    # (Re)subscribe everything
                    for addr in list(self.addresses):
                        await self._send_subscribe(addr)
                    # Drain messages
                    async for raw in ws:
                        try:
                            await self._handle_frame(raw)
                        except Exception as exc:  # noqa: BLE001
                            log.exception("hl.frame_handler_failed", err=str(exc))
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                log.warning(
                    "hl.connection_lost",
                    err=str(exc),
                    backoff=backoff,
                    conn_idx=self.idx,
                )
                WS_RECONNECTS_TOTAL.labels(source="hyperliquid", endpoint="ws").inc()
            finally:
                WS_ACTIVE_CONNECTIONS.labels(source="hyperliquid").dec()
                self._ws = None

            if self._stop.is_set():
                break

            # exponential backoff + jitter
            jitter = random.uniform(0, backoff * 0.2)
            await asyncio.sleep(backoff + jitter)
            backoff = min(MAX_BACKOFF_SEC, backoff * 2)

    async def _send_subscribe(self, addr: str) -> None:
        assert self._ws is not None
        for ch in ("userEvents", "userFills", "webData2"):
            msg = {"method": "subscribe", "subscription": {"type": ch, "user": addr}}
            await self._ws.send(orjson.dumps(msg).decode())
        log.debug("hl.subscribed", addr=addr, conn_idx=self.idx)

    async def _handle_frame(self, raw: bytes | str) -> None:
        try:
            frame = orjson.loads(raw)
        except orjson.JSONDecodeError:
            return

        channel = frame.get("channel")
        if not channel:
            return

        if channel == "subscriptionResponse":
            return  # ack, ignore
        if channel == "pong":
            return

        # Hyperliquid embeds the user address inside frame["data"]["user"]
        # for user-* subscriptions.
        data = frame.get("data") or {}
        addr: str | None = None
        if isinstance(data, dict):
            addr = data.get("user")
        if addr is None:
            # Some channels nest one more level.
            inner = data.get("data") if isinstance(data, dict) else None
            if isinstance(inner, dict):
                addr = inner.get("user")
        if addr is None:
            return

        if channel == "userEvents":
            for ev in parse_user_events_frame(frame, trader_id=addr):
                await self.bus.publish(ev)
        elif channel == "userFills":
            fills = (data or {}).get("fills") or []
            for f in fills:
                ev = parse_user_fill(f, trader_id=addr)
                if ev is not None:
                    await self.bus.publish(ev)
        elif channel == "webData2":
            ev = parse_web_data2(frame, trader_id=addr)
            if ev is not None:
                await self.bus.publish(ev)
                # Optional DB write-back. Without exchange_account_id we cannot
                # populate the column, so we skip if disabled.
                if os.environ.get("WRITE_POSITION_SNAPSHOTS") == "1":
                    for row in ev.payload.get("positions", []):
                        try:
                            await self.registry.write_position_snapshot(
                                exchange_account_id=0,  # 0 = "unknown / no account binding"
                                symbol=row["symbol"],
                                side=row["side"],
                                qty=row["qty"],
                                entry_px=row["entry_px"],
                                lev=row["lev"],
                                margin=row["margin"],
                                unrealized_pnl=row["unrealized_pnl"],
                                ts_ms=ev.ts,
                            )
                        except Exception as exc:  # noqa: BLE001
                            log.debug("hl.snapshot_write_failed", err=str(exc))


# ---------------------------------------------------------------------------
# Sharder — maps address -> connection
# ---------------------------------------------------------------------------
class ShardedHL:
    def __init__(self, bus: EventBus, registry: TraderRegistry) -> None:
        self.bus = bus
        self.registry = registry
        self.conns: list[HLConnection] = []
        self.addr_to_conn: dict[str, int] = {}
        self._tasks: list[asyncio.Task] = []

    async def reconcile(self, target_addrs: set[str]) -> None:
        """Bring the live subscription set in line with the target set."""
        current = set(self.addr_to_conn)
        to_add = target_addrs - current
        to_remove = current - target_addrs

        for addr in to_remove:
            idx = self.addr_to_conn.pop(addr)
            await self.conns[idx].remove_address(addr)

        for addr in to_add:
            # Find connection with capacity
            target_conn: HLConnection | None = None
            for c in self.conns:
                if len(c.addresses) < MAX_SUBS_PER_CONN:
                    target_conn = c
                    break
            if target_conn is None:
                # Spin up a new connection
                target_conn = HLConnection(len(self.conns), self.bus, self.registry)
                self.conns.append(target_conn)
                self._tasks.append(
                    asyncio.create_task(
                        target_conn.run(),
                        name=f"hl.conn.{target_conn.idx}",
                    )
                )
            await target_conn.add_address(addr)
            self.addr_to_conn[addr] = target_conn.idx

        if to_add or to_remove:
            log.info(
                "hl.reconciled",
                added=len(to_add),
                removed=len(to_remove),
                total=len(self.addr_to_conn),
                conns=len(self.conns),
            )

    async def stop_all(self) -> None:
        for c in self.conns:
            await c.stop()
        for t in self._tasks:
            t.cancel()
        for t in self._tasks:
            try:
                await t
            except (asyncio.CancelledError, Exception):
                pass


# ---------------------------------------------------------------------------
# Worker entry-point
# ---------------------------------------------------------------------------
async def run(args: argparse.Namespace) -> None:
    stop_event: asyncio.Event = getattr(args, "stop_event", asyncio.Event())

    redis_client = await get_redis(args.redis_url, dry_run=args.dry_run)
    bus = EventBus(redis_client)
    registry = TraderRegistry(dsn=args.database_url, source_filter="hyperliquid")

    sharder = ShardedHL(bus, registry)

    async def _refresh_loop() -> None:
        while not stop_event.is_set():
            try:
                rows = await registry.refresh()
                target = {r.external_id for r in rows}
                await sharder.reconcile(target)
            except Exception as exc:  # noqa: BLE001
                log.warning("hl.refresh_failed", err=str(exc))
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=REGISTRY_REFRESH_SEC)
            except asyncio.TimeoutError:
                pass

    refresh_task = asyncio.create_task(_refresh_loop(), name="hl.refresh")

    try:
        await stop_event.wait()
    finally:
        log.info("hl.shutting_down")
        refresh_task.cancel()
        try:
            await refresh_task
        except (asyncio.CancelledError, Exception):
            pass
        await sharder.stop_all()
        await bus.aclose()
        await registry.aclose()
