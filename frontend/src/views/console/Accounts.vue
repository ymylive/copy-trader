<script setup lang="ts">
import { computed, onMounted, ref, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAccountsStore } from '@/stores/accounts'
import { accountsApi } from '@/api/accounts'
import IpAllowlist from '@/components/IpAllowlist.vue'
import { BLOOMBERG_THEME } from '@/charts/echartsTheme'
import { formatNum, formatUTC } from '@/utils/format'

const accStore = useAccountsStore()
const chartEl = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

const renderTs = ref(formatUTC())
const apiVisible = ref(false)

onMounted(async () => {
  await accStore.load()
  await nextTick()
  await drawChart()
})

watch(() => accStore.currentId, async () => {
  await nextTick()
  await drawChart()
})

const current = computed(() => accStore.current)

async function drawChart() {
  if (!chartEl.value || !current.value) return
  chart?.dispose()
  chart = echarts.init(chartEl.value, BLOOMBERG_THEME, { renderer: 'canvas' })
  const data = (await accountsApi.pnlSeries(current.value.id)) as any[]

  chart.setOption({
    backgroundColor: 'transparent',
    grid: { left: 60, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: 'category',
      data: data.map((_, i) => `D${i + 1}`),
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisTick: { show: false },
      axisLabel: { color: '#6B7280', fontSize: 9, interval: 4 }
    },
    yAxis: {
      scale: true,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#6B7280', fontSize: 9 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0A0E14',
      borderColor: '#FFB400',
      borderWidth: 1,
      textStyle: { color: '#E6E8EA', fontFamily: 'JetBrains Mono', fontSize: 11 }
    },
    series: [{
      type: 'line',
      data: data.map((d) => d.value),
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
      }
    }]
  })
  window.addEventListener('resize', () => chart?.resize())
}

async function changeLeverage() {
  try {
    const { value } = await ElMessageBox.prompt('NEW LEVERAGE (1-125)', 'EDIT LEVERAGE', { inputPattern: /^\d+$/ })
    if (current.value) await accountsApi.setLeverage(current.value.id, 'BTCUSDT', Number(value))
    ElMessage.success('LEVERAGE UPDATED')
  } catch { /* aborted */ }
}

async function editApi() {
  ElMessage.info('EDIT API KEYS — DIALOG (MOCK)')
}

async function removeAccount() {
  try {
    await ElMessageBox.confirm('DELETE THIS ACCOUNT? CANNOT BE UNDONE.', 'CONFIRM', { type: 'warning' })
    if (current.value) await accountsApi.remove(current.value.id)
    ElMessage.success('ACCOUNT REMOVED')
    await accStore.load()
  } catch { /* aborted */ }
}
</script>

<template>
  <div class="acct-page">
    <div class="sec-head">
      <div class="sec-title"><span class="amber">02 //</span> ACCOUNT MANAGEMENT · 4 BOUND · 3 ACTIVE</div>
      <div class="sec-coord">{{ renderTs }}</div>
    </div>

    <!-- Tab strip -->
    <div class="acct-tabs">
      <button
        v-for="acc in accStore.list"
        :key="acc.id"
        class="acct-tab"
        :class="{ active: accStore.currentId === acc.id, paused: !acc.active }"
        @click="accStore.select(acc.id)"
      >
        <span class="tab-name">{{ acc.name }}</span>
        <span class="tab-uid">UID {{ acc.uid }}</span>
        <span class="status-dot" :class="acc.active ? 'on' : 'off'"></span>
      </button>
    </div>

    <div v-if="current" class="acct-detail">
      <!-- Header row -->
      <div class="detail-head hairline">
        <div class="head-cell">
          <div class="k">EXCHANGE</div>
          <div class="v">{{ current.exchange.toUpperCase() }}</div>
        </div>
        <div class="head-cell">
          <div class="k">UID</div>
          <div class="v amber">{{ current.uid }}</div>
        </div>
        <div class="head-cell">
          <div class="k">STATUS</div>
          <div class="v" :class="current.active ? 'green' : 'red'">
            {{ current.active ? '● ACTIVE' : '○ PAUSED' }}
          </div>
        </div>
        <div class="head-cell">
          <div class="k">INVITED REL.</div>
          <div class="v">{{ current.invited ? '✓ VERIFIED' : '— NONE' }}</div>
        </div>
        <div class="head-cell">
          <div class="k">FUTURES BAL</div>
          <div class="v">{{ formatNum(current.futures_balance, 2) }} <span class="unit">USDT</span></div>
        </div>
        <div class="head-cell">
          <div class="k">TOTAL ASSETS</div>
          <div class="v amber">{{ formatNum(current.total_assets, 2) }} <span class="unit">USDT</span></div>
        </div>
      </div>

      <!-- Actions row -->
      <div class="actions-row">
        <button class="chip-btn" @click="changeLeverage">EDIT LEVERAGE</button>
        <button class="chip-btn" @click="editApi">EDIT API KEYS</button>
        <button class="chip-btn danger" @click="removeAccount">REMOVE ACCOUNT</button>
        <div class="spacer"></div>
        <el-switch v-model="current.active" inline-prompt active-text="ON" inactive-text="OFF" />
      </div>

      <!-- API row -->
      <div class="api-row">
        <div class="api-line">
          <span class="lbl">API_KEY:</span>
          <span class="mono-val">{{ apiVisible ? current.api_key.replace(/•/g, 'x') : current.api_key }}</span>
        </div>
        <div class="api-line">
          <span class="lbl">SECRET:</span>
          <span class="mono-val">{{ apiVisible ? current.secret_key.replace(/•/g, 'x') : current.secret_key }}</span>
        </div>
        <button class="chip-btn small" @click="apiVisible = !apiVisible">
          {{ apiVisible ? 'HIDE' : 'REVEAL' }}
        </button>
      </div>

      <!-- IP allowlist -->
      <div class="ip-row">
        <IpAllowlist :ips="current.egress_ips" />
      </div>

      <!-- Equity chart -->
      <div class="panel">
        <div class="panel-head">
          <span>EQUITY CURVE · 30D · {{ current.name }}</span>
          <span class="badge amber"><span class="dot"></span>LIVE</span>
        </div>
        <div ref="chartEl" class="chart"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.acct-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* tab strip */
