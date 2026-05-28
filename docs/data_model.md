# 数据模型

PostgreSQL 16 + TimescaleDB。所有表通过 Alembic 迁移。

## 核心表

### users — 用户
| 列 | 类型 | 说明 |
|---|---|---|
| id | bigserial PK | |
| username | text unique | |
| password_hash | text | bcrypt |
| email | text | |
| phone | text | |
| invite_code | text unique | 自己的邀请码 |
| referred_by | bigint FK users.id | 推荐人 |
| level | int default 0 | 等级 |
| referral_rate | numeric(5,4) default 0.10 | 返佣比例 |
| created_at | timestamptz default now() | |

### exchange_accounts — 用户绑定的交易所子账户（账户1-N）
| 列 | 类型 | 说明 |
|---|---|---|
| id | bigserial PK | |
| user_id | bigint FK users.id | |
| alias | text | "账户1"、"账户2"... |
| tier | text | standard / express |
| exchange | text | binance / okx / gate / bitget / hyperliquid |
| uid | text | 交易所端 UID |
| api_key_enc | text | AES-GCM 加密 |
| api_secret_enc | text | |
| passphrase_enc | text | OKX 需要 |
| leverage_default | int | |
| status | text | active / inactive / disabled |
| egress_ips | text[] | 分配的出口 IP |
| activated_at | timestamptz | |
| service_expires_at | timestamptz | 订阅服务到期 |
| created_at | timestamptz | |

### subscription_resources — 用户资源（下单名额/跟单名额/带单员资格）
| 列 | 类型 | 说明 |
|---|---|---|
| id | bigserial PK | |
| user_id | bigint FK | |
| sku | text | order_slot / follow_slot / lead_role / express_slot |
| bound_account_id | bigint FK exchange_accounts.id | NULLABLE |
| purchase_time | timestamptz | |
| expires_at | timestamptz | 永久则 9999-12-31 |
| auto_renew | bool | |
| coupon_id | bigint FK | |

### wallet_balances / wallet_transactions
- balances: user_id, currency, amount
- transactions: user_id, type (deposit/withdraw/consume/refund), amount, ref_sku, created_at

### traders — 已知交易员档案（不区分谁加的）
| 列 | 类型 | 说明 |
|---|---|---|
| id | bigserial PK | |
| source | text | 同 SignalEvent.source |
| external_id | text | |
| display_name | text | |
| exchange | text | |
| meta | jsonb | 上架/标签/分类 |
| stats | jsonb | 总盈亏/收益率/夏普/胜率/回撤 缓存 |
| last_active_at | timestamptz | |
| UNIQUE (source, external_id) | | |

### copy_configs — 用户跟单配置（核心）
| 列 | 类型 | 说明 |
|---|---|---|
| id | bigserial PK | |
| user_id | bigint FK | |
| exchange_account_id | bigint FK | 下单账户 |
| trader_id | bigint FK traders.id | |
| reverse | bool | 反向跟单 |
| name | text | 配置别名，默认 "配置1" |
| money_mode | text | fixed / full / compound |
| money_param | jsonb | fixed: {amount}; full/compound: {percent} |
| multiplier | numeric(8,4) | 跟单倍率 |
| initial_strategy | text | none / only_loss / all |
| direction_limit | text | both / long_only / short_only |
| open_trigger | jsonb | {kind: market\|avg_limit\|add_limit, edge_pct} |
| add_trigger | jsonb | 同 |
| tp | jsonb | {enabled, cycle, qty_pct, ...} |
| sl | jsonb | 同上 |
| loss_threshold | jsonb | {usdt, action: pause_and_close} |
| safety_cushion | jsonb | {nav_drop, decay_factor} |
| refill | jsonb | {refill_on_back_to_avg, allow_re_tp} |
| symbol_blacklist | text[] | |
| symbol_whitelist | text[] | |
| notify_channels | text[] | tg/email/wechat/sms |
| notify_types | text[] | open_ok/open_fail/risk/tp_sl/margin_change |
| status | text | running / paused / stopped |
| created_at | timestamptz | |

### copy_orders — 已下单流水
- copy_config_id, exchange_order_id, symbol, side, qty, px, status, source_event_id, created_at

### positions_snapshots — TimescaleDB hypertable（每分钟全量）
- ts, exchange_account_id, symbol, side, qty, entry_px, lev, margin, unrealized_pnl

### nav_curve — TimescaleDB（每小时净值）
- ts, exchange_account_id, total_balance, realized_pnl, unrealized_pnl

### notifications_log
- user_id, channel, type, payload, sent_at, status

### login_history
- user_id, ip, geo, ua, ts

### referral_records
- inviter_id, invitee_id, registered_at, paid_amount, commission, status

## 索引/Hypertable

```sql
SELECT create_hypertable('positions_snapshots', 'ts');
SELECT create_hypertable('nav_curve', 'ts');
CREATE INDEX ix_copy_configs_user_status ON copy_configs(user_id, status);
CREATE INDEX ix_traders_source_external ON traders(source, external_id);
CREATE INDEX ix_copy_orders_config ON copy_orders(copy_config_id, created_at DESC);
```
