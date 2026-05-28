"""End-to-end smoke: ``--worker okx_public`` boots and exits cleanly even when
there are no traders, no PG, and a fake Redis."""

from __future__ import annotations

import argparse
import asyncio

import fakeredis.aioredis
import pytest

from signal_workers.workers.okx_public import main as okx_main


@pytest.mark.asyncio
async def test_okx_worker_no_traders_no_crash(monkeypatch) -> None:
    """The okx_public worker must idle gracefully when traders table is empty."""

    # Bypass network: monkeypatch the discovery call to return nothing.
    async def _fake_lead_traders(self) -> list[dict]:
        return []

    async def _fake_current(self, code: str) -> list[dict]:  # pragma: no cover
        return []

    async def _fake_stats(self, code: str) -> dict | None:  # pragma: no cover
        return None

    monkeypatch.setattr(okx_main.OKXClient, "lead_traders", _fake_lead_traders)
    monkeypatch.setattr(okx_main.OKXClient, "current_subpositions", _fake_current)
    monkeypatch.setattr(okx_main.OKXClient, "stats", _fake_stats)

    # Bypass real Redis with FakeRedis.
    async def _fake_get_redis(*args, **kwargs):
        return fakeredis.aioredis.FakeRedis()

    monkeypatch.setattr(okx_main, "get_redis", _fake_get_redis)

    # Skip the auto-discovery REST call too, just to be safe.
    monkeypatch.setenv("OKX_AUTO_DISCOVER", "0")
    # Tighten loop intervals so the test completes quickly.
    monkeypatch.setattr(okx_main, "POSITION_POLL_INTERVAL", 0.05)
    monkeypatch.setattr(okx_main, "STATS_POLL_INTERVAL", 0.05)
    monkeypatch.setattr(okx_main, "DISCOVERY_INTERVAL", 0.05)

    stop_event = asyncio.Event()
    args = argparse.Namespace(
        worker="okx_public",
        redis_url=None,
        database_url=None,
        metrics_port=None,
        log_level="WARNING",
        dry_run=True,
        stop_event=stop_event,
    )

    task = asyncio.create_task(okx_main.run(args))
    # Let the loops spin a few iterations.
    await asyncio.sleep(0.3)
    stop_event.set()
    await asyncio.wait_for(task, timeout=5)
    # If we got here without exception, the worker survived empty-traders mode.
