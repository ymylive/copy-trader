<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAccountsStore } from '@/stores/accounts'
import { mockPositions } from '@/mock/data'
import PositionTable from '@/components/PositionTable.vue'
import { formatNum, formatSigned, formatPctSigned, formatUTC } from '@/utils/format'

const accStore = useAccountsStore()
const activeTrader = ref('79346')
const activeTab = ref<'positions' | 'history' | 'analysis'>('positions')

const traderList = [
  { id: '79346',  name: '茂茂大魔王',  has_alert: true },
  { id: '369319', name: '风火山林Trader', has_alert: false },
  { id: '1030294', name: '牛的青山在', has_alert: false }
]

const positions = ref<any[]>([])
const operations = ref<any[]>([])
const analysis = ref({ trades: 0, win: 0, lose: 0, total_pnl: 0, max_dd: 0 })
const renderTs = ref(formatUTC())

const currentAccount = computed(() => accStore.current)

onMounted(async () => {
  await accStore.load()
  await loadData()
})

async function loadData() {
  positions.value = mockPositions(activeTrader.value)
  operations.value = [
    { id: 1, time: '2026-05-28 10:32:56 UTC', action: 'OPEN LONG',  symbol: 'BTC-USDT-SWAP', qty: 0.025, price: 74180.50 },
    { id: 2, time: '2026-05-28 10:32:55 UTC', action: 'OPEN SHORT', symbol: 'ETH-USDT-SWAP', qty: 1.50,  price: 2540.20 },
    { id: 3, time: '2026-05-28 10:32:14 UTC', action: 'CLOSE SHORT', symbol: 'ETH-USDT-SWAP', qty: 1.50, price: 2412.10 },
    { id: 4, time: '2026-05-28 10:31:58 UTC', action: 'ADD LONG',   symbol: 'SOL-USDT-SWAP', qty: 5.40,  price: 158.42 }
  ]
  const winning = positions.value.filter((p) => p.unrealized_pnl > 0).length
  analysis.value = {
    trades: positions.value.length + operations.value.length,
    win: winning,
    lose: positions.value.length - winning,
    total_pnl: positions.value.reduce((s, p) => s + p.unrealized_pnl, 0),
    max_dd: 4.32
  }
}

function selectTrader(id: string) {
  activeTrader.value = id
  loadData()
}

function closeAll() {
  positions.value = []
  ElMessage.success('CLOSE ALL SUBMITTED · WAITING FOR FILLS')
}
</script>

