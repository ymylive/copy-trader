<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { Trader } from '@/api/traders'

interface Props {
  trader: Trader
}
const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'start', t: Trader): void
  (e: 'reverse', t: Trader): void
  (e: 'toggle-fav', t: Trader): void
  (e: 'detail', t: Trader): void
}>()

const chartEl = ref<HTMLDivElement>()

const exchangeIcon = computed(() => {
  const e = props.trader.exchange
  const map: Record<string, { bg: string; label: string }> = {
    binance: { bg: '#F0B90B', label: 'B' },
    okx: { bg: '#000', label: 'O' },
    bitget: { bg: '#00C2C7', label: 'BG' },
    hyperliquid: { bg: '#97FCE4', label: 'HL' },
    evm: { bg: '#627EEA', label: 'Ξ' }
  }
  return map[e] || { bg: '#9CA3AF', label: '?' }
})

const exchangeName = computed(() => {
  const map: Record<string, string> = {
    binance: 'Binance', okx: 'OKX', bitget: 'Bitget',
    hyperliquid: 'Hyperliquid', evm: 'On-Chain'
  }
  return map[props.trader.exchange] || props.trader.exchange
})

function fmt(n: number | null | undefined, decimals = 2) {
  if (n == null) return '----'
  return n.toLocaleString('en', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

function renderChart() {
  if (!chartEl.value || !props.trader.curve) return
  const chart = echarts.init(chartEl.value)
  const data = props.trader.curve
  chart.setOption({
    grid: { left: 0, right: 0, top: 4, bottom: 0 },
    xAxis: { type: 'category', show: false, data: data.map((_, i) => i) },
    yAxis: { type: 'value', show: false },
    series: [
      {
        type: 'line',
        smooth: true,
        symbol: 'none',
        data,
        lineStyle: { width: 1.6, color: '#10B981' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(16,185,129,0.4)' },
            { offset: 1, color: 'rgba(16,185,129,0.01)' }
          ])
        }
      }
    ]
  })
}

onMounted(renderChart)
watch(() => props.trader.curve, renderChart)
</script>

<template>
  <div class="trader-card">
    <div class="status-badge" :class="trader.status">
      {{ trader.status === 'listed' ? '已上架' : '数据失效' }}
    </div>

    <div class="card-head">
      <div class="ex-icon" :style="{ background: exchangeIcon.bg }">{{ exchangeIcon.label }}</div>
      <div class="ex-name">{{ exchangeName }}</div>
      <div class="tags">
        <span v-for="t in trader.tags" :key="t" class="tag">{{ t }}</span>
      </div>
      <el-icon
        class="fav"
        :class="{ active: trader.favorited }"
        @click="emit('toggle-fav', trader)"
      >
        <svg v-if="trader.favorited" viewBox="0 0 24 24" width="18" height="18" fill="#F59E0B">
          <path d="M12 17.27 18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21 12 17.27z" />
        </svg>
        <svg v-else viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#9CA3AF" stroke-width="1.6">
          <path d="M12 17.27 18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21 12 17.27z" />
        </svg>
      </el-icon>
    </div>

    <div class="trader-id mono">ID: {{ trader.id }}</div>

    <div class="profile">
      <div class="avatar">{{ trader.nickname.slice(0, 1) }}</div>
      <div class="profile-info">
        <div class="nick">{{ trader.nickname }}</div>
        <div class="days">入驻时长: {{ trader.enrolled_days }} 天</div>
      </div>
      <a class="detail" @click="emit('detail', trader)">查看详情 ›</a>
    </div>

    <div ref="chartEl" class="spark"></div>

    <div class="metrics-head">
      <span>—— 90 天盈亏</span>
      <span>—— 收益率</span>
    </div>

    <div class="metrics">
      <div class="metric">
        <div class="val mono ct-pos">{{ fmt(trader.total_pnl) }} USDT</div>
        <div class="lbl">带单规模</div>
      </div>
      <div class="metric">
        <div class="val mono">{{ trader.sharpe == null ? '----' : trader.sharpe.toFixed(2) }}</div>
        <div class="lbl">夏普比率</div>
      </div>
      <div class="metric">
        <div class="val mono ct-pos">{{ fmt(trader.roi) }}%</div>
        <div class="lbl">90 天胜率</div>
      </div>
      <div class="metric">
        <div class="val mono">{{ trader.max_drawdown == null ? '----' : `${trader.max_drawdown.toFixed(1)}%` }}</div>
        <div class="lbl">90 天最大回撤</div>
      </div>
    </div>

    <div class="actions">
      <el-button type="primary" class="btn primary" @click="emit('start', trader)" :disabled="trader.status === 'invalid'">
        启动跟单
      </el-button>
      <el-button class="btn reverse" @click="emit('reverse', trader)" :disabled="trader.status === 'invalid'">
        反向跟单
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.trader-card {
  position: relative;
  background: var(--ct-bg-card);
  border: 1px solid var(--ct-border);
  border-radius: var(--ct-r-lg);
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: transform 0.15s, box-shadow 0.15s, border-color 0.15s;
}
.trader-card:hover {
  transform: translateY(-2px);
  border-color: var(--ct-primary);
  box-shadow: var(--ct-shadow-md);
}
.status-badge {
  position: absolute;
  top: 0;
  right: 18px;
  padding: 3px 14px;
  border-radius: 0 0 8px 8px;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
}
.status-badge.listed { background: var(--ct-primary); }
.status-badge.invalid { background: var(--ct-text-3); }
.card-head { display: flex; align-items: center; gap: 8px; }
.ex-icon {
  width: 22px; height: 22px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 700; font-size: 11px;
}
.ex-name { color: var(--ct-text-1); font-weight: 600; font-size: 14px; margin-right: 6px; }
.tags { display: flex; gap: 4px; flex-wrap: wrap; flex: 1; }
.tag {
  background: rgba(16, 185, 129, 0.1);
  color: var(--ct-primary);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
}
.fav { cursor: pointer; }
.trader-id { color: var(--ct-text-3); font-size: 11px; }
.profile { display: flex; align-items: center; gap: 10px; }
.avatar {
  width: 34px; height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, #34D399, #0D9488);
  color: #fff;
  font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.profile-info { flex: 1; }
.nick { font-size: 14px; font-weight: 600; color: var(--ct-text-1); }
.days { font-size: 11px; color: var(--ct-text-3); margin-top: 2px; }
.detail { font-size: 12px; color: var(--ct-primary); cursor: pointer; }
.spark { width: 100%; height: 70px; }
.metrics-head {
  display: flex; gap: 14px; font-size: 11px; color: var(--ct-text-3);
  padding-bottom: 4px;
}
.metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  padding: 8px 0;
  border-top: 1px dashed var(--ct-border);
}
.metric { text-align: left; }
.val { font-size: 13px; font-weight: 600; color: var(--ct-text-1); }
.lbl { font-size: 10px; color: var(--ct-text-3); margin-top: 2px; }
.actions { display: flex; gap: 8px; }
.btn { flex: 1; }
.btn.primary {
  background: var(--ct-primary);
  border-color: var(--ct-primary);
  color: #fff;
}
.btn.reverse {
  background: rgba(56, 189, 248, 0.08);
  border-color: rgba(56, 189, 248, 0.3);
  color: var(--ct-accent);
}
</style>
