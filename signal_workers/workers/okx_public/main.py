"""OKX public copytrading polling worker.

Polls these four endpoints (all unauthenticated, see
``research/signal_sources_research.md`` §2.1)::

    /api/v5/copytrading/public-lead-traders
    /api/v5/copytrading/public-current-subpositions
    /api/v5/copytrading/public-subpositions-history
    /api/v5/copytrading/public-stats

Logic
-----
* **Lead-trader discovery** every 60 s: pulls the global lead-trader list and
  upserts new ones into ``traders`` (write-through is left to the backend; we
  surface the list via metrics).
* **Per-trader position diff** every 5 s: pull ``public-current-subpositions``
  for each trader, diff against the previous snapshot, emit ``order_open``
  / ``order_close`` / ``position_snapshot`` events.
* **Stats sync** every 60 s: pull ``public-stats`` and upsert into
  ``traders.stats``.

A single global :class:`~signal_workers.common.ratelimit.TokenBucket`
guards us against OKX's ``20 req/2 s / IP`` cap (we cap ourselves at
``5 req/s`` to leave headroom).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import time
from typing import Any

import aiohttp
import structlog

from signal_workers.common.event_bus import EventBus
from signal_workers.common.metrics import OKX_ACTIVE_TRADERS, OKX_POLLS_TOTAL
from signal_workers.common.ratelimit import TokenBucket
from signal_workers.common.redis_helper import get_redis
from signal_workers.common.trader_registry import TraderRegistry

from .diff import build_snapshot_event, diff_positions

log = structlog.get_logger(__name__)

OKX_BASE = os.environ.get("OKX_BASE_URL", "https://www.okx.com")
ENDPOINT_LEAD_TRADERS = "/api/v5/copytrading/public-lead-traders"
ENDPOINT_CURRENT_POS = "/api/v5/copytrading/public-current-subpositions"
ENDPOINT_HISTORY = "/api/v5/copytrading/public-subpositions-history"
ENDPOINT_STATS = "/api/v5/copytrading/public-stats"

# Tunables ---------------------------------------------------------------
POSITION_POLL_INTERVAL = float(os.environ.get("OKX_POS_POLL_SEC", "5"))
STATS_POLL_INTERVAL = float(os.environ.get("OKX_STATS_POLL_SEC", "60"))
DISCOVERY_INTERVAL = float(os.environ.get("OKX_DISCOVERY_SEC", "60"))
GLOBAL_RATE = float(os.environ.get("OKX_GLOBAL_RPS", "5"))  # 10 req / 2s, we use 5
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)
UA = os.environ.get("OKX_UA", "copy_trader-signal-worker/0.1")

_per_trader_state: dict[str, list[dict[str, Any]]] = {}


# ---------------------------------------------------------------------------
# REST helper
# ---------------------------------------------------------------------------
class OKXClient:
    def __init__(self, session: aiohttp.ClientSession, bucket: TokenBucket) -> None:
        self.session = session
        self.bucket = bucket

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        await self.bucket.acquire(1)
        url = f"{OKX_BASE}{path}"
        status_label = "ok"
        try:
            async with self.session.get(url, params=params or {}, headers={"User-Agent": UA}) as resp:
                if resp.status != 200:
                    status_label = f"http_{resp.status}"
                    log.warning("okx.http_error", path=path, status=resp.status)
                    return None
                data = await resp.json(content_type=None)
                if data.get("code") != "0":
                    status_label = f"okx_{data.get('code')}"
                    log.warning("okx.api_error", path=path, code=data.get("code"), msg=data.get("msg"))
                    return None
                return data
        except aiohttp.ClientError as exc:
            status_label = "network"
            log.warning("okx.network_error", path=path, err=str(exc))
            return None
        except asyncio.TimeoutError:
            status_label = "timeout"
            log.warning("okx.timeout", path=path)
            return None
        finally:
            OKX_POLLS_TOTAL.labels(endpoint=path, status=status_label).inc()

    async def lead_traders(self) -> list[dict[str, Any]]:
        """Page through the public lead-traders list (page size 20)."""
        out: list[dict[str, Any]] = []
        # OKX uses `instType=SWAP` & paginated `page` (1-based).
        page = 1
        while True:
            data = await self._get(
                ENDPOINT_LEAD_TRADERS,
                {"instType": "SWAP", "page": str(page), "limit": "100"},
            )
            if not data:
                break
            rows = data.get("data") or []
            # Some responses wrap data in `{ratings: []}` — accept both.
            if rows and isinstance(rows[0], dict) and "ratings" in rows[0]:
                rows = rows[0].get("ratings") or []
            if not rows:
                break
            out.extend(rows)
            if len(rows) < 100:
                break
            page += 1
            if page > 10:  # safety cap
                break
        return out

    async def current_subpositions(self, unique_code: str) -> list[dict[str, Any]]:
        data = await self._get(
            ENDPOINT_CURRENT_POS,
            {"uniqueCode": unique_code, "instType": "SWAP"},
        )
        if not data:
            return []
        return data.get("data") or []

    async def stats(self, unique_code: str) -> dict[str, Any] | None:
        data = await self._get(ENDPOINT_STATS, {"uniqueCode": unique_code})
        if not data:
            return None
        rows = data.get("data") or []
        return rows[0] if rows else None


# ---------------------------------------------------------------------------
# Per-trader poll loop
# ---------------------------------------------------------------------------
async def _poll_trader(
    *,
    client: OKXClient,
    bus: EventBus,
    unique_code: str,
    trader_name: str | None,
    snapshot_every: int = 12,  # one full snapshot every 12 diff polls (~60s)
    snapshot_counter: dict[str, int] | None = None,
) -> None:
    curr = await client.current_subpositions(unique_code)
    now_ms = int(time.time() * 1000)
    prev = _per_trader_state.get(unique_code)

    # 1) incremental events
    for ev in diff_positions(
        trader_id=unique_code,
        trader_name=trader_name,
        prev=prev,
        curr=curr,
        ts_ms=now_ms,
        received_ts_ms=now_ms,
    ):
        await bus.publish(ev)

    # 2) periodic full snapshot
    if snapshot_counter is not None:
        n = snapshot_counter.get(unique_code, 0) + 1
        snapshot_counter[unique_code] = n
        if n % snapshot_every == 1:
            snap = build_snapshot_event(
                trader_id=unique_code,
                trader_name=trader_name,
                curr=curr,
                ts_ms=now_ms,
                received_ts_ms=now_ms,
            )
            await bus.publish(snap)

    _per_trader_state[unique_code] = curr


# ---------------------------------------------------------------------------
# Worker entry-point
# ---------------------------------------------------------------------------
async def run(args: argparse.Namespace) -> None:
    stop_event: asyncio.Event = getattr(args, "stop_event", asyncio.Event())

    redis_client = await get_redis(args.redis_url, dry_run=args.dry_run)
    bus = EventBus(redis_client)
    registry = TraderRegistry(dsn=args.database_url, source_filter="okx_public")

    bucket = TokenBucket(rate=GLOBAL_RATE, capacity=GLOBAL_RATE * 2)
    session = aiohttp.ClientSession(timeout=REQUEST_TIMEOUT)
    client = OKXClient(session, bucket)

    snapshot_counter: dict[str, int] = {}

    async def _discovery_loop() -> None:
        """Periodically refresh the trader registry from PG *and* OKX."""
        while not stop_event.is_set():
            try:
                # 1) Pull whatever's in PG (might be empty on first deploy).
                await registry.refresh()
                # 2) Top-up from OKX public list (cold-start helper).
                if os.environ.get("OKX_AUTO_DISCOVER", "1") == "1":
                    leaders = await client.lead_traders()
                    log.info("okx.discovered_leaders", count=len(leaders))
                    # We do NOT auto-insert into traders table here — that's
                    # the backend's job to expose via an admin endpoint. We
                    # *do* seed the in-memory registry with them so we can
                    # start polling immediately on a clean DB.
                    from signal_workers.common.trader_registry import TraderRow

                    seeded = [
                        TraderRow(
                            id=-1,
                            source="okx_public",
                            external_id=str(l.get("uniqueCode")),
                            display_name=l.get("nickName"),
                            exchange="okx",
                            meta={"discovered_at": int(time.time())},
                            stats={
                                k: l[k]
                                for k in (
                                    "winRatio",
                                    "pnl",
                                    "roi",
                                    "yieldRatio",
                                    "followerNum",
                                    "leadDays",
                                )
                                if k in l
                            },
                        )
                        for l in leaders
                        if l.get("uniqueCode")
                    ]
                    # Merge: PG rows win, OKX rows fill the rest.
                    existing_codes = {r.external_id for r in registry.snapshot()}
                    merged = registry.snapshot() + [
                        r for r in seeded if r.external_id not in existing_codes
                    ]
                    registry.seed(merged)
            except Exception as exc:  # noqa: BLE001
                log.warning("okx.discovery_failed", err=str(exc))
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=DISCOVERY_INTERVAL)
            except asyncio.TimeoutError:
                pass

    async def _position_loop() -> None:
        while not stop_event.is_set():
            traders = registry.snapshot()
            OKX_ACTIVE_TRADERS.set(len(traders))
            if not traders:
                # Without any traders we MUST NOT crash; we simply wait.
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=POSITION_POLL_INTERVAL)
                except asyncio.TimeoutError:
                    pass
                continue
            # Fire all per-trader polls concurrently; the global TokenBucket
            # serialises them across the OKX rate limit.
            await asyncio.gather(
                *(
                    _poll_trader(
                        client=client,
                        bus=bus,
                        unique_code=t.external_id,
                        trader_name=t.display_name,
                        snapshot_counter=snapshot_counter,
                    )
                    for t in traders
                ),
                return_exceptions=True,
            )
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=POSITION_POLL_INTERVAL)
            except asyncio.TimeoutError:
                pass

    async def _stats_loop() -> None:
        while not stop_event.is_set():
            for t in list(registry.snapshot()):
                try:
                    s = await client.stats(t.external_id)
                    if s:
                        await registry.upsert_stats("okx_public", t.external_id, s)
                except Exception as exc:  # noqa: BLE001
                    log.debug("okx.stats_loop_err", err=str(exc))
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=STATS_POLL_INTERVAL)
            except asyncio.TimeoutError:
                pass

    tasks = [
        asyncio.create_task(_discovery_loop(), name="okx.discovery"),
        asyncio.create_task(_position_loop(), name="okx.position"),
        asyncio.create_task(_stats_loop(), name="okx.stats"),
    ]
    try:
        await stop_event.wait()
    finally:
        log.info("okx.shutting_down")
        for t in tasks:
            t.cancel()
        for t in tasks:
            try:
                await t
            except (asyncio.CancelledError, Exception):
                pass
        await session.close()
        await bus.aclose()
        await registry.aclose()
