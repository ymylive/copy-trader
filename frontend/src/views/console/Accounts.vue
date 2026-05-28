<script setup lang="ts">
import { computed, onMounted, ref, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAccountsStore } from '@/stores/accounts'
import { accountsApi } from '@/api/accounts'
import IpAllowlist from '@/components/IpAllowlist.vue'

const accStore = useAccountsStore()
const chartEl = ref<HTMLDivElement>()
const view = ref<'curve' | 'calendar'>('curve')

onMounted(async () => {
  await accStore.load()
  await nextTick()
  await drawChart()
})

watch(() => accStore.currentId, async () => {
  await nextTick()
  await drawChart()
})

watch(view, () => {
  nextTick(drawChart)
})

const current = computed(() => accStore.current)

async function drawChart() {
  if (!chartEl.value || !current.value) return
  const chart = echarts.init(chartEl.value)
  const data = await accountsApi.pnlSeries(current.value.id) as any[]

  if (view.value === 'curve') {
    chart.setOption({
      grid: { left: 50, right: 16, top: 30, bottom: 30 },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: data.map((_, i) => `D${i + 1}`),
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
          data: data.map((d) => d.value),
          lineStyle: { width: 2, color: '#10B981' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(16,185,129,0.35)' },
              { offset: 1, color: 'rgba(16,185,129,0.01)' }
            ])
          }
        }
      ]
    })
  } else {
    // calendar heatmap-style
    const cal = data.map((d, i) => [`2026-04-${String((i % 30) + 1).padStart(2, '0')}`, d.value])
    chart.setOption({
      tooltip: {},
      visualMap: {
        min: 0,
        max: Math.max(...data.map((d) => d.value)),
        calculable: false,
        orient: 'horizontal',
        left: 'center',
        bottom: 0,
        inRange: { color: ['#D1FAE5', '#10B981', '#047857'] }
      },
      calendar: {
        top: 30,
        left: 30,
        right: 30,
        cellSize: ['auto', 22],
        range: '2026-04',
        itemStyle: { borderColor: '#fff' },
        dayLabel: { color: '#9CA3AF' },
        monthLabel: { color: '#374151' }
      },
      series: { type: 'heatmap', coordinateSystem: 'calendar', data: cal }
    })
  }
  window.addEventListener('resize', () => chart.resize())
}

function exchangeBadge(ex: string) {
  const map: Record<string, { bg: string; label: string }> = {
    binance: { bg: '#F0B90B', label: 'B' },
    okx: { bg: '#000', label: 'O' },
    gate: { bg: '#2354E6', label: 'G' },
    bitget: { bg: '#00C2C7', label: 'BG' },
    hyperliquid: { bg: '#97FCE4', label: 'HL' }
  }
  return map[ex] || { bg: '#9CA3AF', label: '?' }
}

const apiVisible = ref(false)

async function changeLeverage() {
  const { value } = await ElMessageBox.prompt('请输入新的杠杆倍数', '修改杠杆', { inputPattern: /^\d+$/ })
  if (current.value) await accountsApi.setLeverage(current.value.id, 'BTCUSDT', Number(value))
  ElMessage.success('杠杆已更新（mock）')
}

async function editApi() {
  ElMessage.info('编辑 Apikey 弹窗（演示）')
}

async function removeAccount() {
  await ElMessageBox.confirm('确定删除当前账户？删除后无法恢复。', '提示', { type: 'warning' })
  if (current.value) await accountsApi.remove(current.value.id)
  ElMessage.success('已删除（mock）')
  await accStore.load()
}
</script>

