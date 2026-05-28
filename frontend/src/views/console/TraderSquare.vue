<script setup lang="ts">
import { onMounted, ref, watch, computed } from 'vue'
import { useAccountsStore } from '@/stores/accounts'
import { useTradersStore } from '@/stores/traders'
import type { SignalSource, Trader } from '@/api/traders'
import TraderCard from '@/components/TraderCard.vue'
import CopyConfigDialog from '@/components/CopyConfigDialog.vue'
import { formatNum, formatUTC } from '@/utils/format'

const accStore = useAccountsStore()
const tradersStore = useTradersStore()

const dialogOpen = ref(false)
const dialogTrader = ref<Trader | null>(null)
const dialogReverse = ref(false)
const initiatingId = ref<string | null>(null)

interface SourceTab {
  value: SignalSource | 'all' | 'smart' | 'hyperbot'
  label: string
}

const tabs: SourceTab[] = [
  { value: 'all',         label: 'ALL' },
  { value: 'binance',     label: 'BINANCE' },
  { value: 'smart_money', label: 'SMART$' },
  { value: 'okx',         label: 'OKX' },
  { value: 'bitget',      label: 'BITGET' },
  { value: 'bicoin',      label: 'BICOIN' },
  { value: 'hyperbot',    label: 'HYPERBOT' }
]

const activeSource = ref<SignalSource | 'all'>('all')
const filters = ref({
  listed: true,
  sharpe: false,
  dd: false,
  scale: false
})
const search = ref('')
const renderTs = ref(formatUTC())

const currentAccount = computed(() => accStore.current)

onMounted(async () => {
  await accStore.load()
  await tradersStore.load()
})

watch(activeSource, async (v) => {
  tradersStore.source = v === 'all' ? null : v
  await tradersStore.load()
})

watch(search, async (v) => {
  tradersStore.q = v
  await tradersStore.load()
})

const tabCounts = computed(() => {
  const all = tradersStore.list
  return {
    all:     all.length || 348,
    binance: 142,
    smart_money: 50,
    okx:     94,
    bitget:  28,
    bicoin:  23,
    hyperbot: 11
  } as Record<string, number>
})

function onStart(t: Trader) {
  initiatingId.value = t.id
  setTimeout(() => {
    initiatingId.value = null
    dialogTrader.value = t
    dialogReverse.value = false
    dialogOpen.value = true
  }, 1200)
}
function onReverse(t: Trader) {
  dialogTrader.value = t
  dialogReverse.value = true
  dialogOpen.value = true
}
</script>

<template>
  <div class="square-page">
    <div class="sec-head">
      <div class="sec-title">
        <span class="amber">03 //</span> TRADER UNIVERSE · {{ formatNum(tradersStore.list.length, 0) }} LISTED · 6 SIGNAL SOURCES
      </div>
      <div class="sec-coord">SORT BY PNL_30D ↓ · FILTER LIVE · {{ renderTs }}</div>
    </div>

    <!-- Account selector strip -->
    <div class="acct-strip">
      <span class="label">DOWNSTREAM ACCOUNT:</span>
      <el-select
        :model-value="accStore.currentId ?? undefined"
        style="width:280px"
        @update:model-value="(v: number) => accStore.select(v)"
      >
        <el-option
          v-for="a in accStore.list"
          :key="a.id"
          :label="`${a.name}`"
          :value="a.id"
        />
      </el-select>
      <span class="dim">BAL <span class="amber">{{ currentAccount ? formatNum(currentAccount.futures_balance, 2) : '——' }} USDT</span></span>
      <span class="dim">SVC <span class="amber">220D 13H</span></span>
    </div>

    <!-- Venue tabs -->
    <div class="tr-tabs">
      <button
        v-for="t in tabs"
        :key="t.value"
        class="tr-tab"
        :class="{ active: activeSource === t.value }"
        @click="activeSource = t.value as any"
      >
        {{ t.label }} <span class="cnt">{{ tabCounts[t.value] ?? 0 }}</span>
      </button>
    </div>

    <!-- Filter chips -->
    <div class="tr-filters">
      <span class="chip" :class="{ active: filters.listed }" @click="filters.listed = !filters.listed">LISTED ONLY</span>
      <span class="chip" :class="{ active: filters.sharpe }" @click="filters.sharpe = !filters.sharpe">SHARPE ≥ 1.0</span>
      <span class="chip" :class="{ active: filters.dd }" @click="filters.dd = !filters.dd">DD ≤ 15%</span>
      <span class="chip" :class="{ active: filters.scale }" @click="filters.scale = !filters.scale">SCALE ≥ 10K</span>
      <div class="right">
        <span class="amber">VIEW: GRID</span>
        <span class="dim">|</span>
        <span class="dim">TABLE</span>
        <span class="dim">|</span>
        <span>SEARCH:
          <input v-model="search" class="search-inp" placeholder="" />
          <span v-if="!search" class="cursor">▌</span>
        </span>
      </div>
    </div>

    <!-- Grid -->
    <div v-loading="tradersStore.loading" class="tr-grid">
      <TraderCard
        v-for="t in tradersStore.list"
        :key="t.id"
        :trader="t"
        :initiating="initiatingId === t.id"
        @start="onStart"
        @reverse="onReverse"
        @toggle-fav="(tr) => tradersStore.toggleFav(tr)"
      />
    </div>

    <CopyConfigDialog
      v-model="dialogOpen"
      :trader="dialogTrader"
      :reverse="dialogReverse"
      :account-id="accStore.currentId ?? undefined"
    />
  </div>
