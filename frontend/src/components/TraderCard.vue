<script setup lang="ts">
import { computed } from 'vue'
import type { Trader } from '@/api/traders'
import Sparkline from '@/components/Sparkline.vue'
import { formatNum, formatSigned, formatPct, formatPctSigned } from '@/utils/format'

interface Props {
  trader: Trader
  initiating?: boolean
}
const props = withDefaults(defineProps<Props>(), { initiating: false })

const emit = defineEmits<{
  (e: 'start', t: Trader): void
  (e: 'reverse', t: Trader): void
  (e: 'toggle-fav', t: Trader): void
  (e: 'detail', t: Trader): void
}>()

const exchangeTag = computed(() => {
  const e = props.trader.exchange
  const map: Record<string, { label: string; cls: string }> = {
    binance:    { label: 'BINANCE', cls: 'ex-binance' },
    okx:        { label: 'OKX', cls: 'ex-okx' },
    bitget:     { label: 'BITGET', cls: 'ex-bitget' },
    hyperliquid:{ label: 'HYPERLIQUID', cls: 'ex-hl' },
    evm:        { label: 'EVM', cls: 'ex-evm' }
  }
  return map[e] || { label: e.toUpperCase(), cls: '' }
})

const sourceTag = computed(() => {
  // additional badges
  const tags = props.trader.tags || []
  const out: { label: string; cls: string }[] = []
  if (tags.includes('BICOIN')) out.push({ label: 'BICOIN', cls: 'src-bicoin' })
  if (tags.includes('HIDDEN')) out.push({ label: 'HIDDEN', cls: 'src-hidden' })
  if (tags.includes('LEAD'))   out.push({ label: 'LEAD',  cls: 'src-lead' })
  if (tags.includes('SMART$')) out.push({ label: 'SMART$',cls: 'src-smart' })
  return out
})

const uidLabel = computed(() => {
  const ex = props.trader.exchange.toUpperCase()
  const short = ex === 'BINANCE' ? 'BNB' : ex
  return `UID ${short}:${props.trader.id}`
})

const stale = computed(() => props.trader.status === 'invalid')

const pnlClass = computed(() => {
  const v = props.trader.total_pnl
  if (v == null || isNaN(v)) return 'zero'
  if (v === 0) return 'zero'
  return v > 0 ? '' : 'red'
})

const since = computed(() => {
  const days = props.trader.enrolled_days
  if (!days) return 'JOINED ── DAYS · DATA WITHHELD'
  const d = new Date()
  d.setDate(d.getDate() - days)
  const dateStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  return `JOINED ${formatNum(days, 0)} DAYS · ${dateStr}`
})

const isLongHorizon = computed(() => Math.abs(props.trader.roi) > 200)
const pnlLabel = computed(() => isLongHorizon.value ? 'CUMULATIVE PNL · USDT' : '90D PNL · USDT')
const roiLabel = computed(() => isLongHorizon.value ? 'ROI' : 'ROI 90D')

const sparkColor = computed(() => {
  const v = props.trader.total_pnl
  if (v == null || isNaN(v) || v === 0) return '#6B7280'
  return v > 0 ? '#FFB400' : '#EF4444'
})
</script>

<template>
  <div class="tr-card" :class="{ stale }">
    <!-- TOPLINE -->
    <div class="topline">
      <div class="tags">
        <span class="tag" :class="exchangeTag.cls">{{ exchangeTag.label }}</span>
        <span v-for="t in sourceTag" :key="t.label" class="tag" :class="t.cls">{{ t.label }}</span>
      </div>
      <span class="status" :class="{ flag: stale }">{{ stale ? 'STALE' : 'LISTED' }}</span>
    </div>

    <!-- UID + NAME + SINCE -->
    <div class="uid">{{ uidLabel }}</div>
    <div class="name">{{ trader.nickname }}</div>
    <div class="since">{{ since }}</div>

    <!-- PNL -->
    <div class="pnl-lbl">{{ pnlLabel }}</div>
    <div class="pnl" :class="pnlClass">
      {{ formatSigned(trader.total_pnl, 2) }}
    </div>

    <!-- STATS 4-GRID -->
    <div class="stats">
      <div class="stat">
        <div class="k">{{ roiLabel }}</div>
        <div class="v" :class="trader.roi >= 0 ? 'green' : 'red'">
          {{ formatPctSigned(trader.roi, 2) }}
        </div>
      </div>
      <div class="stat">
        <div class="k">AUM</div>
        <div class="v" :class="{ dim: !trader.scale || isNaN(trader.scale) }">
          {{ trader.scale && !isNaN(trader.scale) ? formatNum(trader.scale, 2) : 'NaN' }}
        </div>
      </div>
      <div class="stat">
        <div class="k">{{ trader.sharpe != null ? 'SHARPE' : 'WIN RATE' }}</div>
        <div class="v" :class="{
          green: (trader.sharpe ?? 0) > 1 || (trader.sharpe == null && (trader.win_rate ?? 0) >= 60),
          red:   (trader.sharpe ?? 0) < 0
        }">
          {{ trader.sharpe != null ? trader.sharpe.toFixed(2) : formatPct(trader.win_rate, 2) }}
        </div>
      </div>
      <div class="stat">
        <div class="k">{{ trader.sharpe != null ? 'WIN / DD' : 'MAX DD' }}</div>
        <div class="v" :class="{
          green: (trader.max_drawdown ?? 100) < 5,
          red: (trader.max_drawdown ?? 0) > 50
        }">
          <template v-if="trader.sharpe != null">
            {{ formatPct(trader.win_rate, 2) }} / {{ formatPct(trader.max_drawdown, 2) }}
          </template>
          <template v-else>
            {{ formatPct(trader.max_drawdown, 2) }}
          </template>
        </div>
      </div>
    </div>

    <!-- SPARKLINE -->
    <div class="spark-wrap">
      <Sparkline :data="trader.curve || []" :width="280" :height="18" :color="sparkColor" />
    </div>

    <!-- ACTIONS -->
    <div class="actions">
      <button
        class="btn-cp"
        :class="{ initiating }"
        :disabled="stale"
        @click="emit('start', trader)"
      >
        <template v-if="initiating">▌ INITIATING…</template>
        <template v-else>COPY</template>
      </button>
      <button class="btn-inv" :disabled="stale" @click="emit('reverse', trader)">
        INVERSE
      </button>
    </div>
  </div>
