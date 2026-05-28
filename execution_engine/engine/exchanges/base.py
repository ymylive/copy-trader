"""ExchangeAdapter ABC + shared dataclasses + token-bucket rate limiter.

All concrete adapters MUST:

  * Accept ``dry_run=True`` and short-circuit ``place_order`` to return a
    deterministic stub when set. This lets the engine run end-to-end in
    tests / staging without hitting real exchanges.
  * Wrap network errors in ``ExchangeError`` (or one of its subclasses).
  * Convert unified ``BTC-USDT-SWAP`` symbols using
    :mod:`engine.symbols`.
  * Use ``decimal.Decimal`` everywhere — never float.
"""
from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional


# ─── exceptions ───────────────────────────────────────────────────────


class ExchangeError(Exception):
    """Generic exchange error wrapper."""


class InsufficientBalance(ExchangeError):
    """Not enough margin/balance to place the order."""


class RateLimited(ExchangeError):
    """Exchange returned HTTP 429 / weight exceeded."""


class AuthError(ExchangeError):
    """API key invalid or insufficient permissions."""


# ─── dataclasses ──────────────────────────────────────────────────────


@dataclass(slots=True, frozen=True)
class OrderResult:
    """Normalised response from any exchange."""

    exchange_order_id: str
    symbol: str               # unified BTC-USDT-SWAP
    side: str                 # long/short (NOT buy/sell)
    qty: Decimal
    px: Optional[Decimal]
    status: str               # filled / partial / open / rejected
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class Position:
    """Normalised position view."""

    symbol: str
    side: str                 # long/short
    qty: Decimal
    entry_px: Decimal
    lev: Decimal
    margin: Decimal
    unrealized_pnl: Decimal
    raw: dict[str, Any] = field(default_factory=dict)


# ─── token-bucket rate limiter ────────────────────────────────────────


class TokenBucket:
    """Simple asyncio token bucket; one per (exchange, api_key) pair."""

    def __init__(self, rate_per_sec: float, capacity: Optional[float] = None) -> None:
        self.rate = max(rate_per_sec, 0.1)
        self.capacity = capacity if capacity is not None else max(self.rate, 1.0)
        self.tokens = self.capacity
        self.timestamp = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, n: float = 1.0) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                self.tokens = min(self.capacity, self.tokens + (now - self.timestamp) * self.rate)
                self.timestamp = now
                if self.tokens >= n:
                    self.tokens -= n
                    return
                # how long until we have enough?
                deficit = n - self.tokens
                wait_s = deficit / self.rate
                await asyncio.sleep(wait_s)


# ─── ABC ──────────────────────────────────────────────────────────────


class ExchangeAdapter(ABC):
    """Unified interface every exchange adapter must implement."""

    name: str = "base"

    def __init__(
        self,
        api_key: Optional[str],
        api_secret: Optional[str],
        passphrase: Optional[str] = None,
        *,
        dry_run: bool = False,
        rate_per_sec: float = 10.0,
        **_: Any,
    ) -> None:
        self.api_key = api_key or ""
        self.api_secret = api_secret or ""
        self.passphrase = passphrase or ""
        self.dry_run = dry_run
        self.bucket = TokenBucket(rate_per_sec)

    # ── methods every adapter must implement ─────────────────────────
    @abstractmethod
    async def set_leverage(self, symbol: str, leverage: int) -> None: ...

    @abstractmethod
    async def set_dual_position_mode(self, on: bool) -> None: ...

    @abstractmethod
    async def get_balance(self) -> Decimal:
        """Free USDT margin available."""

    @abstractmethod
    async def get_total_assets(self) -> Decimal:
        """balance + unrealized PnL across all positions."""

    @abstractmethod
    async def get_positions(self) -> list[Position]: ...

    @abstractmethod
    async def place_order(self, intent: "OrderIntentLike") -> OrderResult: ...

    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> None: ...

    @abstractmethod
    async def close_position(
        self, symbol: str, side: str, qty: Optional[Decimal] = None
    ) -> OrderResult: ...

    @abstractmethod
    async def get_mark_price(self, symbol: str) -> Decimal: ...

    # ── convenience ──
    async def close(self) -> None:
        """Release any underlying HTTP/WS sessions. Override if needed."""
        return None


# Forward-declared type to avoid an import cycle (the engine.position_mapper
# imports nothing from exchanges).
OrderIntentLike = Any  # actually engine.position_mapper.OrderIntent
