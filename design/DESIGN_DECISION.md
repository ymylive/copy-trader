# 设计方向决策（落地方案）

> 决策时间：2026-05-28
> 决策依据：3 个设计方向 demo + 专家级 5 维度评审

## 选定方向

**主方向：D1 Bloomberg Terminal · 信息建筑派**（47/50 分）

> "我们在做的不是营销网站，是一台控制台。" —— 设计哲学

## 落地策略：两域分治

| 区域 | 美学 | 原因 |
|---|---|---|
| **控制台**（登录后）| **D1 Bloomberg Terminal 主导** | 高密度数据 + 多账号多信号源 + 实时市场指标，需要终端式信息密度 |
| **公开站**（首页/Pricing/Tutorial/Docs）| **D1 主调 + D3 Editorial 衬线引语点缀** | 公开站要兼顾"机构级可信"感，D3 的留白 + 衬线引语用于 brand statement |
| **过渡动效** | 借用 D2 的数字 count-up + 卡片 hover lift | 让数据"活"起来，但不引入玻璃质感（与终端美学冲突）|

## 设计 Tokens 规范

```css
/* ── D1 主色板（控制台 + 全局 base）── */
:root {
  /* surface */
  --ct-bg:           #0A0E14;          /* graphite black */
  --ct-bg-elevated:  #11151D;
  --ct-bg-hover:     #161A24;
  --ct-divider:      rgba(255,255,255,0.08);  /* hairline */

  /* signal color */
  --ct-amber:        #FFB400;          /* primary signal */
  --ct-amber-dim:    #C68800;
  --ct-amber-soft:   rgba(255,180,0,0.12);

  /* semantic */
  --ct-pos:          #22C55E;          /* terminal green */
  --ct-neg:          #EF4444;          /* terminal red */
  --ct-warn:         #FB923C;
  --ct-info:         #60A5FA;

  /* text */
  --ct-text:         #E6E8EB;
  --ct-text-2:       #9CA3AF;
  --ct-text-3:       #6B7280;
  --ct-text-dim:     #4B5563;

  /* typography */
  --ct-font-mono:    'JetBrains Mono', 'IBM Plex Mono', ui-monospace, monospace;
  --ct-font-serif:   'Newsreader', 'EB Garamond', Georgia, serif;  /* 仅引语 */

  /* radius */
  --ct-radius:       0px;              /* 一律锐角 */
  --ct-radius-soft:  2px;              /* 极少例外（chip） */

  /* spacing 4-base */
  --ct-sp-1: 4px;  --ct-sp-2: 8px;   --ct-sp-3: 12px;
  --ct-sp-4: 16px; --ct-sp-5: 24px;  --ct-sp-6: 32px;
  --ct-sp-8: 48px; --ct-sp-10: 64px;

  /* type scale */
  --ct-fs-xs:  11px;  --ct-fs-sm: 12px;  --ct-fs-base: 14px;
  --ct-fs-md:  16px;  --ct-fs-lg: 24px;  --ct-fs-xl:   32px;
  --ct-fs-2xl: 48px;  --ct-fs-3xl: 64px;

  /* effects */
  --ct-shadow-none: none;
  --ct-blink-cursor: 1s steps(1) infinite;
}

/* 全局基础 */
* { box-sizing: border-box; }
html, body {
  font-family: var(--ct-font-mono);
  font-variant-numeric: tabular-nums;
  letter-spacing: 0;
  background: var(--ct-bg);
  color: var(--ct-text);
}

/* 标签统一 uppercase + letter-spacing */
.label, [data-label] {
  font-size: var(--ct-fs-xs);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ct-text-3);
}

/* 数字主体 */
.num {
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum' 1;
}
.num.pos { color: var(--ct-pos); }
.num.neg { color: var(--ct-neg); }

/* hairline divider */
.hairline { border: 1px solid var(--ct-divider); }
.hairline-b { border-bottom: 1px solid var(--ct-divider); }

/* cursor blink */
.cursor::after {
  content: '▌';
  color: var(--ct-amber);
  animation: blink var(--ct-blink-cursor);
}
@keyframes blink { 50% { opacity: 0; } }

/* status bar (顶栏) */
.statusbar {
  display: flex;
  gap: 16px;
  height: 22px;
  font-size: 11px;
  color: var(--ct-text-3);
  border-bottom: 1px solid var(--ct-divider);
  padding: 0 16px;
  align-items: center;
}

/* button — 锐角 */
.btn {
  border-radius: 0;
  font-family: var(--ct-font-mono);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: 12px;
  padding: 8px 14px;
  border: 1px solid var(--ct-divider);
  background: transparent;
  color: var(--ct-text);
  cursor: pointer;
}
.btn.primary {
  background: var(--ct-amber);
  color: var(--ct-bg);
  border-color: var(--ct-amber);
}
.btn.primary:hover { background: var(--ct-amber-dim); }

/* serif quote (D3 公开站 only) */
.editorial-quote {
  font-family: var(--ct-font-serif);
  font-style: italic;
  font-size: 22px;
  line-height: 1.4;
  border-left: 1px solid var(--ct-amber);
  padding-left: 24px;
  color: var(--ct-text-2);
}
```

## Vue 3 工程实施清单

按子目录列出 todo：

### 1️⃣ `frontend/src/styles/`
- [ ] **重写** `tokens.css` — 用上面的完整 D1 token 替换原 emerald 配色
- [ ] **重写** `global.css` — base 字体改为 JetBrains Mono、`font-variant-numeric: tabular-nums` 全局、`button { border-radius: 0 }` 全局
- [ ] **新增** `terminal.css` — 提取 demo direction_1.html 里所有的 status bar / log stream / cursor blink / hairline 工具类

