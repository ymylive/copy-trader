<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAccountsStore } from '@/stores/accounts'
import type { SignalSource } from '@/api/traders'
import { formatNum, formatUTC } from '@/utils/format'

const accStore = useAccountsStore()
const search = ref('')
const mode = ref<'global' | 'cookie'>('global')
const activeSource = ref<SignalSource | 'all'>('all')
const renderTs = ref(formatUTC())

const sources = [
  { value: 'all',         label: 'ALL' },
  { value: 'binance',     label: 'BINANCE' },
  { value: 'smart_money', label: 'SMART$' },
  { value: 'hyperbot',    label: 'HYPERBOT' }
] as const

interface WatchItem {
  id: string
  source: string
  exchange: string
  nickname: string
  added_at: string
}

const list = ref<WatchItem[]>([])
const currentAccount = computed(() => accStore.current)

onMounted(async () => {
  await accStore.load()
})

function doSearch() {
  if (!search.value) {
    ElMessage.warning('REQUIRE TRADER LINK / ID / NICKNAME')
    return
  }
  list.value.unshift({
    id: search.value,
    source: activeSource.value === 'all' ? 'BINANCE' : String(activeSource.value).toUpperCase(),
    exchange: currentAccount.value?.exchange.toUpperCase() || 'BINANCE',
    nickname: 'SEARCH · ' + search.value,
    added_at: formatUTC()
  })
  ElMessage.success('ADDED TO WATCHLIST')
  search.value = ''
}

function remove(id: string) {
  list.value = list.value.filter((x) => x.id !== id)
}
</script>

<template>
  <div class="watch-page">
    <div class="sec-head">
      <div class="sec-title"><span class="amber">05 //</span> EXCHANGE WATCHLIST · ARBITRARY TRADER SEARCH</div>
      <div class="sec-coord">{{ renderTs }}</div>
    </div>

    <!-- warnings -->
    <div class="warn">
      ⚠ GLOBAL MODE: BINANCE PUBLIC POSITIONS NO-DELAY · HIDDEN POSITIONS HAVE 2-3MIN DELAY.
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
    </div>

    <!-- Source tabs -->
    <div class="src-tabs">
      <button
        v-for="s in sources"
        :key="s.value"
        class="src-tab"
        :class="{ active: activeSource === s.value }"
        @click="activeSource = s.value as any"
      >
        {{ s.label }}
      </button>
    </div>

    <!-- Mode switch -->
    <div class="mode-row">
      <button class="chip-btn" :class="{ active: mode === 'global' }" @click="mode = 'global'">GLOBAL TRADING</button>
      <button class="chip-btn" :class="{ active: mode === 'cookie' }" @click="mode = 'cookie'">
        COOKIE TRADING <span class="svip-tag">SVIP</span>
      </button>

      <div class="search-row">
        <input class="search-inp" v-model="search" placeholder="ENTER TRADER LINK / UID / NICKNAME" @keyup.enter="doSearch" />
        <button class="btn-term primary" @click="doSearch">SEARCH</button>
        <button class="btn-term">FAVORITES</button>
      </div>
    </div>

    <!-- list -->
    <div class="list-wrap">
      <div class="list-head">
        <span>WATCHLIST · {{ list.length }} ENTRIES</span>
        <span class="dim">SORT BY ADDED ↓</span>
      </div>
      <table v-if="list.length" class="w-table">
        <thead>
          <tr>
            <th>SOURCE</th>
            <th>NICKNAME</th>
            <th>UID</th>
            <th>EXCHANGE</th>
            <th>ADDED</th>
            <th class="r">OPS</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in list" :key="row.id">
            <td>{{ row.source }}</td>
            <td>{{ row.nickname }}</td>
            <td class="amber">{{ row.id }}</td>
            <td>{{ row.exchange }}</td>
            <td class="t">{{ row.added_at }}</td>
            <td class="r">
              <button class="link" @click="remove(row.id)">REMOVE</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">— EMPTY · USE SEARCH ABOVE TO ADD TRADERS —</div>
    </div>
  </div>
</template>

<style scoped>
.watch-page { display: flex; flex-direction: column; gap: 14px; }

.warn {
  border: 1px solid rgba(239, 68, 68, 0.35);
  background: rgba(239, 68, 68, 0.06);
  color: var(--ct-neg);
  padding: 8px 12px;
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-family: var(--ct-font-mono);
  line-height: 1.6;
}

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
.acct-strip .label { color: var(--ct-text-3); letter-spacing: 0.12em; text-transform: uppercase; }
.acct-strip .dim { color: var(--ct-text-3); }
.acct-strip .amber { color: var(--ct-amber); }

.src-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--ct-divider);
}
.src-tab {
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
.src-tab.active { color: var(--ct-amber); border-bottom-color: var(--ct-amber); }
.src-tab:hover:not(.active) { color: var(--ct-text); }

.mode-row {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.chip-btn {
  position: relative;
  background: transparent;
  border: 1px solid var(--ct-divider-strong);
  color: var(--ct-text-2);
  padding: 6px 14px;
  font-family: var(--ct-font-mono);
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
}
.chip-btn:hover { border-color: var(--ct-amber); color: var(--ct-amber); }
.chip-btn.active {
  background: var(--ct-amber);
  border-color: var(--ct-amber);
  color: #0A0E14;
  font-weight: 600;
}
.svip-tag {
  display: inline-block;
  background: var(--ct-amber);
  color: #0A0E14;
  font-size: 9px;
  padding: 1px 4px;
  margin-left: 4px;
  font-weight: 700;
}
.chip-btn.active .svip-tag { background: #0A0E14; color: var(--ct-amber); }

.search-row {
  margin-left: auto;
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.search-inp {
  height: 30px;
  background: var(--ct-bg-2);
  border: 1px solid var(--ct-divider);
  color: var(--ct-text);
  padding: 0 12px;
  font-family: var(--ct-font-mono);
  font-size: 12px;
  outline: 0;
  width: 360px;
}
.search-inp:focus { border-color: var(--ct-amber); }
.btn-term {
  height: 30px;
  padding: 0 14px;
  background: transparent;
  border: 1px solid var(--ct-divider-strong);
  color: var(--ct-text);
  font-family: var(--ct-font-mono);
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
}
.btn-term:hover { border-color: var(--ct-amber); color: var(--ct-amber); }
.btn-term.primary {
  background: var(--ct-amber);
  border-color: var(--ct-amber);
  color: #0A0E14;
  font-weight: 600;
}

.list-wrap {
  border: 1px solid var(--ct-divider);
  background: var(--ct-bg);
}
.list-head {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid var(--ct-divider);
  background: var(--ct-bg-2);
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.w-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--ct-font-mono);
  font-size: 12px;
}
.w-table th,
.w-table td {
  height: 30px;
  padding: 0 12px;
  text-align: left;
  border-bottom: 1px solid var(--ct-divider);
}
.w-table th {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-weight: 500;
}
.w-table .r { text-align: right; }
.w-table .amber { color: var(--ct-amber); }
.w-table .t { color: var(--ct-text-dim); }
.empty {
  padding: 40px 0;
  text-align: center;
  color: var(--ct-text-3);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.link {
  background: transparent;
  border: 0;
  color: var(--ct-neg);
  font-family: var(--ct-font-mono);
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
}
.link:hover { color: var(--ct-amber); }
</style>