<template>
  <div class="accounts-page">
    <div class="warning">
      注意事项：交易员广场中上架的交易员无论是否为隐藏持仓，开平仓均无延迟。
      平台是否上架取决于技术原因或其他成本考量，上架不构成任何投资建议，过往数据不代表未来表现。
    </div>

    <el-tabs
      :model-value="accStore.currentId ?? undefined"
      type="card"
      class="acc-tabs"
      @update:model-value="(v) => accStore.select(Number(v))"
    >
      <el-tab-pane
        v-for="acc in accStore.list"
        :key="acc.id"
        :name="acc.id"
        :label="acc.name"
      />
    </el-tabs>

    <div v-if="current" class="acc-detail ct-card">
      <div class="row top-row">
        <div class="lbl">当前账户类型：</div>
        <div class="val"><b>{{ current.name }}</b></div>
        <span class="active-tag">激活</span>
        <el-switch v-model="current.active" inline-prompt active-text="ON" inactive-text="OFF" />
      </div>

      <div class="row">
        <IpAllowlist :ips="current.egress_ips" />
      </div>

      <div class="row">
        <div class="lbl">交易所：</div>
        <div class="ex-icon" :style="{ background: exchangeBadge(current.exchange).bg }">{{ exchangeBadge(current.exchange).label }}</div>
        <div class="ex-name">{{ current.exchange.toUpperCase() }}</div>
        <span class="sep">UID:</span>
        <span class="mono">{{ current.uid }}</span>
        <span v-if="current.invited" class="invited-tag">受邀户</span>

        <div class="spacer"></div>

        <el-button @click="changeLeverage">修改杠杆</el-button>
        <el-button @click="editApi">编辑 Apikey</el-button>
        <el-button type="danger" plain @click="removeAccount">删除当前账户</el-button>
      </div>

      <div class="row">
        <div class="lbl">合约账户余额：</div>
        <div class="val mono">{{ current.futures_balance.toFixed(2) }} USDT</div>
        <span class="sep">账户总资产：</span>
        <span class="mono">{{ current.total_assets.toFixed(2) }} USDT</span>
      </div>

      <div class="api-row">
        <div>
          <span class="lbl">API Key：</span>
          <span class="mono">{{ apiVisible ? current.api_key.replace(/•/g, 'x') : current.api_key }}</span>
        </div>
        <div>
          <span class="lbl">Secret Key：</span>
          <span class="mono">{{ apiVisible ? current.secret_key.replace(/•/g, 'x') : current.secret_key }}</span>
        </div>
        <el-button text type="primary" @click="apiVisible = !apiVisible">{{ apiVisible ? '隐藏' : '显示' }}</el-button>
      </div>

      <div class="curve-block">
        <div class="curve-head">
          <span class="title">收益曲线</span>
          <el-radio-group v-model="view" size="small">
            <el-radio-button label="curve">收益曲线</el-radio-button>
            <el-radio-button label="calendar">盈亏日历</el-radio-button>
          </el-radio-group>
        </div>
        <div ref="chartEl" class="chart"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.accounts-page { display: flex; flex-direction: column; gap: 16px; }
.warning {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.18);
  color: #B91C1C;
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 12px;
  line-height: 1.6;
}
.acc-tabs { background: var(--ct-bg-card); border-radius: 10px; padding: 4px 8px; }
:deep(.el-tabs--card > .el-tabs__header .el-tabs__item.is-active) {
  background: var(--ct-primary-50);
  border-color: var(--ct-primary);
  color: var(--ct-primary);
}
.acc-detail { padding: 22px 24px; display: flex; flex-direction: column; gap: 14px; }
.row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; font-size: 13px; color: var(--ct-text-1); }
.top-row { font-size: 14px; }
.lbl { color: var(--ct-text-2); }
.val { color: var(--ct-text-1); }
.active-tag {
  background: rgba(16, 185, 129, 0.1);
  color: var(--ct-primary);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
.invited-tag {
  background: rgba(245, 158, 11, 0.12);
  color: #B45309;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
.ex-icon { width: 22px; height: 22px; border-radius: 50%; color: #fff; font-weight: 700; font-size: 11px; display: flex; align-items: center; justify-content: center; }
.ex-name { font-weight: 600; }
.sep { color: var(--ct-text-3); margin-left: 8px; }
.spacer { flex: 1; }
.api-row {
  display: flex;
  gap: 18px;
  align-items: center;
  background: var(--ct-bg-elev);
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 12px;
  flex-wrap: wrap;
}
.curve-block { margin-top: 6px; }
.curve-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.title { font-weight: 600; color: var(--ct-text-1); }
.chart { width: 100%; height: 320px; }
</style>
