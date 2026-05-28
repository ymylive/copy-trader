# 跨交易所跟单系统 · 信号源接入技术调研报告

> 项目代号：copy_trader
> 调研日期：2026-05-28
> 调研对象：Binance Lead Trader / OKX Lead Trader / Hyperliquid / 链上聪明钱 / 币Coin
> 参考产品：galaxyquantitative.com（详见同目录 `galaxy_quantitative_report.md`）
> 注：本文为研究性技术摘要，不包含实现代码；URL 与字段名已用 WebFetch/WebSearch 多源交叉验证，但 Binance/OKX/币Coin 类内部接口存在随时变更与法律灰色风险，落地前需再次抓包确认。

---

## 0. 执行摘要（TL;DR）

要把"跨所跟单"做出毫秒级响应，信号源可分为两类：**链上公开数据**（Hyperliquid / EVM 聪明钱）和**中心化交易所私有接口**（Binance / OKX / 币Coin）。前者完全合法、SDK 成熟、推送延迟可压到 100 ms 级别；后者全部依赖反向工程 web 内部接口（bapi / priapi），需要持续维护 Cookie、aws_waf token、cf_clearance、UA 指纹、住宅 IP 池，是工程复杂度最高、最容易失效的部分。

具体结论：

1. **Hyperliquid（P0，最值得做）**——`wss://api.hyperliquid.xyz/ws` 的 `userEvents` / `userFills` / `orderUpdates` 完全公开无鉴权，每订阅一个地址实时推送其全部成交与订单状态变化，是当前唯一能从协议层拿到真正"实时下单事件"的来源。SDK：[`hyperliquid-python-sdk`](https://github.com/hyperliquid-dex/hyperliquid-python-sdk)。一台机器同时盯几百到几千个地址在工程上完全可行。**没有"订阅全链"的 firehose，需要先用 `leaderboard` / Nansen / Hypertracker 找到聪明地址名单再逐个 subscribe**。

2. **链上聪明钱（P0，与 Hyperliquid 共用基础设施）**——Hyperliquid 上的聪明钱完全用上面那条链路；EVM（GMX / dYdX v4 / Aster / Vertex / Paradex）方案是 RPC + Subgraph + 合约事件订阅（`UpdatePosition`、`OrderFilled`、`PositionEvent`），延迟次秒级。免费方案：Alchemy/QuickNode/GetBlock 的 free tier + 自部署 The Graph Node；付费方案：Nansen API（≥$1500/mo Smart Money tag）、Arkham Ultra API、Hypertracker Stream（$1999/mo，200 万 req）。

3. **Binance Lead Trader（P1，半失效）**——原 `/bapi/futures/v1/public/.../getOtherPosition` 已 2023 年被改为 `/v2/private/...`，需要登录 Cookie + p20t/p21t 等内部 token。Leaderboard scraper（github.com/Nunnito/Binance-Futures-Leaderboard-API、tugkan/binance-futures-leaderboard-scraper）仍可拿到 `otherPositionRetList`，但 `positionShared=false` 的"隐藏持仓"在公开接口里**完全不返回**，galaxyquantitative 的"隐藏持仓也能跟"高概率靠的是**用户上传带单员账号 cookie / 移动端 token / 内部带单员 API key**。

4. **OKX Lead Trader（P1，最易接入）**——OKX 官方 v5 文档明确公开了 `/api/v5/copytrading/public-current-subpositions`、`public-subpositions-history`、`public-lead-traders`、`public-stats` 四个 **public-** 前缀端点，**完全免鉴权**，是合规且文档化最好的中心化带单源，建议首期优先接入。

5. **币Coin（P2，依赖账号代理）**——bicoin.com.cn 没有官方开放 API；移动端使用 Native 层加密（sign+data，frida hook），逆向成本高；最稳妥做法和 galaxyquantitative 一样：让最终用户上传自己的币Coin 账号密码 / cookie，由我方代理登录后从已认证的私有接口拉取大佬持仓。法律与口碑风险较高，需用户明示授权 + 走加密保险柜。

| # | 信号源 | 实时性 | 是否需登录/鉴权 | 优先级 |
|---|---|---|---|---|
| 1 | Hyperliquid WebSocket (`userEvents`/`userFills`/`orderUpdates`) | **毫秒级 (链区块 ~1s, ws push <100 ms)** | 无 | **P0** |
| 2 | EVM 聪明钱（GMX / Aster / dYdX 合约事件 + Subgraph） | 1–3 秒（一个区块） | 仅需 RPC key（免费） | **P0** |
| 3 | OKX 公开 copytrading `/api/v5/copytrading/public-*` | ~3–10 秒（轮询） | **无鉴权** | **P0** |
| 4 | Binance Leaderboard `bapi/futures/v?/.../getOtherPosition` | 5–30 秒（轮询） | 需 Cookie/aws_waf token + 住宅 IP | P1 |
| 5 | Binance Lead Portfolio 隐藏持仓 | 5–30 秒（轮询） | **需带单员本人 cookie / Lead Trader API key**，否则拿不到 | P2 (高价值高风险) |
| 6 | Nansen / Arkham / Coinglass Hyperliquid Whale API | 1–30 秒（订阅或轮询） | 付费 API Key | P1（补量） |
| 7 | 币Coin (bicoin.com.cn) 私有接口 | 5–30 秒 | 需用户上传账号 cookie；Native sign 加密 | P2 |

落地建议：**第 1 期只做 Hyperliquid + EVM 聪明钱 + OKX public-copytrading**，三周内可端到端跑通；第 2 期再叠 Binance Leaderboard scraper + 币Coin 代理登录；隐藏持仓这一类"销售卖点"放到 SVIP 套餐里、走"用户自己上传 cookie"模式以转嫁合规风险（galaxyquantitative 即如此）。

---

## 1. Binance Lead Trader / Leaderboard 信号

### 1.1 公开端点现状

历史上 Binance 用户分享自己的合约持仓走的是 web 内部接口：

| 用途 | 旧 URL（已下线/改私有） | 新 URL（需登录） |
|---|---|---|
| 搜索 leaderboard | `POST https://www.binance.com/bapi/futures/v1/public/future/leaderboard/searchLeaderboard` | `POST https://www.binance.com/bapi/futures/v2/private/future/leaderboard/searchLeaderboard` |
| 拉取某带单员持仓 | `POST https://www.binance.com/bapi/futures/v1/public/future/leaderboard/getOtherPosition` | `POST https://www.binance.com/bapi/futures/v2/private/future/leaderboard/getOtherPosition` |
| 排行榜列表 | `POST .../getLeaderboardRank` | 同上迁移 |
| 性能曲线 | `POST .../getOtherPerformance` | 同上迁移 |

请求体示例（POST JSON）：
```json
{ "encryptedUid": "ABCDEF...", "tradeType": "PERPETUAL" }
```
响应字段（关键）：
- `otherPositionRetList[]`：`{symbol, entryPrice, markPrice, pnl, roe, amount, updateTime, leverage, tradeBefore, yellow}`
- `positionShared: bool`：**带单员本人在前端关闭"分享我的持仓"开关后，这里直接返回 `data: null` 或空数组**——这就是"隐藏持仓"的来源。

### 1.2 鉴权要求

- 2023 年迁到 `v2/private/...` 之后，**必须带浏览器登录 Cookie**（`p20t`, `p21t`, `cr00`, `BNC_FV_KEY*`, `bnc-uuid`, `aws-waf-token`, `cf_clearance`，必要时 `csrftoken` + `clienttype=web` header）。无 cookie 直接 403。
- 同时严重依赖 **AWS WAF** + **Cloudflare** 双层防护：UA 必须像 Chrome、Sec-CH-UA 全套、TLS JA3 指纹与浏览器一致——纯 `requests` 会被即拦截。
- 实际操作必须用 `curl_cffi` / `tls-client` / `playwright-stealth` 这一类带 JA3 模拟的库。

### 1.3 更新频率 & 限流

- Web 前端每 ~5 s 轮询一次同一个 `getOtherPosition`，因此官方允许的实际刷新粒度也大致是 **5 s**；高于 1 req/s/EncryptedUid 容易直接触发 WAF 验证码或 IP 黑名单（10–30 分钟）。
- 大规模监控（>100 个带单员）需要 **住宅 IP 池 + Cookie 池**轮换，否则 24 h 内必失效。

### 1.4 隐藏持仓（重要）

公共接口对 `positionShared=false` 的账户**完全无能为力**——这正是 galaxyquantitative 的差异化卖点。可行的（合法性递减）方案：

1. **带单员主动授权**：要求带单员把自己创建的 **Futures Lead Trader API Key**（[官方文档](https://developers.binance.com/docs/copy_trading/future-copy-trading)）填到我们系统里。Lead Trader 的 `/sapi/v1/copyTrading/futures/userStatus` 等私有端点能拿到自己投资组合的全部数据。这是 **唯一合规** 的路径。
2. **代理登录 (cookie 抓取)**：让带单员（或追随者）把自己 Binance 的 Web cookie 上传给我们；我们以他身份调 `getOtherPosition` 拿"他能看到"的页面。
3. **侧信道推断**：从公开聚合数据（资金费率、24h持仓量、Binance 大额异常成交、leaderboard 排名变化 + ROI 反推仓位）做"统计回填"——精度差、延迟高、误差大，galaxyquantitative 没明显采用。

### 1.5 现成 SDK / 开源代码

| 项目 | 说明 |
|---|---|
| [`Nunnito/Binance-Futures-Leaderboard-API`](https://github.com/Nunnito/Binance-Futures-Leaderboard-API) | FastAPI + AIOHTTP，文档全，已老化但接口名是事实标准 |
| [`tugkan/binance-futures-leaderboard-scraper`](https://github.com/tugkan/binance-futures-leaderboard-scraper) | Apify Actor，含住宅 IP 池 |
| [`tpmmthomas/binance-copy-trade-bot`](https://github.com/tpmmthomas/binance-copy-trade-bot) | Telegram bot 案例 |
| [`hgnx/binance-position-tracking-bot`](https://github.com/hgnx/binance-position-tracking-bot) | 实时监控 + TG 通知 |
| [`MarcinGrabowski/binance-copy-bot`](https://github.com/MarcinGrabowski/binance-copy-bot) | 持仓快照差分算法 |
| 商业代理 | Apify、RapidAPI 都有现成 endpoint（$30-150/月起），可作为冷启动兜底 |

### 1.6 风险点

- **WAF/Cloudflare 拦截**：触发后单 IP 通常 10–30 min 冷却，严重时永封。
- **Cookie 失效**：Binance Cookie 寿命 7–30 天；需自建账户池 + 自动续期。
- **接口随时改名**：v1→v2 迁移没通知；建议至少每周 smoke test 一次。
- **法律**：单纯抓 `positionShared=true` 的公开数据为灰色但风险小；登录其他用户 cookie 属于 ToS 违规，必须有用户明示授权 + 数据加密。

---

## 2. OKX Lead Trader 信号

### 2.1 公开端点（官方文档）

OKX 在 v5 REST API 中**明确公开**了一套 `public-` 前缀的无鉴权 copytrading 端点（[OKX docs](https://www.okx.com/docs-v5/en/)），这是所有中心化交易所里对开发者最友好的：

| 用途 | URL（GET） | 鉴权 |
|---|---|---|
| 公开带单员排行 | `https://www.okx.com/api/v5/copytrading/public-lead-traders` | 无 |
| 带单员当前持仓 | `https://www.okx.com/api/v5/copytrading/public-current-subpositions?uniqueCode={code}&instType=SWAP` | 无 |
| 带单员历史持仓 | `https://www.okx.com/api/v5/copytrading/public-subpositions-history?uniqueCode={code}` | 无 |
| 带单员统计 | `https://www.okx.com/api/v5/copytrading/public-stats?uniqueCode={code}` | 无 |
| 周/日 PnL | `.../public-weekly-pnl`, `.../public-daily-pnl` | 无 |
| 偏好币种 | `.../public-preference-currency` | 无 |
| 带单员排名 | `.../public-lead-trader-ranks` | 无 |

`uniqueCode` 16 或 18 位，可在 OKX web URL `/copy-trading/account/<uniqueCode>` 中肉眼看到。

### 2.2 鉴权 / 限流

- **完全公开**，无需 OK-ACCESS-KEY/SIGN/TIMESTAMP/PASSPHRASE。
- OKX 公共端点限流：默认 **20 req/2 s / IP**（不同端点不同），超过返回 50011；推荐串行轮询 + 客户端节流。

### 2.3 数据格式（关键字段）

`public-current-subpositions` 返回 `data[]`：
```
{ instId, posSide, mgnMode, lever, openAvgPx, ccy, subPos, subPosId, openTime, markPx, uplRatio, upl }
```
> 字段名遵循 OKX v5 通用命名，可与下单接口 `/api/v5/trade/order` 直接对接。

### 2.4 私有 priapi（前端用，备用）

OKX web 还使用 `https://www.okx.com/priapi/v5/ecotrade/...` 路径渲染社交页面（更丰富的字段，包含 KOL 标签、跟单人数等），但这条不在官方文档里，长期稳定性弱于 `/api/v5/copytrading/public-*`。建议**只用官方公开端点**。

### 2.5 实时性

- **没有 WebSocket 推送带单员持仓**；只能 REST 轮询。
- 推荐 3–5 s 轮询一次（同一带单员），全平台监控 200 个带单员需要 ≥10 并发或更长间隔。

### 2.6 SDK

- Python：[`okx-sdk`](https://pypi.org/project/okx-sdk/)（含 `CopyTradingAPI` 类）、[`python-okx`](https://github.com/okxapi/python-okx)（官方）
- Node：[`okx-api`](https://github.com/tiagosiebler/okx-api)（`getCopytradingLeadOpenPositions()`、`getCopytradingLeadPositionHistory()` 等）
- 跟单下单可以用通用 OKX trade 端点（无需 copy trading 专属权限）

### 2.7 风险

- 公开接口 OKX 偶尔做 IP-level rate limit，配置稍高超阈值会被 5–10 min ban。
- 接口名稳定性高于 Binance（OKX 在 changelog 公告改动）。
- 没有"隐藏持仓"这个概念——OKX 的 lead trader 一旦上架就完全公开，无附加价值需挖掘。

---

## 3. Hyperliquid 持仓 & 订单（最关键）

### 3.1 REST `info` 端点

统一 URL：`POST https://api.hyperliquid.xyz/info`（一个 endpoint 多个 `type`）

| `type` | 用途 | 请求体 | 响应要点 |
|---|---|---|---|
| `clearinghouseState` | 用户全部 perp 持仓 + 保证金 | `{type, user, dex?}` | `assetPositions[]: {coin, szi, entryPx, leverage, unrealizedPnl, liquidationPx, marginUsed}`、`marginSummary` |
| `openOrders` | 当前挂单 | `{type, user}` | `[{coin, side, sz, limitPx, oid, timestamp}]` |
| `frontendOpenOrders` | 含扩展字段挂单 | 同上 | + `orderType, origSz, isTrigger, reduceOnly` |
| `userFills` | 历史成交（最多近 2000 条） | `{type, user, aggregateByTime?}` | `[{coin, px, sz, side, fee, tid, hash, time, closedPnl}]` |
| `userFillsByTime` | 时间段成交（≤10000 条最近） | `{type, user, startTime, endTime?}` | 同上 |
| `historicalOrders` | 历史订单（含已撤销） | `{type, user}` | `[{order, status, statusTimestamp}]` |
| `userFunding` | 资金费率结算 | `{type, user, startTime, endTime?}` | `[{time, coin, usdc, szi, fundingRate}]` |
| `webData2` | 前端聚合（持仓+订单+余额一次返回） | `{type, user}` | 大对象，1 个请求顶 ≥3 个 |

> **限流**：`/info` 端点 ~**20 req/s per IP**（社区实测），单地址连续轮询完全够用。

### 3.2 WebSocket（最重要！）

- 端点：`wss://api.hyperliquid.xyz/ws`
- 订阅消息体统一格式：
  ```
  { "method": "subscribe", "subscription": { "type": "<type>", "user": "0x..." } }
  ```

| 订阅 `type` | 推送内容 | 用途 |
|---|---|---|
| `userEvents` | **fills + funding + liquidation + nonUserCancel** 综合事件流 | 跟单最核心，一个订阅拿全部账户行为 |
| `userFills` | 成交单（含 `isSnapshot` 首帧 snapshot） | 与 userEvents.fills 重复，但可单独订 |
| `orderUpdates` | 订单状态变更（挂单/撤单/部分成交） | 跟"挂单/撤单"事件用 |
| `webData2` | 前端用户聚合状态变化 | 偷懒方案：一次拿全 |
| `allMids` | 全市场中价 | 风控参考 |
| `l2Book` / `trades` / `candle` | 行情 | 跟单 SL/TP 用 |
| `userFundings` | 资金费率结算流 | 长期风控 |
| `notification` / `userTwapSliceFills` / `userNonFundingLedgerUpdates` | 辅助 | |

实测延迟：交易从 mempool 上链 → ws 推送 < **200 ms**（HL 区块时间 0.07–1 s，验证人节点直推）。

### 3.3 能否监听全链所有交易者？

- **不能直接订阅 "所有用户 fills"**。Hyperliquid 的 ws 订阅是 per-address 设计。
- 工程绕法：
  1. 用 `meta` / `leaderboard`（参考 [Nansen Hyperliquid Leaderboard API](https://docs.nansen.ai/api/hyperliquid/hyperliquid-leaderboard) 或 hypertracker.io）拿到 Top N 地址名单（>1.6M wallets, 通常关心 Top 1000-10000）；
  2. 一个 ws 连接可订阅 ~1000 channel（实测安全值 200–500），用多连接 + 多 IP 横向扩展；
  3. 对于 "新出现的鲸鱼"，每 1 h 重跑一次 leaderboard 增量入库。

### 3.4 SDK

- **官方 Python**：[`hyperliquid-python-sdk`](https://github.com/hyperliquid-dex/hyperliquid-python-sdk) ——`pip install hyperliquid-python-sdk`，Python 3.10 only，包含 `Info` 与 `Exchange` 两个核心类，`Info.user_state(address)` 直接拿 clearinghouseState；`Info.subscribe({"type":"userEvents","user":addr}, callback)` 注册 ws 回调。
- **TypeScript**：[`nktkas/hyperliquid`](https://github.com/nktkas/hyperliquid) ——跨 runtime（Node/Deno/Bun/browser）。
- **Rust**：`hyperliquid` crate（docs.rs）；**Go**：`sonirico/go-hyperliquid`、`slicken/go_hyperliquid`。
- **Elixir**：hexdocs.pm/hyperliquid。
- 包装库：[`quantpylib.wrappers.hyperliquid`](https://quantpylib.hangukquant.com/wrappers/hyperliquid/)。

### 3.5 风险

- **极小**。无鉴权、无 Cookie、无 captcha、文档清晰、SDK 多语言。
- 唯一注意点：单 ws 连接订阅过多 address 时心跳超时；推荐每连接 ≤300 channel、双连主备。

---

## 4. 链上聪明钱（EVM + Hyperliquid）

### 4.1 Hyperliquid 上的聪明钱

**完全复用第 3 节方案**——一个地址 = 一个 ws subscription = 实时持仓 + 实时下单。这是当前唯一可以做到 "毫秒级跟踪聪明钱"的链。

发现地址来源：
- 内置：`POST /info {"type":"leaderboard"}` 或 webdata2 提供 Top traders
- 第三方：Nansen API、Hypertracker、Coinglass（350k+ addresses）、ASXN stats、Beacon Trade

### 4.2 EVM Perp DEX（GMX / Aster / Vertex / dYdX v4 / Paradex）

| DEX | 链 | 实时方案 | 历史方案 |
|---|---|---|---|
| GMX v1/v2 | Arbitrum / Avalanche | `eth_subscribe` 监听 `PositionRouter`、`Vault` 合约的 `IncreasePosition` / `DecreasePosition` 事件 | [`gmx-io/gmx-subgraph`](https://github.com/gmx-io/gmx-subgraph)（已迁去中心化 The Graph） |
| dYdX v4 | dYdX Chain (Cosmos) | gRPC `Indexer` + WebSocket `v4_subaccounts` | REST `/v4/perpetualMarkets` |
| Aster / Vertex / Paradex | 各自 L2 | 各自有 WebSocket，机制类似 Hyperliquid，需逐家适配 | — |

推荐基础设施：
- **节点**：Alchemy free tier (300M CU/月) / QuickNode (10M req/月免费) / GetBlock（含 Hyperliquid 专用端点）/ Drpc.org（多链聚合）/ 自建 Erigon。
- **索引**：The Graph 去中心化网络（旧 hosted service 已停）、Goldsky.com、Subsquid、自建 Subgraph。
- **聚合 API**：DeBank Cloud API（钱包级别仓位聚合，含主流 perp DEX）；Zerion API；Hypertracker $1999/mo Stream tier。

### 4.3 聪明钱发现 / 标签

| 服务 | 数据 | 价格 |
|---|---|---|
| [Nansen API](https://nansen.ai/api) | Smart Money tags（18+ 链 EVM+Solana+HL），perp leaderboard | ~$1500/mo 起 |
| [Arkham Intel](https://intel.arkm.com/api) | Entity-mapped 地址、whale alert、perp 开仓监控 | API 付费 + 公共信号免费 |
| Hypertracker.io | 1.6M HL 地址实时排行 | Free / Pro $99 / Stream $1999 |
| Coinglass Hyperliquid Intelligence | 350k+ 地址持仓快照、whale-alert | API 付费，含 free tier |
| 自建 | 链上 PnL 排行 + 阈值过滤（仓位 > $1M）+ 黑名单 MM/CEX hot wallet | $0 + 工程 |

### 4.4 风险

- **极低**——完全公开链上数据。
- 唯一成本是 RPC 调用量；做几百个 EOA 实时监听，免费档够用。
- 跨链桥/合约升级时事件签名可能变，需定期更新 ABI。

---

## 5. 币Coin（bicoin.com.cn / bcoin123.com）

### 5.1 产品定位与数据来源

- 币Coin 是国内最大的"合约实盘秀+跟单参考"APP，聚合 Binance/OKX 等大佬的持仓快照。
- 数据来源：**带单员主动上传自己的交易所 API Key（只读权限）**，币Coin 后端用这些 key 拉持仓再脱敏展示。
- 没有任何官方公开 API；网站和 App 之外不提供数据导出。

### 5.2 已知接入路径（按可行性递减）

1. **galaxyquantitative 模式（最务实）**：
   - 让最终用户把**自己的币Coin 账号密码**（或登录后 cookie）填到我们系统；
   - 后台用 Playwright / Selenium 代理登录 → 拿到 sessionId / token → 调币Coin 私有 REST（如 `/api/users/getDetail`, `/api/follow/list`）拉数据。
   - 风险：用户 ToS 违规 + 我方在国内合规面承担明示授权义务。

2. **直接逆向 App**：
   - 币Coin App 用 **Native 层 sign 算法**（`sign` + `data` 双参数，关键加密在 .so），需 frida + IDA 动态 hook（参考 [CSDN 逆向文章](https://blog.csdn.net/qq_31050167/article/details/131971764)）。
   - 一次性逆向成本 1–2 人周；维护成本高，每次 App 升级可能改 key。

3. **被动 Web Scraping**：
   - 币Coin Web 端（bicoin.com.cn）渲染了部分公开榜单，可用 Playwright 跑无头浏览器抓 DOM；
   - 受动态加载 + 图片化数字 + 反爬限制，吞吐很低，仅适合"低频校验"用途。

### 5.3 数据更新频率

- 币Coin 自己声明分钟级；实测大佬持仓快照刷新 ~30–60 s。
- 对跟单系统而言，币Coin 永远比交易所原生数据慢一个量级（属于"信号补充"，不是"实时源"）。

### 5.4 风险

- **法律**：代理用户账号、抓取付费内容、转售数据在国内可能触及《反不正当竞争法》第 12 条 + 《数据安全法》。建议产品上明确"用户自带 cookie，平台仅做转发"，由用户承担授权风险。
- **技术**：账号风控（多设备登录会被踢）、滑块/短信验证码、IP 限频。
- **商业**：币Coin 自己也有跟单业务，反爬意愿强；接入随时被定向封禁。

### 5.5 现成工具

- 公开 GitHub 暂未见高质量币Coin SDK（一次性脚本居多，大多过期）。
- 类比项目：Apify 上有 OKX Copytrading Scraper、Bitget Copy Trading Scraper（[apify.com/epctex/okx-copytrading-scraper](https://apify.com/epctex/okx-copytrading-scraper)），架构可借鉴。

---

## 6. 汇总表

| # | 信号源 | 公开 URL | 鉴权 | 实时性 | 数据格式 | 隐藏持仓 | 推荐 SDK | 风险 | 优先级 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Hyperliquid `info` REST | `POST https://api.hyperliquid.xyz/info` | 无 | 秒级 | JSON, `assetPositions`, `userFills` | N/A（链上无隐藏） | hyperliquid-python-sdk | 低 | **P0** |
| 2 | Hyperliquid WebSocket | `wss://api.hyperliquid.xyz/ws` | 无 | <200 ms | `userEvents` 综合事件 | N/A | 同上 | 低 | **P0** |
| 3 | OKX `public-current-subpositions` | `GET https://www.okx.com/api/v5/copytrading/public-current-subpositions?uniqueCode=...` | 无 | 3–10 s 轮询 | `data[].{instId,posSide,subPos,lever,openAvgPx,markPx,upl}` | OKX 无隐藏概念 | python-okx / okx-api | 低 | **P0** |
| 4 | EVM 链聪明钱（GMX/Aster/Vertex） | RPC `eth_subscribe logs` + 各 Subgraph | RPC API Key（多免费） | 1–3 s | `IncreasePosition` / `DecreasePosition` 等事件 | N/A | web3.py / viem | 低 | **P0** |
| 5 | Binance Leaderboard `getOtherPosition` | `POST .../bapi/futures/v2/private/future/leaderboard/getOtherPosition` | **Cookie + WAF token + 住宅 IP** | 5–30 s | `otherPositionRetList[]` | 仅当 `positionShared=true` | Nunnito/Binance-Futures-Leaderboard-API | 中-高 | P1 |
| 6 | Binance Lead Trader 私有 | `/sapi/v1/copyTrading/futures/...` | API Key + HMAC | 实时 | 含本人投资组合细节 | **能（仅本人）** | python-binance fork | 低（仅限本人授权） | P2 |
| 7 | Binance 隐藏持仓（他人） | 同 #5，但 `positionShared=false` 时拿不到 | 必须带单员授权 cookie | 不可控 | — | **只能间接** | 自研 | 高 | P2 |
| 8 | Nansen Hyperliquid Leaderboard | `POST https://api.nansen.ai/api/v1/perp-leaderboard` | `apiKey` header | 分钟级 | `trader_address, total_pnl, roi, account_value, smart_money_labels` | N/A | REST | 低 | P1 |
| 9 | Arkham Intel API | `https://intel.arkm.com/api` | API Key | 实时 | 实体标签 + 持仓 | N/A | REST | 低 | P1 |
| 10 | Coinglass Hyperliquid Whale | docs.coinglass.com（API Key 付费） | API Key | 秒级 | Whale alert + 位置 | N/A | REST | 低 | P1 |
| 11 | 币Coin Web 私有接口 | `https://www.bicoin.com.cn/api/*`（路径需逆向确认） | **用户上传账号 cookie + sign 加密** | 30–60 s | 类 JSON，含 sign+data 加密包 | "有"，但要求用户授权 | 无成熟 SDK | 高（法律+技术） | P2 |

---

## 7. 推荐技术路线（落地建议）

### 7.1 Phase 1（3 周可上线 MVP）

1. **Hyperliquid 信号链**
   - 主线：`hyperliquid-python-sdk` + `Info.subscribe(userEvents)` + Redis Stream 做事件总线；
   - 用 `clearinghouseState` 做 cold-start snapshot 然后 ws 增量；
   - 用 leaderboard / Nansen 拿出 Top 500 地址名单 + 每小时刷一次。

2. **OKX 信号链**
   - 主线：3 s 轮询 `public-current-subpositions` per uniqueCode；
   - 差分上一次快照 → 生成"开/平/调"事件 → Redis Stream；
   - 用 `public-lead-traders` 自动发现新带单员入榜。

3. **EVM 聪明钱**
   - Alchemy/QuickNode WebSocket 订阅 GMX/Aster perp 合约事件；
   - 用 EOA 白名单（人工策展 + Nansen Smart Money tag）。

4. **跟单执行**
   - Hyperliquid → `Exchange.market_open` / `Exchange.order`
   - Binance/OKX/Bitget → `ccxt` 统一封装下单（用户自己提供 API Key）

### 7.2 Phase 2（再 4–6 周）

5. **Binance Leaderboard scraper**：住宅 IP 池 + Cookie 池 + Playwright + `curl_cffi`，仅做 `positionShared=true` 部分。
6. **币Coin 代理登录**：用户上传账号 / cookie，做加密保险柜 + Playwright 后台 worker。
7. **隐藏持仓 SVIP**：要求带单员把自己的 Lead Trader API Key 填进来，或者带单员 cookie 主动上传。

### 7.3 Phase 3

8. 接入 Nansen / Arkham / Coinglass 付费 API 做"聪明钱发现层"，自动把高 PnL 地址推入 Phase 1 的监控池。

---

## 8. 引用源

### Hyperliquid 官方
- WebSocket subscriptions：https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions
- WebSocket 概览：https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket
- Info endpoint：https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint
- Perpetuals info：https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals
- Python SDK：https://github.com/hyperliquid-dex/hyperliquid-python-sdk
- 第三方文档：https://docs.chainstack.com/reference/hyperliquid-info-web-data2 / https://www.quicknode.com/docs/hyperliquid/info-endpoints/webData2

### OKX
- API guide：https://www.okx.com/docs-v5/en/
- Copy trading API zone：https://www.okx.com/en-us/campaigns/copytrading-apizone
- okx-api endpoint list：https://github.com/tiagosiebler/okx-api/blob/master/docs/endpointFunctionList.md
- okx-sdk：https://pypi.org/project/okx-sdk/
- Apify scraper：https://apify.com/epctex/okx-copytrading-scraper

### Binance
- Copy trading 官方文档：https://developers.binance.com/docs/copy_trading/Introduction
- Futures lead trader status：https://developers.binance.com/docs/copy_trading/future-copy-trading
- 旧 leaderboard endpoint 变更 issue：https://github.com/bukowa/binance-leaderboard/issues/2
- Nunnito/Binance-Futures-Leaderboard-API：https://github.com/Nunnito/Binance-Futures-Leaderboard-API
- tugkan/binance-futures-leaderboard-scraper：https://github.com/tugkan/binance-futures-leaderboard-scraper
- hgnx/binance-position-tracking-bot：https://github.com/hgnx/binance-position-tracking-bot
- spartanz51/binance_leaderboard_listener：https://github.com/spartanz51/binance_leaderboard_listener

### 链上 / 聪明钱
- Nansen API：https://nansen.ai/api
- Nansen Hyperliquid leaderboard：https://docs.nansen.ai/api/hyperliquid/hyperliquid-leaderboard
- Arkham API：https://intel.arkm.com/api
- HyperTracker：https://hypertracker.io/
- Coinglass Hyperliquid：https://www.coinglass.com/hyperliquid
- Coinglass API：https://www.coinglass.com/CryptoApi
- QuickNode Hyperliquid whale guide：https://www.quicknode.com/guides/hyperliquid/real-time-hyperliquid-whale-alert-bot
- GetBlock Hyperliquid guide：https://docs.getblock.io/guides/build-a-real-time-hyperliquid-whale-tracker-bot-with-getblock
- kukapay/hyperliquid-whalealert-mcp：https://github.com/kukapay/hyperliquid-whalealert-mcp
- kiyoshi-work/hyperliquid-tracker：https://github.com/kiyoshi-work/hyperliquid-tracker
- GMX subgraph：https://github.com/gmx-io/gmx-subgraph

### 币Coin
- 产品介绍：https://cryptotradingcafe.com/bicoin/
- 接口加密分析（部分付费墙）：https://blog.csdn.net/qq_31050167/article/details/131971764
- 同类参考（OKX/Bitget）：https://apify.com/brilliant_gum/bitget-scraper、https://apify.com/epctex/okx-copytrading-scraper

### 反爬基础设施
- AWS WAF token：https://github.com/xKiian/awswaf
- Scrapfly bypass：https://scrapfly.io/bypass
- Cloudflare bypass 综述：https://asadfix.github.io/scraping-guide/