.acct-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--ct-divider);
  flex-wrap: wrap;
}
.acct-tab {
  background: transparent;
  border: 0;
  border-bottom: 2px solid transparent;
  padding: 10px 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  cursor: pointer;
  font-family: var(--ct-font-mono);
  position: relative;
  text-align: left;
}
.acct-tab .tab-name {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ct-text-2);
}
.acct-tab .tab-uid {
  font-size: 10px;
  color: var(--ct-text-dim);
  letter-spacing: 0.04em;
}
.acct-tab.active {
  border-bottom-color: var(--ct-amber);
}
.acct-tab.active .tab-name { color: var(--ct-amber); }
.acct-tab .status-dot {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 6px;
  height: 6px;
}
.acct-tab .status-dot.on { background: var(--ct-pos); }
.acct-tab .status-dot.off { background: var(--ct-text-dim); }

.acct-detail {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* head row */
.detail-head {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  border: 1px solid var(--ct-divider);
}
.head-cell {
  padding: 14px 14px;
  border-right: 1px solid var(--ct-divider);
}
.head-cell:last-child { border-right: 0; }
.head-cell .k {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 6px;
}
.head-cell .v {
  font-size: 14px;
  font-weight: 600;
  color: var(--ct-text);
  font-variant-numeric: tabular-nums;
}
.head-cell .v.green { color: var(--ct-pos); }
.head-cell .v.red   { color: var(--ct-neg); }
.head-cell .v.amber { color: var(--ct-amber); }
.head-cell .v .unit {
  font-size: 10px;
  color: var(--ct-text-3);
  margin-left: 4px;
}

/* actions */
.actions-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.chip-btn {
  background: transparent;
  border: 1px solid var(--ct-divider-strong);
  color: var(--ct-text-2);
  padding: 6px 12px;
  font-family: var(--ct-font-mono);
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
}
.chip-btn:hover { border-color: var(--ct-amber); color: var(--ct-amber); }
.chip-btn.danger { border-color: rgba(239,68,68,0.4); color: var(--ct-neg); }
.chip-btn.danger:hover { background: rgba(239,68,68,0.08); border-color: var(--ct-neg); color: var(--ct-neg); }
.chip-btn.small { padding: 4px 10px; font-size: 10px; }
.spacer { flex: 1; }

/* api */
.api-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  background: var(--ct-bg-2);
  border: 1px solid var(--ct-divider);
  padding: 12px 14px;
}
.api-line { display: flex; gap: 8px; font-family: var(--ct-font-mono); font-size: 12px; }
.api-line .lbl {
  color: var(--ct-text-3);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-size: 10px;
}
.mono-val {
  color: var(--ct-text);
  font-family: var(--ct-font-mono);
  letter-spacing: 0.02em;
  word-break: break-all;
}

.ip-row {
  padding: 8px 0;
}

/* panel */
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
.chart {
  width: 100%;
  height: 320px;
}

@media (max-width: 1100px) {
  .detail-head { grid-template-columns: repeat(3, 1fr); }
  .head-cell:nth-child(3) { border-right: 0; }
}
</style>
