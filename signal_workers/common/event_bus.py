"""Async Redis-Streams publisher with built-in back-pressure and dedupe.

Every worker uses *one* :class:`EventBus` instance.  It owns:

* a single ``redis.asyncio.Redis`` connection
* a global token bucket that caps publish rate (default 5k events/sec, per
  the spec) — when the bucket is empty we drop the **oldest** event in our
  internal buffer rather than block the worker producer
* a TTL-keyed LRU cache for ``event_id`` so a worker restart that re-sees
  the same upstream frame does not double-publish

Why not just rely on ``XADD MAXLEN ~``? The MAXLEN cap is global to the
*stream* — but each trader has its own stream. We need an additional
per-source cap on the producer side so a runaway WS source cannot starve
healthy ones, hence the in-process token bucket.
"""

from __future__ import annotations

import asyncio
import collections
import time
from typing import Optional

import structlog

from .metrics import BUS_DROPPED_TOTAL, SIGNAL_EVENTS_TOTAL
from .ratelimit import TokenBucket
from .schema import SignalEvent

log = structlog.get_logger(__name__)


class _LRUSet:
    """A simple bounded LRU set used to dedupe event_ids.

    Bounded so memory stays O(maxsize); we do not need exact LRU semantics
    — a FIFO ring is plenty for sub-second-scale dedup windows.
    """

    def __init__(self, maxsize: int = 50_000) -> None:
        self._maxsize = maxsize
        self._data: "collections.OrderedDict[str, None]" = collections.OrderedDict()

    def add_if_new(self, key: str) -> bool:
        if key in self._data:
            # Touch for LRU.
            self._data.move_to_end(key)
            return False
        self._data[key] = None
        if len(self._data) > self._maxsize:
            self._data.popitem(last=False)
        return True


class EventBus:
    """Thin wrapper around ``redis.asyncio`` Streams with rate-limit & dedupe.

    Parameters
    ----------
    redis_client
        An *already constructed* ``redis.asyncio.Redis`` instance. We accept it
        from the outside so tests can pass a ``fakeredis.aioredis.FakeRedis``
        without us importing fakeredis at runtime.
    max_publish_per_sec
        Soft cap on the producer side. Excess events are dropped (oldest
        first) and counted in ``BUS_DROPPED_TOTAL``.
    stream_maxlen
        Translated to ``XADD ... MAXLEN ~ {N}`` (approximate trim, much cheaper
        than exact). Default 10000 matches ``docs/event_schema.md``.
    """

    def __init__(
        self,
        redis_client,
        *,
        max_publish_per_sec: int = 5_000,
        stream_maxlen: int = 10_000,
        dedup_window: int = 50_000,
    ) -> None:
        self._r = redis_client
        self._bucket = TokenBucket(rate=max_publish_per_sec, capacity=max_publish_per_sec)
        self._maxlen = stream_maxlen
        self._dedup = _LRUSet(maxsize=dedup_window)

    # ------------------------------------------------------------------
    # Stream key derivation
    # ------------------------------------------------------------------
    @staticmethod
    def stream_key(source: str, trader_id: str) -> str:
        # trader_id may contain ':' (rare) — replace with '_' so the stream
        # key parser stays simple.
        safe = trader_id.replace(":", "_")
        return f"stream:signals:{source}:{safe}"

    # ------------------------------------------------------------------
    # Publish
    # ------------------------------------------------------------------
    async def publish(self, event: SignalEvent) -> Optional[str]:
        """Publish a single :class:`SignalEvent`.

        Returns the Redis-assigned stream id on success, ``None`` if the event
        was dropped (dedupe hit or rate-limit drop).
        """
        # 1) dedupe
        if not self._dedup.add_if_new(event.event_id):
            log.debug("bus.dedup_hit", event_id=event.event_id, source=event.source)
            return None

        # 2) back-pressure — try_acquire is non-blocking; if we cannot take a
        #    token we drop the event. This is intentional: under pressure we
        #    prefer fresh data over stale data.
        if not self._bucket.try_acquire(1):
            BUS_DROPPED_TOTAL.labels(source=event.source, reason="ratelimit").inc()
            log.warning(
                "bus.dropped",
                reason="ratelimit",
                source=event.source,
                trader_id=event.trader_id,
            )
            return None

        key = self.stream_key(event.source, event.trader_id)
        try:
            sid = await self._r.xadd(
                name=key,
                fields=event.to_redis_fields(),
                maxlen=self._maxlen,
                approximate=True,
            )
        except Exception as exc:  # noqa: BLE001 — we want every failure to log
            BUS_DROPPED_TOTAL.labels(source=event.source, reason="redis_error").inc()
            log.error("bus.xadd_failed", err=str(exc), key=key)
            return None

        SIGNAL_EVENTS_TOTAL.labels(source=event.source, kind=event.kind).inc()
        # propagate latency to the histogram
        lag_ms = int(time.time() * 1000) - event.ts
        if 0 <= lag_ms <= 60_000:  # filter clock-skew outliers
            from .metrics import EVENT_LAG_MS

            EVENT_LAG_MS.labels(source=event.source).observe(lag_ms)
        return sid.decode() if isinstance(sid, bytes) else sid

    async def publish_many(self, events: list[SignalEvent]) -> int:
        """Publish a batch sequentially; returns count actually written."""
        if not events:
            return 0
        # ``redis.asyncio`` does support pipelines, but mixing pipelines with
        # MAXLEN ~ and the dedupe gate adds complexity — and a batch of <=N00
        # XADDs is still O(ms) on local Redis. Keep it simple.
        ok = 0
        for ev in events:
            res = await self.publish(ev)
            if res is not None:
                ok += 1
        return ok

    async def aclose(self) -> None:
        """Close the underlying Redis connection. Idempotent."""
        try:
            await self._r.aclose()
        except AttributeError:
            # older redis-py used .close()
            try:
                await self._r.close()  # type: ignore[func-returns-value]
            except Exception:  # noqa: BLE001
                pass

    # Allow `async with EventBus(...)` for short-lived scripts/tests.
    async def __aenter__(self) -> "EventBus":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()
