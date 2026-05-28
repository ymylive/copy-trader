"""Symbol mapping: unified  ↔  exchange-native formats.

Canonical format used internally and in SignalEvent payloads:
    ``BASE-QUOTE-SWAP``     e.g. ``BTC-USDT-SWAP``

Each adapter calls ``to_native(exchange, unified)`` before placing orders
and ``to_unified(exchange, native)`` when reading positions.
"""
from __future__ import annotations

import re
from typing import Final

_UNIFIED_RE = re.compile(r"^(?P<base>[A-Z0-9]+)-(?P<quote>[A-Z0-9]+)-SWAP$")


def parse_unified(symbol: str) -> tuple[str, str]:
    """Return ``(base, quote)`` from a canonical symbol; raises ValueError."""
    m = _UNIFIED_RE.match(symbol.upper())
    if not m:
        raise ValueError(f"not a valid unified symbol: {symbol!r}")
    return m.group("base"), m.group("quote")


SUPPORTED_EXCHANGES: Final = ("binance", "okx", "gate", "bitget", "hyperliquid")


def to_native(exchange: str, unified: str) -> str:
    """Convert canonical symbol to the format the exchange expects."""
    base, quote = parse_unified(unified)
    ex = exchange.lower()
    if ex == "binance":
        return f"{base}{quote}"                     # BTCUSDT
    if ex == "okx":
        return f"{base}-{quote}-SWAP"               # BTC-USDT-SWAP
    if ex == "gate":
        return f"{base}_{quote}"                    # BTC_USDT (gate USDT-M perp)
    if ex == "bitget":
        return f"{base}{quote}_UMCBL"               # BTCUSDT_UMCBL
    if ex == "hyperliquid":
        return base                                 # HL uses just base
    raise ValueError(f"unsupported exchange: {exchange!r}")


def to_unified(exchange: str, native: str) -> str:
    """Reverse direction. Best-effort; falls back to ``native``-USDT-SWAP."""
    ex = exchange.lower()
    native_u = native.upper()
    if ex == "binance":
        # BTCUSDT → BTC-USDT-SWAP   (USDT-margined perp assumption)
        for q in ("USDT", "USDC", "BUSD", "FDUSD"):
            if native_u.endswith(q):
                base = native_u[: -len(q)]
                return f"{base}-{q}-SWAP"
        raise ValueError(f"cannot unify binance symbol: {native!r}")
    if ex == "okx":
        # already canonical
        if native_u.endswith("-SWAP"):
            return native_u
        # spot pair like BTC-USDT → BTC-USDT-SWAP
        if native_u.count("-") == 1:
            return f"{native_u}-SWAP"
        raise ValueError(f"cannot unify okx symbol: {native!r}")
    if ex == "gate":
        if "_" in native_u:
            base, quote = native_u.split("_", 1)
            return f"{base}-{quote}-SWAP"
        raise ValueError(f"cannot unify gate symbol: {native!r}")
    if ex == "bitget":
        # BTCUSDT_UMCBL → BTC-USDT-SWAP
        body = native_u.split("_", 1)[0]
        for q in ("USDT", "USDC"):
            if body.endswith(q):
                base = body[: -len(q)]
                return f"{base}-{q}-SWAP"
        raise ValueError(f"cannot unify bitget symbol: {native!r}")
    if ex == "hyperliquid":
        return f"{native_u}-USD-SWAP"
    raise ValueError(f"unsupported exchange: {exchange!r}")


def is_supported(exchange: str) -> bool:
    return exchange.lower() in SUPPORTED_EXCHANGES
