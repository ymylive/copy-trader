# 统一信号事件 Schema

所有 `signal_workers` 产出的事件必须符合本规范，写入 Redis Stream：

- key: `stream:signals:{source}:{trader_id}`
- maxlen: 10000 (XADD MAXLEN ~)

## SignalEvent v1

```python
{
  "schema": "signal.v1",
  "event_id": "uuid4",              # 去重
  "source": "hyperliquid|okx_public|binance_lead|evm_smart_money|okx_portfolio|bicoin",
  "trader_id": "0xabc... | 79346 | 4120066087544364033",
  "trader_name": "茂茂大魔王",
  "trader_meta": {                  # 可选辅助信息
    "exchange": "OKX",              # 该交易员所在交易所
    "is_hidden": false,
    "is_lead": true
  },
  "ts": 1714286400000,              # 事件 ms 时间戳（信号源给的）
  "received_ts": 1714286400123,     # worker 接收 ms（用于延迟分析）
  "kind": "position_snapshot | order_open | order_close | order_modify | margin_change",
  "payload": {
    # kind 决定 payload 结构

    # position_snapshot — 周期性持仓快照（全量）
    "positions": [
      {
        "symbol": "BTC-USDT-SWAP",   # 统一符号
        "side": "long|short",
        "qty": "1.234",
        "entry_px": "65000.0",
        "lev": "10",
        "margin": "8024.5",
        "unrealized_pnl": "120.0"
      }
    ],

    # order_open / order_close — 增量事件
    "symbol": "BTC-USDT-SWAP",
    "side": "long|short",
    "action": "open|increase|reduce|close",
    "qty_delta": "0.5",           # 变动量
    "px": "65100.0",              # 成交均价（若有）
    "reason": "manual|liquidation|stop_loss|take_profit",

    # margin_change
    "margin_delta": "-200.0"
  }
}
```

## 符号映射

执行引擎统一使用 `BTC-USDT-SWAP` 这种 OKX 风格，各交易所适配器内部转换：

| 统一 | Binance | OKX | Gate | Bitget | Hyperliquid |
|------|---------|-----|------|--------|-------------|
| BTC-USDT-SWAP | BTCUSDT | BTC-USDT-SWAP | BTC_USDT | BTCUSDT_UMCBL | BTC |

映射表实现于 `execution_engine/engine/symbols.py`。
