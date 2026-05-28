<script setup lang="ts">
import { onMounted, ref, nextTick, computed, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { BLOOMBERG_THEME } from '@/charts/echartsTheme'
import LiveLog from '@/components/LiveLog.vue'
import EditorialQuote from '@/components/EditorialQuote.vue'
import { dashboardApi } from '@/api/dashboard'
import { formatUTC } from '@/utils/format'

const chartEl = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null
const execFeed = ref<any[]>([])
const renderTs = ref(formatUTC())
const utcLive = ref(formatUTC())

let clockTimer: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  execFeed.value = (await dashboardApi.execFeed()) as any[]
  await nextTick()
  drawCandles()
  clockTimer = setInterval(() => { utcLive.value = formatUTC() }, 1000)
})
onBeforeUnmount(() => { if (clockTimer) clearInterval(clockTimer) })

function pad(n: number) { return n < 10 ? '0' + n : String(n) }
function genCandles(n: number, start: number) {
  let p = start
  const out: number[][] = []
  for (let i = 0; i < n; i++) {
    const o = p
    const ch = (Math.sin(i * 0.37 + 1) - 0.1) * 180
    const c = o + ch
    const h = Math.max(o, c) + Math.abs(Math.cos(i)) * 60
    const l = Math.min(o, c) - Math.abs(Math.sin(i)) * 60
    out.push([+o.toFixed(2), +c.toFixed(2), +l.toFixed(2), +h.toFixed(2)])
    p = c
  }
  return out
}
function genTimes(n: number) {
  const base = new Date('2026-05-28T10:00:00Z').getTime()
  const out: string[] = []
  for (let i = 0; i < n; i++) {
    const d = new Date(base + i * 60000)
    out.push(pad(d.getUTCHours()) + ':' + pad(d.getUTCMinutes()))
  }
  return out
}

function drawCandles() {
  if (!chartEl.value) return
  chart = echarts.init(chartEl.value, BLOOMBERG_THEME, { renderer: 'canvas' })
  const candles = genCandles(60, 74000)
  chart.setOption({
    backgroundColor: 'transparent',
    grid: { left: 42, right: 48, top: 14, bottom: 24 },
    xAxis: {
      type: 'category',
      data: genTimes(60),
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisTick: { show: false },
      axisLabel: { color: '#6B7280', fontSize: 9, interval: 9 }
    },
    yAxis: {
      scale: true,
      position: 'right',
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#6B7280', fontSize: 9, formatter: (v: number) => v.toFixed(0) },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0A0E14',
      borderColor: '#FFB400',
      borderWidth: 1,
      textStyle: { color: '#E6E8EA', fontFamily: 'JetBrains Mono', fontSize: 11 }
    },
    series: [{
      type: 'candlestick',
      data: candles,
      itemStyle: {
        color: '#22C55E', color0: '#EF4444',
        borderColor: '#22C55E', borderColor0: '#EF4444',
        borderWidth: 1
      },
      barWidth: '62%'
    }]
  })
  window.addEventListener('resize', () => chart?.resize())
}

const tierData = [
  { name: 'STARTER',  price: 80,  period: '/MO', features: ['1 ACCOUNT', '2 COPY SLOTS', 'STANDARD QUEUE', 'EMAIL ALERTS', 'COMMUNITY DOCS'] },
  { name: 'PRO',      price: 240, period: '/MO', features: ['4 ACCOUNTS', '6 COPY SLOTS', 'PRIORITY QUEUE (<2MS)', 'TELEGRAM ALERTS', 'BICOIN COOKIE'] },
  { name: 'ENTERPRISE', price: '—', period: 'CONTACT', features: ['UNLIMITED ACCOUNTS', 'UNLIMITED COPIES', 'BINANCE FAST EXEC 0.03S', 'DEDICATED SLA', 'CUSTOM REGION VPC'] }
]
</script>

