<script setup lang="ts">
import { onMounted, ref, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { dashboardApi } from '@/api/dashboard'

const overview = ref<any>({ total_assets: 0, account_count: 0, cumulative_pnl: 0, today_pnl: 0 })
const news = ref<any[]>([])
const widgets = ref<any>({})
const series = ref<any[]>([])

const chartEl = ref<HTMLDivElement>()

onMounted(async () => {
  overview.value = await dashboardApi.overview()
  news.value = (await dashboardApi.news()) as any[]
  widgets.value = await dashboardApi.marketWidgets()
  series.value = (await dashboardApi.pnlSeries()) as any[]
  await nextTick()
  drawChart()
})

function drawChart() {
  if (!chartEl.value) return
  const chart = echarts.init(chartEl.value)
  chart.setOption({
    grid: { left: 50, right: 16, top: 28, bottom: 30 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: series.value.map((d) => d.date),
      axisLabel: { color: '#9CA3AF', fontSize: 10 },
      axisLine: { lineStyle: { color: '#E5E7EB' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#9CA3AF' },
      splitLine: { lineStyle: { color: '#F3F4F6' } }
    },
    series: [
      {
        type: 'line',
        smooth: true,
        symbol: 'none',
        data: series.value.map((d) => d.value),
        lineStyle: { width: 2, color: '#10B981' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(16,185,129,0.3)' },
            { offset: 1, color: 'rgba(16,185,129,0.01)' }
          ])
        }
      }
    ]
  })
  window.addEventListener('resize', () => chart.resize())
}

watch(series, drawChart)

const widgetMeta = [
  { key: 'btc_price', label: 'BTC 价格 (USDT)', val: (w: any) => w.btc_price && `$${w.btc_price.value.toLocaleString('en')}`, sub: (w: any) => w.btc_price && `${w.btc_price.change_24h >= 0 ? '+' : ''}${w.btc_price.change_24h}%`, tone: (w: any) => (w.btc_price?.change_24h >= 0 ? 'pos' : 'neg') },
  { key: 'fear_greed', label: '恐慌 / 贪婪指数', val: (w: any) => w.fear_greed?.value, sub: (w: any) => w.fear_greed?.label },
  { key: 'liquidation_24h', label: '24h 全网爆仓 ($M)', val: (w: any) => `$${w.liquidation_24h}M`, sub: () => '24h' },
  { key: 'liquidation_1h', label: '1h 全网爆仓 ($M)', val: (w: any) => `$${w.liquidation_1h}M`, sub: () => '1h' },
  { key: 'open_interest', label: '合约持仓 ($B)', val: (w: any) => `$${(w.open_interest?.binance || 0).toFixed(1)}B`, sub: () => 'Binance' },
  { key: 'premium_quarter', label: 'BTC 季度溢价 %', val: (w: any) => `${(w.premium_quarter?.binance || 0).toFixed(2)}%`, sub: () => 'Binance' },
  { key: 'long_short_ratio', label: '多空人数比', val: (w: any) => (w.long_short_ratio || 0).toFixed(2), sub: () => '全网' },
  { key: 'funding_rate', label: '资金费率', val: (w: any) => `${((w.funding_rate || 0) * 100).toFixed(4)}%`, sub: () => 'Avg' },
  { key: 'usdt_netflow', label: 'USDT 净流入 ($M)', val: (w: any) => `$${w.usdt_netflow}M`, sub: () => '24h' },
  { key: 'usdt_premium', label: 'USDT 溢价', val: (w: any) => `${w.usdt_premium}%`, sub: () => 'OTC' },
  { key: 'retail_long_short', label: '实盘多空', val: (w: any) => `${w.retail_long_short?.long_pct}% / ${w.retail_long_short?.short_pct}%`, sub: () => '长 / 短' },
  { key: 'weibo_sentiment', label: '微博分析师多空', val: (w: any) => `${w.weibo_sentiment?.long}% / ${w.weibo_sentiment?.short}%`, sub: () => '长 / 短' }
]
</script>

<template>
  <div class="dashboard">
    <div class="stats-row">
      <div class="stat-card">
        <div class="label">总资金</div>
        <div class="num mono">${{ overview.total_assets.toLocaleString('en', { maximumFractionDigits: 2 }) }}</div>
        <div class="sub">USDT 等值</div>
      </div>
      <div class="stat-card">
        <div class="label">账户数量</div>
        <div class="num mono">{{ overview.account_count }}</div>
        <div class="sub">活跃账户</div>
      </div>
      <div class="stat-card">
        <div class="label">累计盈亏</div>
        <div class="num mono ct-pos">+${{ overview.cumulative_pnl.toLocaleString('en', { maximumFractionDigits: 2 }) }}</div>
        <div class="sub">历史总和</div>
      </div>
      <div class="stat-card">
        <div class="label">今日盈亏</div>
        <div class="num mono" :class="overview.today_pnl >= 0 ? 'ct-pos' : 'ct-neg'">
          {{ overview.today_pnl >= 0 ? '+' : '' }}${{ overview.today_pnl.toFixed(2) }}
        </div>
        <div class="sub">最近 24h</div>
      </div>
    </div>

    <div class="content-grid">
      <div class="ct-card chart-card">
        <div class="card-head">
          <span class="title">累计盈亏曲线</span>
          <el-radio-group size="small" model-value="all">
            <el-radio-button label="7d">7D</el-radio-button>
            <el-radio-button label="30d">30D</el-radio-button>
            <el-radio-button label="all">All</el-radio-button>
          </el-radio-group>
        </div>
        <div ref="chartEl" class="chart"></div>
      </div>

      <div class="ct-card news-card">
        <div class="card-head"><span class="title">实时新闻流</span><span class="ct-mute">NS3</span></div>
        <ul class="news-list">
          <li v-for="n in news" :key="n.id">
            <span class="time mono">{{ n.time }}</span>
            <div class="news-body">
              <div class="title-line">{{ n.title }}</div>
              <div class="src">{{ n.source }}</div>
            </div>
          </li>
        </ul>
      </div>
    </div>

    <div class="market-grid">
      <h3 class="section-title">市场宽幅指标</h3>
      <div class="widget-grid">
        <div v-for="m in widgetMeta" :key="m.key" class="widget">
          <div class="w-label">{{ m.label }}</div>
          <div class="w-val mono" :class="m.tone?.(widgets)">{{ m.val(widgets) }}</div>
          <div class="w-sub">{{ m.sub(widgets) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard { display: flex; flex-direction: column; gap: 22px; }
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}
.stat-card {
  background: var(--ct-bg-card);
  border: 1px solid var(--ct-border);
  border-radius: var(--ct-r-lg);
  padding: 20px 22px;
}
.label { color: var(--ct-text-3); font-size: 12px; }
.num { font-size: 26px; font-weight: 700; margin: 6px 0; color: var(--ct-text-1); }
.sub { color: var(--ct-text-3); font-size: 11px; }
.content-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
}
.ct-card {
  background: var(--ct-bg-card);
  border: 1px solid var(--ct-border);
  border-radius: var(--ct-r-lg);
  padding: 18px 20px;
}
.card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.title { font-weight: 600; color: var(--ct-text-1); }
.chart { width: 100%; height: 280px; }
.news-card { max-height: 360px; overflow: hidden; }
.news-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-height: 290px;
  overflow-y: auto;
}
.news-list li { display: flex; gap: 12px; padding-bottom: 12px; border-bottom: 1px dashed var(--ct-border); }
.news-list li:last-child { border-bottom: 0; }
.time { color: var(--ct-text-3); font-size: 12px; min-width: 40px; }
.news-body { flex: 1; }
.title-line { font-size: 13px; color: var(--ct-text-1); line-height: 1.6; }
.src { font-size: 11px; color: var(--ct-text-3); margin-top: 4px; }

.section-title { font-size: 16px; font-weight: 600; color: var(--ct-text-1); margin: 0 0 12px; }
.widget-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}
.widget {
  background: var(--ct-bg-card);
  border: 1px solid var(--ct-border);
  border-radius: var(--ct-r-md);
  padding: 14px 16px;
}
.w-label { color: var(--ct-text-3); font-size: 11px; }
.w-val { font-size: 18px; font-weight: 700; color: var(--ct-text-1); margin: 4px 0 2px; }
.w-val.pos { color: var(--ct-primary); }
.w-val.neg { color: var(--ct-danger); }
.w-sub { color: var(--ct-text-3); font-size: 11px; }

@media (max-width: 980px) {
  .content-grid { grid-template-columns: 1fr; }
}
</style>
