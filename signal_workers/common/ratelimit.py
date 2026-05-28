"""Tiny async-friendly token-bucket rate limiter.

We deliberately keep this lock-free / coroutine-friendly: the lock is held
only across the arithmetic update of the bucket, never across awaits, so
hot paths stay cheap even under heavy contention.
"""

from __future__ import annotations

import asyncio
import time


class TokenBucket:
    """A leaky-token bucket.

    Parameters
    ----------
    rate
        Tokens added per second (steady-state cap).
    capacity
        Maximum tokens that can accumulate while the consumer is idle.

    The bucket is initialised *full* so the first burst of N requests at
    process start is not penalised.
    """

    __slots__ = ("_rate", "_capacity", "_tokens", "_last", "_lock")

    def __init__(self, rate: float, capacity: float | None = None) -> None:
        if rate <= 0:
            raise ValueError("rate must be > 0")
        self._rate = float(rate)
        self._capacity = float(capacity if capacity is not None else rate)
        self._tokens = self._capacity
        self._last = time.monotonic()
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Non-blocking — used by the publish hot path.
    # ------------------------------------------------------------------
    def try_acquire(self, n: float = 1.0) -> bool:
        now = time.monotonic()
        elapsed = now - self._last
        self._last = now
        # refill
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
        if self._tokens >= n:
            self._tokens -= n
            return True
        return False

    # ------------------------------------------------------------------
    # Blocking variant — for REST pollers that want to "wait their turn".
    # ------------------------------------------------------------------
    async def acquire(self, n: float = 1.0) -> None:
        # Loop until we get a token. We compute sleep time analytically
        # rather than busy-looping.
        while True:
            async with self._lock:
                if self.try_acquire(n):
                    return
                # tokens we still need
                deficit = n - self._tokens
            # Calculate exact wait time outside the lock so other coros can
            # try too.
            wait_s = deficit / self._rate
            await asyncio.sleep(max(wait_s, 0.001))