<template>
  <div class="home">
    <!-- HERO -->
    <section class="hero">
      <div class="sec-head">
        <div class="sec-title"><span class="amber">01 //</span> PUBLIC LANDING · MAIN ENTRY</div>
        <div class="sec-coord">REF 0x4A.HERO · {{ renderTs }}</div>
      </div>

      <div class="hero-grid">
        <!-- LEFT -->
        <div class="hero-left">
          <div class="hero-meta">
            <span class="amber">●</span>
            <span>SYS / COPY-TRADING-ENGINE</span>
            <span class="sep">|</span>
            <span>BUILD 8941</span>
            <span class="sep">|</span>
            <span>PRESS [TAB] TO NAVIGATE</span>
          </div>

          <h1 class="hero-h1">
            cross-exchange copy trading.<br/>
            with <span class="em">terminal-grade</span> execution.<span class="cursor">▌</span>
          </h1>

          <p class="hero-sub">
            latency under 2 ms <span class="sep">·</span> 5 venues <span class="sep">·</span> 6 signal sources <span class="sep">·</span> zero profit share<br/>
            engineered for the high-frequency tail of crypto derivatives. okx, binance, bitget, gate, hyperliquid — one console, one execution path.
          </p>

          <div class="hero-badges">
            <div class="hbadge">
              <div class="lbl">ACTIVE FOLLOWERS</div>
              <div class="val">15 847</div>
              <div class="delta">+312 / 24H</div>
            </div>
            <div class="hbadge">
              <div class="lbl">MEDIAN EXECUTION</div>
              <div class="val">&lt;2<span class="unit">ms</span></div>
              <div class="delta amber">P99 4.1 MS</div>
            </div>
            <div class="hbadge">
              <div class="lbl">30D COPIED VOLUME</div>
              <div class="val">$284M<span class="unit">+</span></div>
              <div class="delta">+18.4% MoM</div>
            </div>
          </div>

          <div class="hero-ctas">
            <router-link to="/register" class="btn-cta primary">START TRIAL <span class="arrow">→</span></router-link>
            <router-link to="/tutorial" class="btn-cta ghost">READ DOCS <span class="arrow">↗</span></router-link>
          </div>

          <div class="hero-footnote">
            <span><span class="num">[01]</span> SOC 2 TYPE II</span>
            <span><span class="num">[02]</span> ZERO PROFIT SHARE</span>
            <span><span class="num">[03]</span> NON-CUSTODIAL · API KEYS LOCAL</span>
            <span><span class="num">[04]</span> 99.97% UPTIME · 90D</span>
          </div>
        </div>

        <!-- RIGHT -->
        <div class="hero-right">
          <div class="panel">
            <div class="panel-head">
              <span>BTC-USDT-SWAP · OKX · 1M</span>
              <div class="right">
                <span class="badge amber"><span class="dot"></span>LIVE</span>
                <span>LAT 1.8MS</span>
              </div>
            </div>
            <div ref="chartEl" class="hero-chart"></div>
          </div>

          <div class="panel">
            <div class="panel-head">
              <span>EXECUTION FEED · /var/log/exec.tail</span>
              <div class="right">
                <span>247 EVT/S</span>
                <span class="badge green"><span class="dot"></span>STREAM</span>
              </div>
            </div>
            <div class="panel-body">
              <LiveLog :rows="execFeed" max-height="200px" />
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- TRUST (D3 editorial style) -->
    <section class="trust">
      <div class="sec-head">
        <div class="sec-title"><span class="amber">02 //</span> ENGINEERING PHILOSOPHY</div>
        <div class="sec-coord">REF 0x4B.TRUST</div>
      </div>
      <div class="trust-grid">
        <EditorialQuote cite="— design doctrine · copy//trader engine">
          We are not building a marketing website. We are building a console.
          Every pixel renders a decision the operator already wants to make —
          faster, with fewer keystrokes, fewer surprises.
        </EditorialQuote>
        <EditorialQuote cite="— execution layer · latency budget">
          Two milliseconds is not a marketing claim, it is a service-level objective
          enforced by tick-time scheduling, colocated egress, and a single execution
          path per venue. Everything else is overhead.
        </EditorialQuote>
      </div>
    </section>

    <!-- PRICING -->
    <section class="pricing">
      <div class="sec-head">
        <div class="sec-title"><span class="amber">03 //</span> PRICING · FLAT &amp; TRANSPARENT</div>
        <div class="sec-coord">NO PROFIT SHARE · MONTH-TO-MONTH</div>
      </div>
      <table class="price-table">
        <thead>
          <tr>
            <th>PLAN</th>
            <th class="r">PRICE</th>
            <th>INCLUDES</th>
            <th class="r">CTA</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="tier in tierData" :key="tier.name">
            <td class="tier-name">{{ tier.name }}</td>
            <td class="r price">
              <template v-if="typeof tier.price === 'number'">
                ${{ tier.price.toFixed(2) }}<span class="period">{{ tier.period }}</span>
              </template>
              <template v-else>
                <span class="amber">{{ tier.price }}</span><span class="period"> {{ tier.period }}</span>
              </template>
            </td>
            <td class="feats">
              <span v-for="f in tier.features" :key="f" class="feat">{{ f }}</span>
            </td>
            <td class="r">
              <router-link to="/shop" class="link-cta">SUBSCRIBE →</router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- FOOTER -->
    <footer class="ct-footer">
      <div class="foot-row">
        <div class="foot-col">
          <div class="foot-h">PRODUCT</div>
          <a>TRADER SQUARE</a>
          <a>WATCHLIST</a>
          <a>HYPERLIQUID VAULT</a>
        </div>
        <div class="foot-col">
          <div class="foot-h">RESOURCES</div>
          <a>DOCS</a>
          <a>API REFERENCE</a>
          <a>CHANGELOG</a>
        </div>
        <div class="foot-col">
          <div class="foot-h">VENUES</div>
          <a href="https://www.binance.com" target="_blank">BINANCE ↗</a>
          <a href="https://www.okx.com" target="_blank">OKX ↗</a>
          <a href="https://hyperliquid.xyz" target="_blank">HYPERLIQUID ↗</a>
          <a href="https://www.bicoin.com.cn" target="_blank">BICOIN ↗</a>
        </div>
        <div class="foot-col">
          <div class="foot-h">STATUS</div>
          <div class="status-line"><span class="dot green"></span>HOST · ONLINE</div>
          <div class="status-line"><span class="dot green"></span>SIGNAL BUS · 3.2K OPS/S</div>
          <div class="status-line"><span class="dot amber"></span>LATENCY · 1.8MS</div>
          <div class="status-line clock">{{ utcLive }}</div>
        </div>
      </div>
      <div class="copyright">© 2026 COPY//TRADER · CROSS-EXCHANGE COPY TRADING TERMINAL · ALL RIGHTS RESERVED</div>
    </footer>
  </div>
