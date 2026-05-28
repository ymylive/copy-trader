"""OKX perpetual swap adapter (via ccxt.okx; requires passphrase)."""
from __future__ import annotations

from ._ccxt_base import CCXTAdapter


class OKXAdapter(CCXTAdapter):
    name = "okx"
    CCXT_ID = "okx"
    DEFAULT_OPTIONS = {
        "defaultType": "swap",
    }
