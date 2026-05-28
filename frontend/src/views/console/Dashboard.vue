<script setup lang="ts">
import { onMounted, ref, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { dashboardApi } from '@/api/dashboard'
import { BLOOMBERG_THEME } from '@/charts/echartsTheme'
import LiveLog from '@/components/LiveLog.vue'
import Sparkline from '@/components/Sparkline.vue'
import { formatNum, formatSigned, formatPctSigned, formatUTC } from '@/utils/format'

const overview = ref<any>({
  total_assets: 0, account_count: 0, active_count: 0, paused_count: 0, err_count: 0,
  cumulative_pnl: 0, cumulative_pct: 0, today_pnl: 0, today_orders: 0, today_open: 0,
  since: ''
})
const widgets = ref<any>({})
const news = ref<any[]>([])
const series = ref<any[]>([])
const execFeed = ref<any[]>([])

const chartEl = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

const renderTs = ref(formatUTC())

onMounted(async () => {
  overview.value  = await dashboardApi.overview()
  widgets.value   = await dashboardApi.marketWidgets()
  news.value      = (await dashboardApi.news()) as any[]
  series.value    = (await dashboardApi.pnlSeries()) as any[]
  execFeed.value  = (await dashboardApi.execFeed()) as any[]
  await nextTick()
  drawEquityChart()
})

function drawEquityChart() {
  if (!chartEl.value) return
  chart = echarts.init(chartEl.value, BLOOMBERG_THEME, { renderer: 'canvas' })
  const dates = series.value.map((d) => d.date)
  const vals = series.value.map((d) => d.value)
  chart.setOption({
    backgroundColor: 'transparent',
    grid: { left: 62, right: 24, top: 22, bottom: 30 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisTick: { show: false },
      axisLabel: { color: '#6B7280', fontSize: 9, interval: 6 }
    },
    yAxis: {
      scale: true,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: '#6B7280',
        fontSize: 9,
        formatter: (v: number) => '$' + (v / 1000).toFixed(1) + 'k'
      },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0A0E14',
      borderColor: '#FFB400',
      borderWidth: 1,
      textStyle: { color: '#E6E8EA', fontFamily: 'JetBrains Mono', fontSize: 11 },
      formatter: (p: any) =>
        p[0].axisValue + '<br/>EQUITY <span style="color:#FFB400">$' +
        Number(p[0].data).toLocaleString('en-US', { minimumFractionDigits: 2 }) +
        '</span>'
    },
    series: [{
      type: 'line',
      data: vals,
      symbol: 'none',
      smooth: false,
      lineStyle: { color: '#FFB400', width: 1.5 },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(255,180,0,0.18)' },
            { offset: 1, color: 'rgba(255,180,0,0)' }
          ]
        }
      },
      markLine: {
        symbol: 'none',
        lineStyle: { color: 'rgba(34,197,94,0.4)', type: 'dashed', width: 1 },
        data: [{
          yAxis: vals[0],
          label: {
            formatter: 'ENTRY $' + (vals[0] || 0).toFixed(0),
            color: '#22C55E',
            fontSize: 9,
            fontFamily: 'JetBrains Mono',
            position: 'insideStartTop'
          }
        }]
      }
    }]
  })
  window.addEventListener('resize', () => chart?.resize())
}

/* spark for btc */
const btcSpark = computed(() => {
  // generate deterministic-ish small wave for BTC
  const arr: number[] = []
  let v = 74180
  for (let i = 0; i < 30; i++) {
    v += v * (Math.sin(i * 0.4) * 0.006 - 0.001)
    arr.push(+v.toFixed(2))
  }
  return arr
})
</script>

