# signal_workers

Signal-acquisition daemons for the Copy Trader platform. Each worker subscribes
to one upstream data source and emits unified `SignalEvent` records to Redis
Streams (`stream:signals:{source}:{trader_id}`).

## Workers

| name | status | source | transport |
|------|--------|--------|-----------|
| `hyperliquid_ws`    | P0 implemented | Hyperliquid `wss://api.hyperliquid.xyz/ws` | WebSocket |
| `okx_public`        | P0 implemented | OKX `/api/v5/copytrading/public-*` | REST polling |
| `evm_smart_money`   | P0 implemented (low-fidelity log decode) | Alchemy/QuickNode WS | RPC subs |
| `binance_lead`      | P1 stub        | `bapi/futures/v2/private/...` | Cookie + JA3 (TODO) |
| `bicoin_scraper`    | P2 stub        | bicoin.com.cn private | Playwright (TODO) |

## Install & run

```bash
cd signal_workers
pip install -e .

# Run a worker
python -m signal_workers --worker okx_public --dry-run

# Real Redis + real PG
REDIS_URL=redis://localhost:6379/0 \
DATABASE_URL=postgres://user:pass@localhost/copy_trader \
ALCHEMY_WS_URL_ARBITRUM=wss://arb-mainnet.g.alchemy.com/v2/<key> \
python -m signal_workers --worker hyperliquid_ws
```

## Tests

```bash
pip install -e .[dev]
pytest signal_workers/tests
```

See `docs/event_schema.md` (repo-root) for the wire format.
