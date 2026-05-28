"""Gate.io USDT-perp adapter (via ccxt.gate)."""
from __future__ import annotations

from ._ccxt_base import CCXTAdapter


class GateAdapter(CCXTAdapter):
    name = "gate"
    CCXT_ID = "gate"
    DEFAULT_OPTIONS = {
        "defaultType": "swap",
        "marginMode": "cross",
    }