<template>
  <div class="dashboard">
    <div class="sec-head">
      <div class="sec-title">
        <span class="amber">02 //</span> OPERATOR CONSOLE · ACCOUNT 4 (GATE) · STANDARD
      </div>
      <div class="sec-coord">REFRESH 1s · WS BIND ✓ · LAT 1.8MS · {{ renderTs }}</div>
    </div>

    <!-- 4 asset cells -->
    <div class="asset-row">
      <div class="asset-cell">
        <div class="k">TOTAL EQUITY / USDT</div>
        <div class="v">${{ formatNum(overview.total_assets, 0) }}<span class="unit">.{{ String(overview.total_assets.toFixed(2)).split('.')[1] }}</span></div>
        <div class="sub">ACROSS <span style="color:var(--ct-amber)">4 ACCOUNTS</span> · GATE / OKX / BINANCE / BYBIT</div>
      </div>
      <div class="asset-cell">
        <div class="k">CUMULATIVE PNL</div>
        <div class="v green">+{{ formatNum(overview.cumulative_pnl, 0) }}<span class="unit">.{{ String(overview.cumulative_pnl.toFixed(2)).split('.')[1] }}</span></div>
        <div class="sub"><span class="green">+{{ formatNum(overview.cumulative_pct, 2) }}%</span> SINCE {{ overview.since }}</div>
      </div>
      <div class="asset-cell">
        <div class="k">PNL TODAY (UTC)</div>
        <div class="v">${{ formatNum(overview.today_pnl, 0) }}<span class="unit">.00</span></div>
        <div class="sub">{{ overview.today_orders }} ORDERS · {{ overview.today_open }} OPEN · 0.00% TURN</div>
      </div>
      <div class="asset-cell">
        <div class="k">BOUND ACCOUNTS</div>
        <div class="v amber">{{ overview.account_count }}</div>
        <div class="sub">{{ overview.active_count }} ACTIVE · {{ overview.paused_count }} PAUSED · {{ overview.err_count }} ERR</div>
      </div>
    </div>

    <!-- Grid: equity chart (left) + widget grid (right) -->
    <div class="dash-grid">
      <div class="panel">
        <div class="panel-head">
          <span>EQUITY CURVE · 60D · ACCOUNT 4 (GATE)</span>
          <div class="right">
            <span class="badge amber"><span class="dot"></span>+820.65%</span>
            <span>SHARPE 2.41</span>
            <span>MAX DD 4.32%</span>
          </div>
        </div>
        <div class="panel-body no-pad">
          <div ref="chartEl" class="equity-chart"></div>
        </div>
      </div>

      <div class="widget-col">
        <div class="widget-grid">
          <!-- 1 BTC SPOT -->
          <div class="widget">
            <div class="lbl"><span>BTC · SPOT</span><span class="src">BINANCE</span></div>
            <div class="v">${{ formatNum(widgets.btc_price?.value, 0) }}</div>
            <div class="meta">
              <span :class="(widgets.btc_price?.change_24h ?? 0) >= 0 ? 'green' : 'red'">
                {{ formatPctSigned(widgets.btc_price?.change_24h, 2) }}
              </span>
              <span class="dim">24H · {{ formatSigned(widgets.btc_price?.change_usd, 0) }}</span>
            </div>
            <Sparkline :data="btcSpark" :width="200" :height="18" :color="(widgets.btc_price?.change_24h ?? 0) >= 0 ? '#22C55E' : '#EF4444'" />
          </div>
          <!-- 2 FNG -->
          <div class="widget">
            <div class="lbl"><span>FEAR &amp; GREED INDEX</span><span class="src">ALTERNATIVE.ME</span></div>
            <div class="v red">{{ widgets.fear_greed?.value }}</div>
            <div class="meta"><span class="red">{{ widgets.fear_greed?.label }}</span><span class="dim">PREV {{ widgets.fear_greed?.prev }}</span></div>
            <div class="bar-row">
              <div class="seg-r" :style="{ width: (widgets.fear_greed?.value || 0) + '%' }"></div>
              <div class="seg-empty" :style="{ width: (100 - (widgets.fear_greed?.value || 0)) + '%' }"></div>
            </div>
          </div>
          <!-- 3 LIQ 24h -->
          <div class="widget">
            <div class="lbl"><span>24H LIQUIDATIONS</span><span class="src">COINGLASS</span></div>
            <div class="v red">${{ widgets.liquidation_24h?.total }}M</div>
            <div class="meta">
              <span class="dim">1H</span><span>${{ widgets.liquidation_24h?.last_1h }}M</span>
              <span class="dim">·</span><span class="red">LONG {{ widgets.liquidation_24h?.long_pct }}%</span>
            </div>
            <div class="bar-row">
              <div class="seg-r" :style="{ width: (widgets.liquidation_24h?.long_pct || 0) + '%' }"></div>
              <div class="seg-g" :style="{ width: (widgets.liquidation_24h?.short_pct || 0) + '%' }"></div>
            </div>
          </div>
          <!-- 4 OI -->
          <div class="widget">
            <div class="lbl"><span>OPEN INTEREST</span><span class="src">3 VENUES</span></div>
            <div class="v">${{ widgets.open_interest?.total }}B</div>
            <div class="meta"><span class="dim">BINANCE</span><span>${{ widgets.open_interest?.binance }}B</span></div>
            <div class="meta">
              <span class="dim">BITMEX</span><span>${{ widgets.open_interest?.bitmex }}B</span>
              <span class="dim">·</span><span class="dim">OKX</span><span>${{ widgets.open_interest?.okx }}</span>
            </div>
          </div>
          <!-- 5 PREMIUM Q -->
          <div class="widget">
            <div class="lbl"><span>BTC QUARTERLY PREMIUM</span><span class="src">FUTURES</span></div>
            <div class="v green">+${{ widgets.premium_quarter?.okx }}</div>
            <div class="meta">
              <span class="dim">OKX</span><span class="green">+${{ widgets.premium_quarter?.okx }}</span>
              <span class="dim">·</span><span class="dim">BINANCE</span><span class="green">+${{ widgets.premium_quarter?.binance }}</span>
            </div>
            <div class="meta"><span class="dim">CONTANGO · CARRY +{{ widgets.premium_quarter?.ann_pct }}% ANN</span></div>
          </div>
          <!-- 6 L/S RATIO -->
          <div class="widget">
            <div class="lbl"><span>L/S RATIO · ACCOUNTS</span><span class="src">BINANCE</span></div>
            <div class="v green">{{ widgets.long_short_ratio?.value }}</div>
            <div class="meta">
              <span class="green">LONG {{ widgets.long_short_ratio?.long_pct }}%</span>
              <span class="dim">·</span><span class="red">SHORT {{ widgets.long_short_ratio?.short_pct }}%</span>
            </div>
            <div class="bar-row">
              <div class="seg-g" :style="{ width: (widgets.long_short_ratio?.long_pct || 0) + '%' }"></div>
              <div class="seg-r" :style="{ width: (widgets.long_short_ratio?.short_pct || 0) + '%' }"></div>
            </div>
          </div>
          <!-- 7 funding -->
          <div class="widget">
            <div class="lbl"><span>BTC FUNDING RATE</span><span class="src">8H</span></div>
            <div class="v green">+{{ widgets.funding_rate?.value?.toFixed(3) }}%</div>
            <div class="meta">
              <span class="dim">ANN. APR</span><span>+{{ widgets.funding_rate?.ann_apr }}%</span>
              <span class="dim">·</span><span class="green">NORMAL</span>
            </div>
          </div>
          <!-- 8 USDT premium -->
          <div class="widget">
            <div class="lbl"><span>USDT OTC PREMIUM</span><span class="src">CN OTC</span></div>
            <div class="v">¥{{ widgets.usdt_premium?.otc_cny }}</div>
            <div class="meta">
              <span class="green">+{{ widgets.usdt_premium?.change_pct }}%</span>
              <span class="dim">vs USD 0.9989</span>
            </div>
            <div class="meta">
              <span class="dim">NET FLOW</span><span class="green">+${{ widgets.usdt_premium?.flow_1h }}M / 1H</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- News flow -->
    <div class="news-flow">
      <div class="news-head">
        <span>NEWS STREAM · ALL VENUES · 47 EVT / 24H</span>
        <span><span class="amber">●</span> LIVE · BUFFER 12K</span>
      </div>
      <div v-for="n in news" :key="n.id" class="news-row">
        <div class="t">{{ n.time }}</div>
        <div class="src" :class="n.tone">{{ n.src }}</div>
        <div class="body">{{ n.body }}</div>
        <div class="pct" :class="n.pct >= 0 ? 'green' : 'red'">{{ formatPctSigned(n.pct, 2) }}</div>
      </div>
    </div>

    <!-- Live execution log -->
    <div class="panel">
      <div class="panel-head">
        <span>EXECUTION FEED · /var/log/exec.tail</span>
        <div class="right">
          <span>247 EVT/S</span>
          <span class="badge green"><span class="dot"></span>STREAM</span>
        </div>
      </div>
      <div class="panel-body">
        <LiveLog :rows="execFeed" max-height="240px" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* asset row */
