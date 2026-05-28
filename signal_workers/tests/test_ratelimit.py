"""TokenBucket: minimal correctness checks."""

from __future__ import annotations

import asyncio
import time

import pytest

from signal_workers.common.ratelimit import TokenBucket


def test_try_acquire_starts_full() -> None:
    b = TokenBucket(rate=10, capacity=10)
    # 10 immediate acquires should all succeed (full bucket at start).
    assert all(b.try_acquire(1) for _ in range(10))
    # 11th should fail because no time has passed for refill.
    assert b.try_acquire(1) is False


def test_try_acquire_refills_over_time() -> None:
    b = TokenBucket(rate=100, capacity=1)
    assert b.try_acquire(1) is True
    assert b.try_acquire(1) is False
    time.sleep(0.05)  # 100 tps × 0.05 = 5 tokens, capped at 1
    assert b.try_acquire(1) is True


@pytest.mark.asyncio
async def test_acquire_blocks_then_succeeds() -> None:
    b = TokenBucket(rate=20, capacity=1)
    # Drain.
    assert b.try_acquire(1) is True
    # ``acquire`` must wait ≥1/rate = 50 ms.
    start = time.monotonic()
    await b.acquire(1)
    elapsed = time.monotonic() - start
    assert 0.02 < elapsed < 0.5
