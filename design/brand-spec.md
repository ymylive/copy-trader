# Copy Trader · Brand Spec (3 个并行设计方向)

> 采集日期：2026-05-28
> 资产完整度：方向选定后再补真实 logo

## 🎯 项目定位

- **品牌名**：Copy Trader
- **产品类**：加密合约智能跟单 SaaS / Quant Trading Console
- **核心受众**：高净值加密交易者（25-45 岁，技术型，看数据，追求执行速度）
- **品牌气质关键词**：精准 · 冷峻 · 数据感 · 毫秒级 · 跨链 · 专业可信

## 真实数据（demo 必须使用，不用 lorem ipsum）

### 平台上架交易员（demo 数据集）
| 昵称 | ID | 交易所 | 数据源 | 总盈亏 | 收益率% | 带单规模 | 夏普 | 胜率 | 回撤 | 入驻天数 |
|---|---|---|---|---|---|---|---|---|---|---|
| 茂茂大魔王 | 79346 | OKX | 币Coin | 1,343,829.94 | 14539.61% | 7618.91 USDT | --- | 34.40% | 2.57% | 2209 |
| 风火山林Trader | 369319 | Binance | 币Coin | 1,927,532.79 | 6880.06% | 89999.16 USDT | --- | 45.45% | 6.86% | 1705 |
| 牛的青山在 | 1030294 | OKX | 币Coin | 297,089.72 | 10326.49% | 13292.43 USDT | --- | 75.00% | 1.15% | 899 |
| 寒星日照 | 951891 | OKX | 币Coin | 408,565.96 | 343.37% | 138001.32 USDT | --- | 43.33% | 14.51% | 1218 |
| MaximizeSR | 4120066087544364033 | Binance | 隐藏持仓 | -319.96 (90d) | -6.03% | 46358.66 USDT | 0.06 | 51.29% | 9.15% | 653 |
| KNOTMAIN | 3779422221599733504 | Binance | 隐藏持仓 | 365,404.77 (90d) | 53.51% | NaN USDT | 3.20 | 57.83% | 13.32% | -- |
| 穩定暴擊 Crit | 4030560779244867073 | Binance | 隐藏持仓 | -102,513.70 (90d) | -57.91% | 69091.23 USDT | -0.05 | 32.76% | 69.91% | 715 |
| Melanya | 3904393221729556225 | Binance | 隐藏持仓 | 0.00 (90d) | 0.00% | 10177.62 USDT | -0.13 | 0.00% | 0.00% | 802 |

### Dashboard 市场指标（实时数值快照样本）
- BTC 报价：$74,180  / 24h: -1.97%
- 恐慌指数：22 (极度恐慌)
- 24h 爆仓：$2.89 亿  / 1h: $365 万
- OKX 合约持仓：$0  · BitMEX：$1.62 亿  · 币安：$75.05 亿
- BTC 季度溢价：OKX 正 $795  · 币安 正 $203
- 币安多空人数：1.69 (多头居多)
- BTC 资金费率：+0.010% (费率正常)
- USDT 净流入：小额流入交易所
- USDT 溢价：￥6.780  ·  0.01%
- 实盘多空人数：多 58% : 空 42%
- 实盘多空金额：多 45% : 空 55%
- 微博分析师：多 0 : 空 0
- BTC 全网多空：多 44% : 空 56%

### 账户数据
- 总资金：$32,771.35 USDT
- 累计盈亏：269,066.53
- 今日盈亏：$0.00
- 账户4(Gate) 合约账户：30,518.43 USDT
- 总资产：32,771.79 USDT
- 出口 IP：8.211.140.223 / 43.153.149.108 / 101.36.104.169 / 47.245.8.141
- UID：52494073
- 服务剩余：220 天 13 小时

### 跟单配置完整字段（20+，必须 1:1 还原）
**资金管理模式**（3 选 1）：固定金额 / 全仓跟单 / 复利滚动

**基础设置**：
- 跟单倍率（数字）
- 启动跟单设置：不复制 / 仅复制浮亏持仓 / 复制所有持仓
- 持仓方向限制：无限制 / 只开多单 / 只开空单
- 开仓触发条件：市价 / 持仓均价限价 / 加仓价限价 + 价格优于交易员的百分比 %
- 加仓触发条件：同上

**止盈止损**：
- 持仓止盈：不启用 / 循环触发 + 平仓数量 %
- 持仓止损：同
- 跟单亏损阈值（USDT 绝对值）
- 安全垫亏损值（×）
- 触发止盈后市场价格再次回到开仓均价时重新补满仓位
- 补满仓位后允许再次止盈

**币种过滤**：黑名单 / 白名单

**通知**：
- 方式：不通知 / 邮件 / TG机器人
- 类型：下单成功 / 下单失败 / 触发风控 / 止盈止损 / 交易员保证金变动

### 6 类信号源（必须呈现为 tabs）
- 全部 / 币安 / 聪明钱 / 欧易 / Bitget / 币Coin / Hyperbot