.asset-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0;
  border-top: 1px solid var(--ct-divider);
  border-bottom: 1px solid var(--ct-divider);
}
.asset-cell {
  padding: 18px 18px;
  border-right: 1px solid var(--ct-divider);
}
.asset-cell:last-child { border-right: 0; }
.asset-cell .k {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 8px;
}
.asset-cell .v {
  font-size: 26px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--ct-text);
  font-variant-numeric: tabular-nums;
}
.asset-cell .v .unit {
  font-size: 11px;
  color: var(--ct-text-3);
  margin-left: 1px;
  letter-spacing: 0;
}
.asset-cell .v.green { color: var(--ct-pos); }
.asset-cell .v.amber { color: var(--ct-amber); }
.asset-cell .sub {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-top: 6px;
}
.asset-cell .sub .green { color: var(--ct-pos); }

/* dash grid */
.dash-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 18px;
}
.panel {
  border: 1px solid var(--ct-divider);
  background: var(--ct-bg-2);
}
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
.panel-head .right {
  display: flex;
  gap: 8px;
  align-items: center;
}
.panel-body { padding: 12px; }
.panel-body.no-pad { padding: 0; }
.equity-chart { height: 380px; width: 100%; }

.widget-col {
  display: flex;
  flex-direction: column;
}
.widget-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  border: 1px solid var(--ct-divider);
  flex: 1;
}
.widget {
  padding: 10px 12px;
  border-right: 1px solid var(--ct-divider);
  border-bottom: 1px solid var(--ct-divider);
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-height: 92px;
}
.widget:nth-child(2n) { border-right: 0; }
.widget:nth-last-child(-n+2) { border-bottom: 0; }
.widget .lbl {
  font-size: 9px;
  color: var(--ct-text-3);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  display: flex;
  justify-content: space-between;
}
.widget .lbl .src { color: var(--ct-text-dim); }
.widget .v {
  font-size: 18px;
  font-weight: 600;
  color: var(--ct-text);
  font-variant-numeric: tabular-nums;
}
.widget .v.green { color: var(--ct-pos); }
.widget .v.red   { color: var(--ct-neg); }
.widget .v.amber { color: var(--ct-amber); }
.widget .meta {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.04em;
  display: flex;
  gap: 8px;
  align-items: center;
}
.widget .meta .green { color: var(--ct-pos); }
.widget .meta .red   { color: var(--ct-neg); }
.widget .meta .dim   { color: var(--ct-text-3); }
.widget .bar-row {
  display: flex;
  height: 4px;
  background: var(--ct-bg-3);
  overflow: hidden;
}
.widget .seg-g { background: var(--ct-pos); }
.widget .seg-r { background: var(--ct-neg); }
.widget .seg-empty { background: var(--ct-bg-3); }