</template>

<style scoped>
.square-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* account strip */
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
.acct-strip .dim {
  color: var(--ct-text-3);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.acct-strip .amber { color: var(--ct-amber); }

/* venue tabs */
.tr-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--ct-divider);
  flex-wrap: wrap;
}
.tr-tab {
  height: 36px;
  padding: 0 18px;
  display: inline-flex;
  align-items: center;
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ct-text-2);
  border-bottom: 2px solid transparent;
  background: none;
  border-top: 0;
  border-left: 0;
  border-right: 0;
  cursor: pointer;
  font-family: var(--ct-font-mono);
}
.tr-tab .cnt {
  color: var(--ct-text-dim);
  margin-left: 6px;
}
.tr-tab.active {
  color: var(--ct-amber);
  border-bottom: 2px solid var(--ct-amber);
}
.tr-tab.active .cnt { color: var(--ct-amber); }
.tr-tab:hover:not(.active) { color: var(--ct-text); }

/* filters */
.tr-filters {
  display: flex;
  gap: 14px;
  align-items: center;
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-family: var(--ct-font-mono);
  padding: 4px 0;
  flex-wrap: wrap;
}
.tr-filters .chip {
  padding: 3px 8px;
  border: 1px solid var(--ct-divider-strong);
  cursor: pointer;
  user-select: none;
}
.tr-filters .chip.active {
  border-color: var(--ct-amber);
  color: var(--ct-amber);
}
.tr-filters .chip:hover:not(.active) {
  border-color: var(--ct-text-2);
  color: var(--ct-text);
}
.tr-filters .right {
  margin-left: auto;
  display: flex;
  gap: 14px;
  align-items: center;
}
.tr-filters .right .dim { color: var(--ct-text-dim); }
.tr-filters .right .amber { color: var(--ct-amber); }
.search-inp {
  background: transparent;
  border: 0;
  border-bottom: 1px solid var(--ct-divider-strong);
  outline: 0;
  color: var(--ct-text);
  font-family: var(--ct-font-mono);
  font-size: 11px;
  width: 120px;
  letter-spacing: 0.04em;
  padding: 2px 4px;
}
.search-inp:focus { border-bottom-color: var(--ct-amber); }
.cursor {
  color: var(--ct-amber);
  animation: blink 1s steps(2, start) infinite;
}
@keyframes blink { to { visibility: hidden; } }

/* grid */
.tr-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0;
  border-top: 1px solid var(--ct-divider);
  border-left: 1px solid var(--ct-divider);
}

@media (max-width: 1280px) {
  .tr-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 900px) {
  .tr-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .tr-grid { grid-template-columns: 1fr; }
}
</style>
