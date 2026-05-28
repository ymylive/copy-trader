"""Binance USDT-margined futures adapter (via ccxt.binanceusdm)."""
from __future__ import annotations

from ._ccxt_base import CCXTAdapter


class BinanceAdapter(CCXTAdapter):
    name = "binance"
    CCXT_ID = "binanceusdm"
    DEFAULT_OPTIONS = {
        "defaultType": "future",
        "hedgeMode": True,
        "recvWindow": 5000,
    }