### 头像图（真图，使用 Unsplash / Wikimedia Commons / DiceBear）
- 推荐用 DiceBear API 生成确定性头像：`https://api.dicebear.com/7.x/identicon/svg?seed=茂茂大魔王&backgroundColor=...`
- 或 Picsum: `https://i.pravatar.cc/120?u={trader_id}`
- Hero 配图建议：抽象 perlin 噪点 / 数据网格 / 实拍金融 K 线图（unsplash 搜 "trading screen"）

## 三个方向各自的视觉语言

### D1 · Bloomberg Terminal · 信息建筑派
```
- 主色: #0A0E14 (石墨黑底)  +  #FFB400 (琥珀信号灯)
- 涨/跌: #22C55E / #EF4444  (终端绿/跌红)
- Mono 字阶: 11/12/14/16/24/32 px (max 32)
- 字体: 'Berkeley Mono', 'JetBrains Mono', 'IBM Plex Mono' (全场)
- 数字: tabular-nums + uppercase
- 圆角: 0px (锐角)
- 边框: 1px solid rgba(255,255,255,0.08)  (hairline)
- 表格行高: 28px (高密度)
- Hero 字号: 64px display tracking-tight
- 签名细节: 终端式 cursor 闪烁 ▌ + latency badge "<2ms" + tick 时序 sparkline
- 反 slop: 无圆角、无渐变、无 emoji、无图标装饰
```

### D2 · Linear × Hyperliquid · 运动诗学派
```
- 主色: #0B0B12 (Obsidian)  +  #3F8EFC (Electric Blue) + #A78BFA (Quantum Violet)
- 强调: 涨 #34D399 / 跌 #F87171
- 玻璃: rgba(255,255,255,0.04) bg + backdrop-blur(20px) + 1px rgba(255,255,255,0.08) border
- 字阶: 12/14/16/20/28/40/56/72 px
- 字体: 标题 'Aeonik' / 'Söhne' / Inter Display; 数字 'Söhne Mono' / 'JetBrains Mono'
- 圆角: 12px 主卡片 / 8px 控件 / 24px 弹窗
- 签名: 渐变光 orb / 数字滚动器 odometer / hover 时呼吸光晕 / Apple 弱衬线斜体引语
- 动效: hero 入场 stagger 80ms, 卡片 hover lift -4px, 数字 count-up
- 反 slop: 不用 emoji，不用 default Inter 全场，玻璃卡片仅 hero/弹窗用，主体仍是实体
```

### D3 · Stripe Editorial · 极简主义派
```
- 主色: 暗模式 #0F1419 (深墨)  +  亮模式 #FAFAF8 (纸白)
- 单点 accent: #0F766E (深 emerald)
- 涨/跌: #15803D / #991B1B (深绿 / 暗红)
- Neutral: 11 级灰阶 #161A20 → #F7F7F4
- 字阶: 12/13/14/16/18/22/30/48 px
- 字体: 标题 'Söhne Halbfett'; body 'Söhne Buch'; 数字 'Söhne Mono'; 引语 'Tiempos Headline Italic'
- 圆角: 4px (统一)
- 边框: 1px solid rgba(255,255,255,0.06)
- 间距: 极大 padding (24/32/48/64)
- 签名: 黑色 hairline 分组、衬线斜体段落引语、column count 报刊感、单点 emerald inline mark
- 反 slop: 0 装饰图标、0 渐变、0 emoji，全靠排印 + 留白决出层次
```

## 给三位 agent 的统一交付要求

每个 demo HTML 文件：`/Users/cornna/project/copy_trader/design/direction_{1,2,3}.html`

必含 4 个 sections（顶部 sticky tab 切换）：
1. **🚀 Hero 公开页** — slogan + 3 个数据徽章 + 主 CTA + 抽象配图
2. **📊 Dashboard 控制台** — 4 张顶部资产卡 + 净值曲线 (ECharts) + 6+ 个市场指标 widget + 实时新闻流
3. **👥 交易员广场** — 6 类信号源 tab + 6-8 张交易员卡片（含全部字段）+ 1 张"启动跟单"按钮
4. **⚙️ 跟单配置弹窗** — 20+ 字段完整展开

技术：
- 单文件 HTML，CDN 加载 ECharts + dayjs
- 字体走 Google Fonts CDN（JetBrains Mono / Inter / Sohne 替代为 Inter Tight、衬线用 Newsreader / EB Garamond）
- 真实头像：`https://api.dicebear.com/7.x/identicon/svg?seed={name}`
- 1440×900 视口（macbook standard）
- Playwright 截屏：`/Users/cornna/project/copy_trader/design/screenshots/direction_{N}_{section}.png`
- 一定要用真实数据（上方表格），不要伪造数字

反 slop 红线：
- ❌ 不要紫渐变球 + 大字 + emoji 那种 AI 通用 hero
- ❌ 不要 Material-style 左 border accent card
- ❌ 不要 SVG 手画的人脸
- ❌ 不要"圆角 +微立体阴影 + 装饰 icon" 套路
- ✅ 用 hairline 1px divider 替代厚边框
- ✅ 数字必 tabular-nums
- ✅ 涨跌色严格遵守 D1/D2/D3 各自的色卡
- ✅ 每个细节问"为什么必要"——不必要的删