### 2️⃣ `frontend/index.html`
- [ ] Google Fonts link 改为 JetBrains Mono + IBM Plex Mono + Newsreader

### 3️⃣ `frontend/src/components/`

| 组件 | 改动 |
|---|---|
| `TraderCard.vue` | 重写：参考 `direction_1.html` 第 traders section 的卡片样式。0 圆角、hairline、琥珀大数字、INITIATING blink、STALE 50% opacity |
| `CopyConfigDialog.vue` | 重写：参考 demo 的 config section。5 个 form group 编号 01-05、`MODE: FIXED AMOUNT` 按钮组、`CFG_HASH 0xXXXX` 底部签名 |
| `PositionTable.vue` | 1px hairline 表格、`tabular-nums`、行高 28px、表头 uppercase 11px |
| `IpAllowlist.vue` | mono 等宽展示 IP，前缀 `EGRESS:` |
| `RechargeDialog.vue` | TRC20/ERC20 切换走 chip 按钮（锐角描边） |
| `StatusBar.vue` *(新增)* | 顶部 22px 状态条：`HOST online · REDIS 3.2K ops/s · WS 1247 sub · CPU 12% · LATENCY 1.8MS · UTC 2026-05-28 18:14` |
| `LiveLog.vue` *(新增)* | Hero / Dashboard 用的终端日志流组件，5 色分级（FILL/SIGNAL/SUBSCR/WARN/REJECT） |
| `Sparkline.vue` *(新增)* | 80×16 px 单色琥珀 sparkline，每张交易员卡用 |
| `EditorialQuote.vue` *(新增)* | 公开站专用的衬线斜体引语段 |

### 4️⃣ `frontend/src/views/console/`

| 页面 | 改动 |
|---|---|
| `Layout.vue` | 侧边栏改为 22px status bar + 52px 主 nav 的双层结构；侧栏背景 `#0A0E14`；菜单项 uppercase mono |
| `Dashboard.vue` | 重写：4 张资产卡 hairline 分隔 + 60 天 ECharts 净值曲线（琥珀单色 + 极弱 area gradient）+ 8 个 widget grid + LiveLog 新闻流 |
| `Accounts.vue` | 4 个账户 tab 加底部 underline、API Key/Secret mono 长串、修改杠杆 chip 按钮 |
| `TraderSquare.vue` | 7 个 venue tab + filter chips (LISTED ONLY / SHARPE ≥ 1 / DD ≤ 15% / SCALE ≥ 10K) + 4×2 grid |
| `Positions.vue` | 持仓表格 1px hairline、`一键全平` btn primary 琥珀 |
| `System.vue` | 通知渠道改为 chip-radio + `SEND TEST` 按钮 + 软件更新进度条用琥珀进度块 |
| `ExchangeWatchlist.vue` | "全域跟单 / Cookie 跟单 SVIP" 改为 chip 切换 |
| `BicoinWatchlist.vue` | 登录表单 underline input style |

### 5️⃣ `frontend/src/views/home/Home.vue`（公开站）

- [ ] Hero：cross-exchange copy trading. with terminal-grade execution.（mono lowercase 56px）+ 3 数据徽章 + K 线 + LiveLog
- [ ] Trust section：D3 editorial 风格的衬线斜体引语 1-2 段
- [ ] Pricing：Bloomberg 风格表格（hairline，无背景填充）
- [ ] Footer：UTC 时钟 + 服务状态点

### 6️⃣ `frontend/src/views/auth/`
- [ ] Login / Register：mono 字体、琥珀 active state、`▌ AUTHENTICATING...` blink 风格 loading

### 7️⃣ `frontend/src/views/shop|wallet|invite|profile/`
- [ ] 全部按 D1 token 重写表格 + 卡片 + 按钮
- [ ] 商品价格使用 `mono $80.00 /MO` 格式

### 8️⃣ ECharts 主题
- [ ] **新增** `frontend/src/charts/echartsTheme.ts` — 注册全局 Bloomberg theme：背景透明、琥珀单色 line、grid `rgba(255,255,255,0.04)`、tooltip 黑底白字 hairline border、字体 JetBrains Mono

## 实施顺序（建议）

1. **第一波（基础设施）**：tokens.css + global.css + terminal.css + ECharts theme
2. **第二波（核心组件）**：StatusBar / TraderCard / CopyConfigDialog / Sparkline / LiveLog
3. **第三波（控制台页面）**：Dashboard → TraderSquare → Accounts → Positions → System
4. **第四波（公开站）**：Home + Pricing + Tutorial + Auth
5. **第五波（其余页面）**：Shop / Wallet / Invite / Profile
6. **验证**：Playwright 跑 1440×900 截图，对比 demo direction_1.html 视觉一致性

## 风格自检（实施时反复对照）

每提交一个组件，问自己：
- [ ] 字体是 JetBrains Mono 不是 Inter？
- [ ] `border-radius: 0` 严格遵守？
- [ ] 数字有 `font-variant-numeric: tabular-nums`？
- [ ] 没有任何 box-shadow？
- [ ] 没有 emoji 装饰？
- [ ] 千分位是空格分隔不是逗号？
- [ ] 至少 1 个签名细节（cursor、UTC、latency badge、status bar、log）？

## 参考资产

| 文件 | 用途 |
|---|---|
| `design/direction_1.html` | **D1 落地的视觉真理表** — 任何样式不确定就 grep 这里 |
| `design/direction_3.html` | D3 衬线引语的样板（仅 marketing 段落用） |
| `design/screenshots/direction_1_*.png` | Playwright 验证基准截图 |
| `design/brand-spec.md` | 真实数据来源（交易员、市场指标、配置字段） |
