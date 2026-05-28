"""Bitget USDT-M perp adapter (via ccxt.bitget)."""
from __future__ import annotations

from ._ccxt_base import CCXTAdapter


class BitgetAdapter(CCXTAdapter):
    name = "bitget"
    CCXT_ID = "bitget"
    DEFAULT_OPTIONS = {
        "defaultType": "swap",
        "productType": "USDT-FUTURES",
    }
