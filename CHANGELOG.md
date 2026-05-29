# Changelog

本项目重要变更记录于此。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### 公开营销站全新设计 + 国际化（2026-05-29）

#### Added
- **营销站全新视觉方向 Institutional Clarity**（Swiss Editorial 亮色）落地 Vue：新增 `Home` / `Features` / `Pricing` 三页 + `MarketingLayout` 共享外壳 + `styles/marketing.css`（`.marketing-site` 作用域 `--m-*` token）。
- **设计探索资产**：`design/marketing/` 下 3 套差异化方向高保真 HTML 原型（ONCHAIN VELOCITY / INSTITUTIONAL CLARITY / SIGNAL BRUTALISM）+ 5 维度专家评审 + 截图，最终选定 Clarity 落地。
- **中英双语 i18n**（vue-i18n，默认 `zh-CN`、可切 `en`）：per-page locale 模块 `i18n/marketing/{layout,home,features,pricing}.ts`、导航语言切换器、`<html lang>` 随 locale 同步、系统 CJK 字体兜底。
- **`usePublicTraders` composable**：营销页交易员数据接入 `tradersApi`（`mockTraders()` 种子打底 + onMounted 静默拉 live + 失败/空静默回退，公开页永不空榜）。
- **Element Plus 组件文案随 i18n 联动**：`App.vue` 用 `<el-config-provider :locale>`（computed from `useI18n().locale`）。
- **营销站响应式**：移动端 / 平板 / 桌面断点（≤960 / 768 / 640 / 420），巨号标题 `clamp()` 流体字号，定价对比矩阵窄屏转「按档堆叠卡片」。

#### Changed
- **路由**：新增 `MarketingLayout` 承载营销站亮色主题（`/`、`/features`、`/pricing`），与暗色 `PublicLayout` / 控制台严格隔离；`Home` 从 `PublicLayout` 迁至 `MarketingLayout`。
- **`api/axios.ts`**：错误拦截器支持 `config.meta.silent`，营销页静默请求失败不弹错误 toast（既有非静默行为不变）。
- **`api/traders.ts`**：`list()` 增加可选 `{ silent }`，透传给真后端请求。
- **`index.html`**：加载 Inter Tight / Newsreader / Geist Mono（保留控制台 JetBrains Mono / IBM Plex Mono）。

#### 保持不变（隔离铁律）
- 暗色 D1 Bloomberg Terminal 控制台与全局 dark 逻辑（`:root` / `tokens.css` / `global.css` / `main.ts`）零改动；亮色主题严格作用于 `.marketing-site`。

#### 验证
- `npm run build`（vue-tsc --noEmit + vite build）零类型错误通过；中英双语 × 移动/平板/桌面全路由截图核验；EP locale 切换实证；`/shop` 暗色隔离回归通过。

---

## 历史交付

- **v2 (2026-05-28)** — D1 Bloomberg Terminal 设计落地 + 实时 WebSocket 推送 + 真实市场数据源（CoinGecko / Fear&Greed / Binance Futures / CryptoPanic）。详见 [`FINAL.md`](FINAL.md)。
- **v1 (2026-05-28)** — 全栈骨架：backend (FastAPI) + signal_workers + execution_engine（5 adapter + 风控）+ frontend（Vue 3 · 16 页），101 测试通过。详见 [`STATUS.md`](STATUS.md)。
