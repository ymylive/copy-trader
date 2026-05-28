# Copy Trader — 跨交易所·跨数据源 智能跟单系统

> 立项时间：2026-05-28
> 对标：[Galaxy Quantitative](https://galaxyquantitative.com/home)（详细调研见 `research/galaxy_quantitative_report.md`）
> 信号源调研：`research/signal_sources_research.md`

## 一、产品愿景

打造一套**比 Galaxy Quantitative 更全栈、更链上、更工程化**的加密合约智能跟单系统：

- **6 大信号源**：Binance 带单员、OKX 带单员、OKX 交易员持仓展示、Hyperliquid、链上聪明钱、币Coin
- **4 大交易所执行**：Binance Futures、OKX Perpetual、Gate.io Perp、Bitget Mix；Hyperliquid 链上原生
- **零分润 + 月租订阅**：用户盈利全留，按月订阅
- **隐藏持仓 / 私域 / 满员 / 未上架交易员 都能跟**
- **多账号**：单用户最多 N 个绑定子账号，每账号独立出口 IP

## 二、技术决策（已拍板）

| 层 | 技术 | 说明 |
|---|---|---|
| 后端 HTTP | **Python 3.11 + FastAPI** | 异步、生态全 |
| ORM | **SQLAlchemy 2.0 (async) + Alembic** | 类型友好 |
| DB | **PostgreSQL 16 + TimescaleDB** | 持仓快照、净值曲线时序 |
| 缓存/队列 | **Redis 7 + Redis Streams** | 信号事件总线 |
| 任务调度 | **APScheduler** | 订阅扫描、Cookie 续期 |
| 交易 SDK | **CCXT (统一层) + binance-connector + python-okx + hyperliquid-python-sdk** | |
| 链上 | **web3.py 6 + Alchemy/Infura/Hyperliquid RPC** | 多 RPC fallback |
| WS | **websockets + aiohttp** | |
| 鉴权 | **JWT + bcrypt + TOTP（2FA 可选）** | |
| 前端 | **Vue 3 + TypeScript + Element Plus + Vite + Pinia + ECharts** | 与原站同栈，便于迁移参考 |
| 部署 | **Docker Compose（开发）→ K8s + Helm（生产）** | |
| 监控 | **Prometheus + Grafana + Loki** | |
| 通知 | **aiogram (TG) + email + WeChat WorkPush + Twilio** | |

## 三、Monorepo 目录

```
copy_trader/
├── README.md                ← 本文件
├── docs/                    架构 / API / 数据模型 / 运维
├── infra/                   docker-compose / migrations / k8s
├── backend/                 FastAPI HTTP/WS 网关 + 业务 API
├── signal_workers/          信号采集独立进程组
│   └── workers/
│       ├── hyperliquid_ws/
│       ├── okx_public/
│       ├── binance_lead/
│       ├── evm_smart_money/
│       └── bicoin_scraper/
├── execution_engine/        跟单执行引擎 + 风控
│   └── exchanges/{binance,okx,gate,bitget,hyperliquid}
├── frontend/                Vue 3 SPA（公开站 + 控制台）
└── research/                竞品 / 信号源调研报告（已完成）
```

## 四、信号源接入策略（基于调研）

| 信号源 | 实时性 | 鉴权 | 优先级 | 接入方案 |
|---|---|---|---|---|
| **Hyperliquid** | <200ms | 无 | **P0** | `wss://api.hyperliquid.xyz/ws` 直接订阅 `userEvents/userFills` |
| **OKX 带单 (public)** | ~1s | 无 | **P0** | `/api/v5/copytrading/public-*` 四端点 |
| **EVM 聪明钱** | block-time | 无 | **P0** | RPC eth_subscribe / Alchemy webhook |
| **OKX 个人持仓展示** | ~5s | 无 | P1 | OKX portfolio 公开页 |
| **Bitget 带单** | ~1s | 无 | P1 | Bitget copy-trade public API |
| **Binance 带单** | 5-30s | Cookie | P1 | Leaderboard scraper（私接口 `bapi/futures/v2`）+ 住宅 IP 池 |
| **Binance 隐藏持仓** | 视情况 | 用户 Cookie | P2 | SVIP 自带 cookie |
| **币Coin** | 不可控 | 用户名/密码 | P2 | 代理登录爬取 |

## 五、对标功能 Checklist（来自 Galaxy 报告）

### A. 跟单引擎核心参数（**必须 1:1 还原**）
- 资金管理：固定金额 / 全仓 / 复利滚动
- 跟单倍率（multiplier）
- 启动策略：不复制 / 仅浮亏 / 全部
- 方向限制：多/空/双向
- 开仓 & 加仓触发：市价 / 持仓均价限价 / 加仓价限价 + 价格优于 %
- 持仓止盈止损（循环触发 + 平仓比例）
- 跟单亏损阈值（USDT 绝对值）
- **安全垫亏损值**（净值跌破触发倍率衰减）
- 止盈回填策略
- 币种黑/白名单
- 反向跟单

### B. 账户与订阅
- 多账户（账户1-N，标准/极速）
- 每账户多出口 IP（白名单友好）
- API Key/Secret 加密存储 + 修改杠杆 + 双向持仓自动配置
- 商城：下单名额 / 跟单名额 / 带单员资格 / 极速跟单
- 钱包：余额、自动续费、资金明细
- 邀请：10% 返佣 + 受邀 UID 半价
- 7 天试用

### C. 通知 / 系统
- TG / 邮件 / 微信 / 短信
- 通知类型：下单成功 / 下单失败 / 触发风控 / 止盈止损 / 交易员保证金变动
- 软件更新（每账户独立服务实例）

### D. UI 页面
- 公开站：首页 / 推广返佣 / 商城 / 钱包 / 个人中心 / 使用教程
- 控制台：Dashboard / 账户管理 / 交易员广场 / 交易所自选 / 币Coin自选 / 持仓详情 / 系统控制
- 跟单配置弹窗（20+ 参数）
- 持仓详情（持仓列表/操作记录/跟单分析 + 一键全平）

## 六、里程碑（Roadmap）

| 里程碑 | 时间 | 交付物 |
|---|---|---|
| **M0 基础设施** | Day 0-3 | Monorepo 骨架 + Docker Compose + DB schema + 鉴权 + 用户/账户/订阅 API |
| **M1 信号源 P0** | Day 4-10 | Hyperliquid WS + OKX public + EVM 聪明钱 worker，事件总线打通 |
| **M2 执行引擎** | Day 11-17 | 跟单引擎 + 风控 + Binance/OKX/Hyperliquid 下单适配器，单测覆盖 |
| **M3 前端控制台** | Day 18-24 | Vue 3 SPA + 控制台全部页面 + 跟单配置弹窗 |
| **M4 商业化层** | Day 25-30 | 商城 + 钱包 + 邀请 + 通知 + 端到端联调 + 单用户全链路 demo |
| **M5 信号源 P1/P2** | Day 31-45 | Binance leaderboard scraper + 币Coin 代理登录 + Bitget + Gate.io |
| **M6 监控+部署** | Day 46-60 | Prometheus/Grafana + 多节点部署 + 出口 IP 池 |

## 七、差异化（超越 Galaxy）

1. **Hyperliquid 一等公民**：原站"Hyperbot" tab 是空的；我们做 vault + 链上原生 + 0 信任跟单
2. **链上聪明钱多链**：不仅 Hyperliquid，扩展到 GMX、dYdX、Arbitrum、Solana
3. **风控加强**：单笔最大滑点、API 健康检查、撤销孤儿单
4. **可 self-host**：docker 一键部署
5. **归因分析**：净值曲线、信号源叠加图、Sharpe/Calmar/MAR 全套指标
6. **合规优先**：用户 Cookie/账号上传走显式 OAuth 授权 + 风险提示

## 八、开发执行（已并发 Agent 启动）

详见 `docs/dev_plan.md`。