/* news */
.news-flow {
  border: 1px solid var(--ct-divider);
  background: var(--ct-bg);
}
.news-head {
  padding: 8px 12px;
  border-bottom: 1px solid var(--ct-divider);
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.news-head .amber { color: var(--ct-amber); }
.news-row {
  display: grid;
  grid-template-columns: 200px 90px 1fr 80px;
  gap: 14px;
  padding: 7px 12px;
  border-bottom: 1px solid var(--ct-divider);
  font-size: 12px;
  color: var(--ct-text-2);
  align-items: center;
}
.news-row:last-child { border-bottom: 0; }
.news-row:hover { background: var(--ct-bg-2); }
.news-row .t {
  color: var(--ct-text-dim);
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}
.news-row .src {
  font-size: 10px;
  color: var(--ct-amber);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-weight: 500;
}
.news-row .src.red { color: var(--ct-neg); }
.news-row .src.green { color: var(--ct-pos); }
.news-row .body { color: var(--ct-text); line-height: 1.5; }
.news-row .pct {
  text-align: right;
  font-size: 11px;
  color: var(--ct-text-3);
  font-variant-numeric: tabular-nums;
}
.news-row .pct.green { color: var(--ct-pos); }
.news-row .pct.red   { color: var(--ct-neg); }

/* responsive */
@media (max-width: 1100px) {
  .asset-row { grid-template-columns: repeat(2, 1fr); }
  .asset-cell:nth-child(2) { border-right: 0; }
  .dash-grid { grid-template-columns: 1fr; }
}
</style>
