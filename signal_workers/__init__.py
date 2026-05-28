"""signal_workers — signal acquisition daemons for the copy_trader platform.

Each worker is a long-running asyncio process that subscribes to one upstream
data source (Hyperliquid WS, OKX public copytrading REST, EVM perp DEX logs,
Binance leaderboard, bicoin private API) and emits unified ``SignalEvent``
records to Redis Streams (``stream:signals:{source}:{trader_id}``).

Run via:

    python -m signal_workers --worker hyperliquid_ws
    python -m signal_workers --worker okx_public
    python -m signal_workers --worker evm_smart_money
"""

__version__ = "0.1.0"