</template>

<style scoped>
.home {
  padding: 18px 18px 36px;
  display: flex;
  flex-direction: column;
  gap: 48px;
}

/* HERO */
.hero { min-height: 100vh; display: flex; flex-direction: column; }
.hero-grid {
  display: grid;
  grid-template-columns: 1.35fr 1fr;
  gap: 24px;
  flex: 1;
}
.hero-left { display: flex; flex-direction: column; }
.hero-meta {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  margin-bottom: 18px;
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
  font-family: var(--ct-font-mono);
}
.hero-meta .amber { color: var(--ct-amber); }
.hero-meta .sep { color: var(--ct-text-dim); }

.hero-h1 {
  font-size: 60px;
  line-height: 1.04;
  letter-spacing: -0.025em;
  font-weight: 500;
  color: var(--ct-text);
  font-family: var(--ct-font-mono);
  margin: 0;
}
.hero-h1 .em { color: var(--ct-amber); }
.cursor {
  color: var(--ct-amber);
  animation: blink 1s steps(2, start) infinite;
  font-weight: 700;
  margin-left: 2px;
}
@keyframes blink { to { visibility: hidden; } }

.hero-sub {
  margin-top: 22px;
  font-size: 14px;
  color: var(--ct-text-2);
  letter-spacing: 0.01em;
  max-width: 560px;
  line-height: 1.6;
  font-family: var(--ct-font-mono);
}
.hero-sub .sep { color: var(--ct-text-dim); margin: 0 6px; }

