"""Trader-registry in-memory paths.

We do not have a real Postgres in CI, so this test exercises only the
``seed`` / ``snapshot`` / ``filter`` no-DB code path. The asyncpg-backed
methods are covered in integration tests run against the docker-compose
PG container.
"""

from __future__ import annotations

import pytest

from signal_workers.common.trader_registry import TraderRegistry, TraderRow


@pytest.mark.asyncio
async def test_refresh_without_dsn_is_noop() -> None:
    r = TraderRegistry(dsn=None)
    assert await r.refresh() == []
    # Seeding works even without DSN.
    r.seed(
        [
            TraderRow(id=1, source="okx_public", external_id="UC1"),
            TraderRow(id=2, source="okx_public", external_id="UC2"),
        ]
    )
    assert {t.external_id for t in r.snapshot()} == {"UC1", "UC2"}
    await r.aclose()


@pytest.mark.asyncio
async def test_filter_by_chain() -> None:
    r = TraderRegistry(dsn=None)
    r.seed(
        [
            TraderRow(id=1, source="evm_smart_money", external_id="0xa", meta={"chain": "arbitrum"}),
            TraderRow(id=2, source="evm_smart_money", external_id="0xb", meta={"chain": "ethereum"}),
            TraderRow(id=3, source="evm_smart_money", external_id="0xc", meta={"chain": "arbitrum"}),
        ]
    )
    arb = r.filter(chain="arbitrum")
    assert {t.external_id for t in arb} == {"0xa", "0xc"}
    await r.aclose()


@pytest.mark.asyncio
async def test_position_snapshot_write_without_dsn_is_silent() -> None:
    r = TraderRegistry(dsn=None)
    # Should NOT raise.
    await r.write_position_snapshot(
        exchange_account_id=1,
        symbol="BTC-USDT-SWAP",
        side="long",
        qty="1.0",
        entry_px="65000",
        lev="10",
        margin="6500",
        unrealized_pnl="0",
        ts_ms=1714286400000,
    )
    await r.aclose()