</template>

<style scoped>
.tr-card {
  position: relative;
  background: var(--ct-bg);
  padding: 14px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: background 120ms linear;
  border: 0;
  border-right: 1px solid var(--ct-divider);
  border-bottom: 1px solid var(--ct-divider);
}
.tr-card:hover { background: var(--ct-bg-2); }
.tr-card.stale { opacity: 0.5; }

.topline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.tags { display: flex; gap: 5px; flex-wrap: wrap; }
.tag {
  font-size: 9px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 2px 6px;
  border: 1px solid var(--ct-divider-strong);
  color: var(--ct-text-2);
  font-family: var(--ct-font-mono);
}
.tag.ex-okx     { color: var(--ct-teal);     border-color: rgba(31,204,177,0.35); }
.tag.ex-binance { color: var(--ct-binance);  border-color: rgba(240,185,11,0.35); }
.tag.ex-bitget  { color: #00C2C7;            border-color: rgba(0,194,199,0.35); }
.tag.ex-hl      { color: #97FCE4;            border-color: rgba(151,252,228,0.35); }
.tag.src-bicoin { color: var(--ct-amber);    border-color: rgba(255,180,0,0.35); }
.tag.src-hidden { color: var(--ct-text-3); }
.tag.src-lead   { color: var(--ct-violet);   border-color: rgba(167,139,250,0.35); }
.tag.src-smart  { color: #34D399;            border-color: rgba(52,211,153,0.35); }

.status {
  font-size: 9px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  padding: 2px 6px;
  color: #0A0E14;
  background: var(--ct-pos);
  font-family: var(--ct-font-mono);
  font-weight: 600;
}
.status.flag { background: var(--ct-neg); color: #0A0E14; }

.uid {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.04em;
  font-family: var(--ct-font-mono);
}
.name {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.005em;
  color: var(--ct-text);
}
.since {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.pnl-lbl {
  font-size: 9px;
  color: var(--ct-text-3);
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
.pnl {
  margin-top: -2px;
  font-size: 28px;
  font-weight: 700;
  color: var(--ct-amber);
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
}
.pnl.red  { color: var(--ct-neg); }
.pnl.zero { color: var(--ct-text-3); }

.stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0;
  margin-top: 4px;
  border-top: 1px solid var(--ct-divider);
}
.stat {
  padding: 6px 0;
  border-bottom: 1px solid var(--ct-divider);
}
.stat:nth-child(2n) {
  border-left: 1px solid var(--ct-divider);
  padding-left: 8px;
}
.stat:nth-last-child(-n+2) { border-bottom: 0; }
.stat .k {
  font-size: 9px;
  color: var(--ct-text-3);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.stat .v {
  font-size: 13px;
  color: var(--ct-text);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  margin-top: 2px;
}
.stat .v.green { color: var(--ct-pos); }
.stat .v.red   { color: var(--ct-neg); }
.stat .v.dim   { color: var(--ct-text-3); }

.spark-wrap { width: 100%; }

.actions {
  display: flex;
  gap: 0;
  margin-top: 6px;
}
.btn-cp {
  flex: 1;
  height: 30px;
  background: var(--ct-amber);
  color: #0A0E14;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-weight: 600;
  border: 1px solid var(--ct-amber);
  font-family: var(--ct-font-mono);
  cursor: pointer;
}
.btn-cp:hover:not(:disabled) { filter: brightness(1.1); }
.btn-cp:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-cp.initiating {
  background: transparent;
  color: var(--ct-amber);
  animation: blink-bg 1s steps(2, start) infinite;
}
@keyframes blink-bg { 50% { background: rgba(255,180,0,0.08); } }

.btn-inv {
  flex: 1;
  height: 30px;
  background: transparent;
  color: var(--ct-text);
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-weight: 500;
  border: 1px solid var(--ct-divider-strong);
  border-left: 0;
  font-family: var(--ct-font-mono);
  cursor: pointer;
}
.btn-inv:hover:not(:disabled) {
  color: var(--ct-neg);
  border-color: var(--ct-neg);
}
.btn-inv:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
