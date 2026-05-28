"""Cross-exchange symbol & side normalisation.

The wire-level :class:`~signal_workers.common.schema.SignalEvent` uses the OKX
"unified" symbol form (``BTC-USDT-SWAP``) everywhere. Each worker calls into
this module before publishing so the rest of the platform (execution_engine,
backend, frontend) never needs to know the upstream's native naming.

Mapping table (must stay in sync with ``execution_engine/engine/symbols.py``).
"""

from __future__ import annotations

import re
from typing import Final

# Coins commonly traded that need explicit overrides (e.g. Hyperliquid "kPEPE"
# means 1000-PEPE perp). Anything not in this table goes through the generic
# uppercase + "-USDT-SWAP" suffix path.
_HL_OVERRIDES: Final[dict[str, str]] = {
    "BTC": "BTC-USDT-SWAP",
    "ETH": "ETH-USDT-SWAP",
    "SOL": "SOL-USDT-SWAP",
    "ARB": "ARB-USDT-SWAP",
    "kPEPE": "1000PEPE-USDT-SWAP",
    "kSHIB": "1000SHIB-USDT-SWAP",
    "kBONK": "1000BONK-USDT-SWAP",
    "kFLOKI": "1000FLOKI-USDT-SWAP",
    "HYPE": "HYPE-USDT-SWAP",
}

_BINANCE_RE = re.compile(r"^([A-Z0-9]+?)(USDT|USDC|BUSD)$")


def normalize_symbol(raw: str, source: str) -> str:
    """Translate an upstream symbol string into the unified OKX style.

    Parameters
    ----------
    raw
        The exchange-native symbol (e.g. ``BTCUSDT``, ``BTC``, ``BTC-USDT-SWAP``).
    source
        :class:`~signal_workers.common.schema.SignalSource`. Used to disambiguate
        Hyperliquid's bare coin tickers.

    The function is intentionally pure and side-effect-free so it's trivial to
    unit-test the symbol table.
    """
    if not raw:
        return raw

    s = raw.strip()

    # 1) already in unified form
    if s.endswith("-USDT-SWAP") or s.endswith("-USDC-SWAP"):
        return s.upper().replace("-USDC-SWAP", "-USDT-SWAP")  # normalise quote

    # 2) Hyperliquid bare coin (no quote, no suffix)
    if source == "hyperliquid":
        if s in _HL_OVERRIDES:
            return _HL_OVERRIDES[s]
        return f"{s.upper()}-USDT-SWAP"

    # 3) Binance-style BTCUSDT
    m = _BINANCE_RE.match(s.upper())
    if m:
        base, quote = m.group(1), m.group(2)
        # USDC / BUSD all collapse to -USDT-SWAP at the unified layer; the
        # execution adapter re-translates if a target exchange genuinely has
        # a USDC contract.
        return f"{base}-USDT-SWAP"

    # 4) OKX already does it right.
    if "-SWAP" in s.upper():
        return s.upper()

    # 5) Last-resort: assume it's a bare base ticker.
    return f"{s.upper()}-USDT-SWAP"


# ---------------------------------------------------------------------------
# Side normalisation
# ---------------------------------------------------------------------------
_LONG_SET = {"long", "buy", "bid", "b", "1", "true", "yes"}
_SHORT_SET = {"short", "sell", "ask", "a", "-1", "s"}


def normalize_side(raw: str | bool | int | float) -> str:
    """Reduce free-form side spellings to ``long`` / ``short``.

    Hyperliquid uses ``"B"/"A"`` (bid/ask), Binance uses ``BUY/SELL``, OKX uses
    ``"long"/"short"``, and EVM contract logs sometimes encode side as a bool
    or a sign on size — we accept all of those.

    Raises :class:`ValueError` rather than guessing on unknown inputs so the
    bug surfaces in CI / logs rather than mis-routing capital.
    """
    if isinstance(raw, bool):
        return "long" if raw else "short"
    if isinstance(raw, (int, float)):
        if raw > 0:
            return "long"
        if raw < 0:
            return "short"
        raise ValueError("cannot derive side from a zero-sized quantity")
    if not isinstance(raw, str):
        raise TypeError(f"side must be str/bool/number, got {type(raw).__name__}")

    s = raw.strip().lower()
    if s in _LONG_SET:
        return "long"
    if s in _SHORT_SET:
        return "short"
    raise ValueError(f"unknown side spelling: {raw!r}")