.hero-badges {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
  margin-top: 36px;
  border-top: 1px solid var(--ct-divider);
  border-bottom: 1px solid var(--ct-divider);
}
.hbadge { padding: 18px 16px; border-right: 1px solid var(--ct-divider); }
.hbadge:last-child { border-right: 0; }
.hbadge .lbl {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 8px;
}
.hbadge .val {
  font-size: 30px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--ct-text);
  font-variant-numeric: tabular-nums;
}
.hbadge .val .unit {
  font-size: 14px;
  color: var(--ct-text-3);
  margin-left: 4px;
  letter-spacing: 0;
}
.hbadge .delta {
  font-size: 11px;
  color: var(--ct-pos);
  margin-top: 6px;
  letter-spacing: 0.02em;
  font-variant-numeric: tabular-nums;
}
.hbadge .delta.amber { color: var(--ct-amber); }

.hero-ctas { margin-top: 28px; display: flex; gap: 12px; }
.btn-cta {
  height: 40px;
  padding: 0 18px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-weight: 500;
  border: 1px solid var(--ct-amber);
  background: var(--ct-amber);
  color: #0A0E14;
  font-family: var(--ct-font-mono);
  transition: filter 120ms linear;
}
.btn-cta:hover { filter: brightness(1.08); }
.btn-cta.ghost {
  background: transparent;
  color: var(--ct-text);
  border-color: var(--ct-divider-strong);
}
.btn-cta.ghost:hover { border-color: var(--ct-amber); color: var(--ct-amber); }

.hero-footnote {
  margin-top: 28px;
  font-size: 10px;
  color: var(--ct-text-dim);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  font-family: var(--ct-font-mono);
}
.hero-footnote .num { color: var(--ct-text-2); margin-right: 4px; }

.hero-right { display: flex; flex-direction: column; gap: 14px; }
.panel { border: 1px solid var(--ct-divider); background: var(--ct-bg-2); }
.panel-head {
  height: 28px;
  padding: 0 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--ct-divider);
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.panel-head .right { display: flex; gap: 8px; align-items: center; }
.panel-body { padding: 12px; }
.hero-chart { height: 260px; }

/* TRUST */
.trust-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 36px;
  padding: 12px 0 36px;
}

/* PRICING */
.price-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--ct-font-mono);
  font-size: 12px;
  border: 1px solid var(--ct-divider);
}
.price-table th,
.price-table td {
  padding: 14px 14px;
  text-align: left;
  border-bottom: 1px solid var(--ct-divider);
  vertical-align: top;
}
.price-table th {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  background: var(--ct-bg-2);
  font-weight: 500;
}
.price-table .r { text-align: right; }
.tier-name {
  color: var(--ct-amber);
  font-weight: 600;
  letter-spacing: 0.1em;
  font-size: 14px;
}
.price-table .price {
  color: var(--ct-text);
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.01em;
  font-variant-numeric: tabular-nums;
}
.price-table .period {
  font-size: 10px;
  color: var(--ct-text-3);
  margin-left: 4px;
  letter-spacing: 0.06em;
}
.feats { display: flex; flex-wrap: wrap; gap: 6px; }
.feat {
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border: 1px solid var(--ct-divider-strong);
  color: var(--ct-text-2);
  padding: 2px 8px;
}
.link-cta {
  color: var(--ct-amber);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

/* FOOTER */
.ct-footer {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--ct-divider);
  font-family: var(--ct-font-mono);
}
.foot-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 32px;
  padding-bottom: 24px;
}
.foot-h {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  margin-bottom: 12px;
}
.foot-col a {
  display: block;
  color: var(--ct-text-2);
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 4px 0;
}
.foot-col a:hover { color: var(--ct-amber); }
.status-line {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 11px;
  color: var(--ct-text-2);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.status-line .dot { width: 6px; height: 6px; }
.status-line .dot.green { background: var(--ct-pos); }
.status-line .dot.amber { background: var(--ct-amber); }
.status-line.clock {
  color: var(--ct-amber);
  margin-top: 8px;
  border-top: 1px solid var(--ct-divider);
  padding-top: 8px;
}
.copyright {
  text-align: center;
  color: var(--ct-text-dim);
  font-size: 10px;
  padding-top: 18px;
  border-top: 1px solid var(--ct-divider);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

@media (max-width: 1100px) {
  .hero-grid { grid-template-columns: 1fr; }
  .hero-h1 { font-size: 42px; }
}
@media (max-width: 768px) {
  .trust-grid, .foot-row { grid-template-columns: 1fr; }
  .hero-h1 { font-size: 32px; }
  .hbadge .val { font-size: 22px; }
}
</style>
