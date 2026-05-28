"""Asyncpg-backed view onto the ``traders`` table.

Each worker calls :meth:`TraderRegistry.refresh` every 60 s to pick up newly
added trader rows (or `stats`/`meta` updates).  The registry caches the last
result in memory so the WS/REST subscription loop never blocks on the DB.

Schema reference: ``docs/data_model.md``::

    traders(id, source, external_id, display_name, exchange, meta, stats,
            last_active_at)
    UNIQUE (source, external_id)

The worker code holds :class:`TraderRow` instances, **never raw asyncpg
records**, so type-checking and tests stay decoupled from the DB driver.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from typing import Any, Optional

import structlog

log = structlog.get_logger(__name__)


@dataclass(slots=True)
class TraderRow:
    id: int
    source: str
    external_id: str
    display_name: Optional[str] = None
    exchange: Optional[str] = None
    meta: dict[str, Any] = field(default_factory=dict)
    stats: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        """Composite key used as ``SignalEvent.trader_id``.

        Hyperliquid/EVM addresses already include the source-implicit prefix
        in their format (0x...); OKX uses ``uniqueCode``; Binance uses
        ``encryptedUid``. All are unique within their source — we publish
        the *external_id* here so consumers can correlate with the upstream
        trader without an extra DB join.
        """
        return self.external_id


class TraderRegistry:
    """Read-only async cache of the ``traders`` table.

    Parameters
    ----------
    dsn
        PostgreSQL DSN. If ``None``, falls back to ``DATABASE_URL`` env.
        If still empty, the registry runs in **memory-only mode**: the
        ``seed()`` method becomes the only data source. This keeps unit
        tests and ``--worker okx_public`` "no traders at all" smoke runs
        from crashing.
    source_filter
        Restrict refresh queries to one ``traders.source`` value.
    """

    def __init__(self, dsn: str | None = None, source_filter: str | None = None) -> None:
        self._dsn = dsn or os.environ.get("DATABASE_URL")
        self._source = source_filter
        self._rows: list[TraderRow] = []
        self._lock = asyncio.Lock()
        self._pool = None  # asyncpg.Pool — lazy init

    # ------------------------------------------------------------------
    # Seed / inspect API (works without a DB).
    # ------------------------------------------------------------------
    def seed(self, rows: list[TraderRow]) -> None:
        """Replace the in-memory cache without touching Postgres.

        Useful in tests and in worker `--dry-run` mode.
        """
        self._rows = list(rows)

    def snapshot(self) -> list[TraderRow]:
        """Return a shallow copy of the current cache."""
        return list(self._rows)

    def filter(self, *, chain: str | None = None) -> list[TraderRow]:
        out = []
        for r in self._rows:
            if chain is not None and r.meta.get("chain") != chain:
                continue
            out.append(r)
        return out

    # ------------------------------------------------------------------
    # DB-backed refresh
    # ------------------------------------------------------------------
    async def _ensure_pool(self) -> None:
        if self._pool is not None or not self._dsn:
            return
        import asyncpg

        self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=4)

    async def refresh(self) -> list[TraderRow]:
        """Re-query Postgres and update the cache.

        If no DSN is configured, this is a no-op that returns the current
        in-memory cache — workers can still loop happily without a DB.
        """
        if not self._dsn:
            return self.snapshot()

        await self._ensure_pool()
        assert self._pool is not None

        sql = """
            SELECT id, source, external_id, display_name, exchange,
                   COALESCE(meta, '{}'::jsonb)  AS meta,
                   COALESCE(stats, '{}'::jsonb) AS stats
              FROM traders
        """
        args: list[Any] = []
        if self._source:
            sql += " WHERE source = $1"
            args.append(self._source)

        try:
            async with self._pool.acquire() as conn:
                records = await conn.fetch(sql, *args)
        except Exception as exc:  # noqa: BLE001
            log.error("trader_registry.refresh_failed", err=str(exc))
            return self.snapshot()

        new_rows: list[TraderRow] = []
        for r in records:
            meta = r["meta"]
            stats = r["stats"]
            # asyncpg returns jsonb as Python dict already if you set
            # codec; otherwise as str. Handle both.
            if isinstance(meta, str):
                import orjson

                meta = orjson.loads(meta)
            if isinstance(stats, str):
                import orjson

                stats = orjson.loads(stats)
            new_rows.append(
                TraderRow(
                    id=r["id"],
                    source=r["source"],
                    external_id=r["external_id"],
                    display_name=r["display_name"],
                    exchange=r["exchange"],
                    meta=meta or {},
                    stats=stats or {},
                )
            )

        async with self._lock:
            self._rows = new_rows
        log.info("trader_registry.refreshed", source=self._source, count=len(new_rows))
        return list(new_rows)

    # ------------------------------------------------------------------
    # `traders.stats` write-back (used by okx_public to upsert stats).
    # ------------------------------------------------------------------
    async def upsert_stats(self, source: str, external_id: str, stats: dict[str, Any]) -> None:
        if not self._dsn:
            return
        await self._ensure_pool()
        assert self._pool is not None
        import orjson

        sql = """
            UPDATE traders
               SET stats = $3::jsonb,
                   last_active_at = now()
             WHERE source = $1 AND external_id = $2
        """
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(sql, source, external_id, orjson.dumps(stats).decode())
        except Exception as exc:  # noqa: BLE001
            log.warning("trader_registry.upsert_stats_failed", err=str(exc))

    async def write_position_snapshot(
        self,
        *,
        exchange_account_id: int,
        symbol: str,
        side: str,
        qty: str,
        entry_px: str,
        lev: str,
        margin: str,
        unrealized_pnl: str,
        ts_ms: int,
    ) -> None:
        """Insert one row into ``positions_snapshots`` (TimescaleDB hypertable).

        Workers call this when they receive a ``position_snapshot`` event; the
        DB row is written **regardless** of whether any user is following the
        trader yet (so historical analytics survive subscription churn).
        """
        if not self._dsn:
            return
        await self._ensure_pool()
        assert self._pool is not None

        # ts column is timestamptz — convert ms → datetime
        import datetime as _dt

        ts = _dt.datetime.fromtimestamp(ts_ms / 1000.0, tz=_dt.timezone.utc)
        sql = """
            INSERT INTO positions_snapshots
                (ts, exchange_account_id, symbol, side, qty, entry_px, lev, margin, unrealized_pnl)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    sql,
                    ts,
                    exchange_account_id,
                    symbol,
                    side,
                    qty,
                    entry_px,
                    lev,
                    margin,
                    unrealized_pnl,
                )
        except Exception as exc:  # noqa: BLE001
            log.warning("trader_registry.snapshot_write_failed", err=str(exc))

    async def aclose(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
