# 架构设计

## 数据流总览

```
                     ┌────────────────────────────────────────┐
                     │           信号采集层 (Workers)         │
                     │  ┌──────────────┐ ┌──────────────┐    │
                     │  │ Hyperliquid  │ │ OKX public   │    │
                     │  │   WS firehose│ │ copytrading  │    │
                     │  └──────┬───────┘ └──────┬───────┘    │
                     │  ┌──────┴───────┐ ┌──────┴───────┐    │
                     │  │ EVM Smart $$ │ │ Binance lead │    │
                     │  │   RPC subs   │ │ scraper      │    │
                     │  └──────┬───────┘ └──────┬───────┘    │
                     │         │                │             │
                     └─────────┼────────────────┼─────────────┘
                               ▼                ▼
                  ┌──────────────────────────────────┐
                  │  Redis Streams (event bus)        │
                  │  stream:signals:<source>:<id>     │
                  │  Schema: SignalEvent v1           │
                  └─────────────┬────────────────────┘
                                ▼
                  ┌──────────────────────────────────┐
                  │  Execution Engine (跟单引擎)      │
                  │  ┌────────────────────────────┐  │
                  │  │ FollowerRunner per user/    │  │
                  │  │ account/trader 配置         │  │
                  │  └──────┬─────────────────────┘  │
                  │  ┌──────▼──────┐                  │
                  │  │ PositionMapper (映射仓位)    │  │
                  │  └──────┬──────┘                  │
                  │  ┌──────▼──────┐                  │
                  │  │ RiskGuard (安全垫/止盈止损) │  │
                  │  └──────┬──────┘                  │
                  │  ┌──────▼──────┐                  │
                  │  │ ExchangeAdapter             │  │
                  │  │ (Binance/OKX/Gate/Bitget/HL)│  │
                  │  └──────┬──────┘                  │
                  └─────────┼────────────────────────┘
                            ▼
                  ┌─────────────────┐
                  │  交易所/链 (下单) │
                  └─────────────────┘

  ┌──────────────────────────────────────────────────────┐
  │  Backend (FastAPI) ── 用户/账户/订阅/钱包/通知 HTTP API │
  │  ────────────────────────────────────────────────────│
  │  PostgreSQL + TimescaleDB ── ORM via SQLAlchemy       │
  │  Redis ── 缓存 + Streams                              │
  └─────────────┬────────────────────────────────────────┘
                │
                ▼
        ┌────────────────┐
        │  Frontend SPA   │
        │  Vue 3 + EP     │
        └────────────────┘
```

## 进程拓扑

1. **`backend`** ── FastAPI HTTP/WS 网关；多副本无状态
2. **`signal_workers/<source>`** ── 独立 daemon，每信号源一组 worker，水平扩容
3. **`execution_engine`** ── 每用户账户 1 个 FollowerRunner 协程（asyncio），可单进程承载数百用户
4. **`postgres`、`redis`、`prometheus`、`grafana`** ── 基础设施

## 共享事件 Schema

见 `docs/event_schema.md`。所有 worker 产出统一 `SignalEvent`，发到 `stream:signals:<source>:<trader_id>`。

## 共享数据模型

见 `docs/data_model.md`。所有表通过 Alembic 管理。
