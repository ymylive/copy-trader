"""Construct an async Redis client honouring the CLI / env config.

In ``--dry-run`` mode we substitute a ``StdoutRedis`` shim so workers can be
exercised locally without a live Redis. The shim implements only the calls
the :class:`~signal_workers.common.event_bus.EventBus` uses.
"""

from __future__ import annotations

import os
from typing import Any

import structlog

log = structlog.get_logger(__name__)


class StdoutRedis:
    """Minimal stand-in that prints what a real ``XADD`` would have written.

    Mirrors the subset of the ``redis.asyncio.Redis`` surface that
    :class:`EventBus` calls (``xadd`` and ``aclose``).
    """

    async def xadd(self, *, name: str, fields: dict[str, str], maxlen: int, approximate: bool) -> bytes:
        import orjson

        log.info("dryrun.xadd", stream=name, fields=fields)
        return f"{name}-{int.from_bytes(os.urandom(4), 'big')}".encode()

    async def aclose(self) -> None:
        return None


async def get_redis(redis_url: str | None, *, dry_run: bool = False) -> Any:
    if dry_run:
        log.info("redis.dry_run_mode")
        return StdoutRedis()

    url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    import redis.asyncio as redis_async

    client = redis_async.from_url(url, encoding="utf-8", decode_responses=False)
    try:
        await client.ping()
        log.info("redis.connected", url=url)
    except Exception as exc:  # noqa: BLE001
        log.warning("redis.ping_failed", err=str(exc), url=url)
    return client
