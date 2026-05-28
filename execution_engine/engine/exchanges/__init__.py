"""Exchange adapters (Binance, OKX, Gate, Bitget, Hyperliquid)."""
from __future__ import annotations

from typing import Any

from .base import (
    ExchangeAdapter,
    OrderResult,
    Position,
    ExchangeError,
    InsufficientBalance,
    RateLimited,
    AuthError,
)
from .binance import BinanceAdapter
from .okx import OKXAdapter
from .gate import GateAdapter
from .bitget import BitgetAdapter
from .hyperliquid import HyperliquidAdapter


def make_adapter(
    exchange: str,
    *,
    api_key: str | None,
    api_secret: str | None,
    passphrase: str | None = None,
    dry_run: bool = False,
    **extra: Any,
) -> ExchangeAdapter:
    """Factory: instantiate the right adapter."""
    ex = exchange.lower()
    if ex == "binance":
        return BinanceAdapter(api_key=api_key, api_secret=api_secret, dry_run=dry_run, **extra)
    if ex == "okx":
        return OKXAdapter(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            dry_run=dry_run,
            **extra,
        )
    if ex == "gate":
        return GateAdapter(api_key=api_key, api_secret=api_secret, dry_run=dry_run, **extra)
    if ex == "bitget":
        return BitgetAdapter(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            dry_run=dry_run,
            **extra,
        )
    if ex == "hyperliquid":
        return HyperliquidAdapter(
            wallet_private_key=api_secret,
            wallet_address=api_key,
            dry_run=dry_run,
            **extra,
        )
    raise ValueError(f"unsupported exchange: {exchange!r}")


__all__ = [
    "ExchangeAdapter",
    "OrderResult",
    "Position",
    "ExchangeError",
    "InsufficientBalance",
    "RateLimited",
    "AuthError",
    "BinanceAdapter",
    "OKXAdapter",
    "GateAdapter",
    "BitgetAdapter",
    "HyperliquidAdapter",
    "make_adapter",
]