<template>
  <div class="pos-page">
    <div class="sec-head">
      <div class="sec-title"><span class="amber">03 //</span> POSITIONS · OPEN ORDERS · EXECUTION HISTORY</div>
      <div class="sec-coord">{{ renderTs }}</div>
    </div>

    <!-- Account strip -->
    <div class="acct-strip">
      <span class="label">DOWNSTREAM ACCOUNT:</span>
      <el-select
        :model-value="accStore.currentId ?? undefined"
        style="width:280px"
        @update:model-value="(v: number) => accStore.select(v)"
      >
        <el-option v-for="a in accStore.list" :key="a.id" :label="a.name" :value="a.id" />
      </el-select>
      <span class="dim">BAL <span class="amber">{{ currentAccount ? formatNum(currentAccount.futures_balance, 2) : '——' }} USDT</span></span>
      <span class="dim">SVC <span class="amber">220D 13H</span></span>
    </div>

    <!-- Trader chip selector -->
    <div class="trader-chips">
      <button
        v-for="t in traderList"
        :key="t.id"
        class="t-chip"
        :class="{ active: activeTrader === t.id }"
        @click="selectTrader(t.id)"
      >
        <span class="name">{{ t.name }}</span>
        <span class="uid">UID:{{ t.id }}</span>
        <span v-if="t.has_alert" class="alert-dot"></span>
      </button>
    </div>

    <!-- Sub tabs -->
    <div class="pos-tabs">
      <button class="pos-tab" :class="{ active: activeTab === 'positions' }" @click="activeTab = 'positions'">
        <span class="idx">A1</span>POSITIONS
      </button>
      <button class="pos-tab" :class="{ active: activeTab === 'history' }" @click="activeTab = 'history'">
        <span class="idx">A2</span>OPERATION LOG
      </button>
      <button class="pos-tab" :class="{ active: activeTab === 'analysis' }" @click="activeTab = 'analysis'">
        <span class="idx">A3</span>ANALYSIS
      </button>
    </div>

    <!-- Positions table -->
    <div v-if="activeTab === 'positions'">
      <PositionTable :data="positions" @close-all="closeAll" />
    </div>

    <!-- History -->
    <div v-else-if="activeTab === 'history'" class="history-wrap">
      <table class="op-table">
        <thead>
          <tr>
            <th>TS</th>
            <th>ACTION</th>
            <th>SYMBOL</th>
            <th class="r">QTY</th>
            <th class="r">PX</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="op in operations" :key="op.id">
            <td class="t">{{ op.time }}</td>
            <td :class="op.action.includes('LONG') ? 'pos' : op.action.includes('SHORT') ? 'neg' : ''">{{ op.action }}</td>
            <td>{{ op.symbol }}</td>
            <td class="r">{{ formatNum(op.qty, 4) }}</td>
            <td class="r">{{ formatNum(op.price, 2) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Analysis -->
    <div v-else class="analysis-grid">
      <div class="ana-cell">
        <div class="k">TOTAL TRADES</div>
        <div class="v">{{ formatNum(analysis.trades, 0) }}</div>
      </div>
      <div class="ana-cell">
        <div class="k">WIN / LOSS</div>
        <div class="v">{{ analysis.win }} / {{ analysis.lose }}</div>
      </div>
      <div class="ana-cell">
        <div class="k">UNREALIZED PNL</div>
        <div class="v" :class="analysis.total_pnl >= 0 ? 'pos' : 'neg'">
          {{ formatSigned(analysis.total_pnl, 2) }}
        </div>
      </div>
      <div class="ana-cell">
        <div class="k">MAX DRAWDOWN</div>
        <div class="v amber">{{ formatPctSigned(-analysis.max_dd, 2) }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pos-page { display: flex; flex-direction: column; gap: 14px; }

.acct-strip {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  padding: 10px 14px;
  background: var(--ct-bg-2);
  border: 1px solid var(--ct-divider);
  font-family: var(--ct-font-mono);
  font-size: 11px;
}
.acct-strip .label {
  color: var(--ct-text-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.acct-strip .dim { color: var(--ct-text-3); letter-spacing: 0.06em; text-transform: uppercase; }
.acct-strip .amber { color: var(--ct-amber); }

.trader-chips { display: flex; gap: 8px; flex-wrap: wrap; }
.t-chip {
  position: relative;
  background: transparent;
  border: 1px solid var(--ct-divider);
  padding: 8px 14px;
  font-family: var(--ct-font-mono);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 2px;
  text-align: left;
}
.t-chip:hover { border-color: var(--ct-text-2); }
.t-chip.active { border-color: var(--ct-amber); background: rgba(255,180,0,0.06); }
.t-chip .name { font-size: 12px; color: var(--ct-text); letter-spacing: 0.04em; }
.t-chip .uid { font-size: 10px; color: var(--ct-text-3); letter-spacing: 0.06em; }
.t-chip .alert-dot {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 6px;
  height: 6px;
  background: var(--ct-neg);
}

.pos-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--ct-divider);
}
.pos-tab {
  background: transparent;
  border: 0;
  border-bottom: 2px solid transparent;
  padding: 10px 18px;
  font-family: var(--ct-font-mono);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ct-text-2);
  cursor: pointer;
}
.pos-tab .idx { color: var(--ct-text-dim); margin-right: 8px; }
.pos-tab.active { color: var(--ct-amber); border-bottom-color: var(--ct-amber); }
.pos-tab.active .idx { color: var(--ct-amber); }

.history-wrap {
  border: 1px solid var(--ct-divider);
  background: var(--ct-bg);
}
.op-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--ct-font-mono);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}
.op-table th,
.op-table td {
  height: 28px;
  padding: 0 12px;
  text-align: left;
  border-bottom: 1px solid var(--ct-divider);
}
.op-table th {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  background: var(--ct-bg-2);
  font-weight: 500;
}
.op-table .r { text-align: right; }
.op-table .t { color: var(--ct-text-dim); }
.op-table .pos { color: var(--ct-pos); }
.op-table .neg { color: var(--ct-neg); }

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1px solid var(--ct-divider);
}
.ana-cell {
  padding: 18px 18px;
  border-right: 1px solid var(--ct-divider);
}
.ana-cell:last-child { border-right: 0; }
.ana-cell .k {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 6px;
}
.ana-cell .v {
  font-size: 24px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.ana-cell .v.pos { color: var(--ct-pos); }
.ana-cell .v.neg { color: var(--ct-neg); }
.ana-cell .v.amber { color: var(--ct-amber); }

@media (max-width: 900px) {
  .analysis-grid { grid-template-columns: repeat(2, 1fr); }
  .ana-cell:nth-child(2) { border-right: 0; }
}
</style>
