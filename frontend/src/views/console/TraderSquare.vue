<script setup lang="ts">
import { onMounted, ref, watch, computed } from 'vue'
import { useAccountsStore } from '@/stores/accounts'
import { useTradersStore } from '@/stores/traders'
import type { SignalSource, Trader } from '@/api/traders'
import TraderCard from '@/components/TraderCard.vue'
import CopyConfigDialog from '@/components/CopyConfigDialog.vue'

const accStore = useAccountsStore()
const tradersStore = useTradersStore()

const view = ref<'grid' | 'list'>('grid')
const dialogOpen = ref(false)
const dialogTrader = ref<Trader | null>(null)
const dialogReverse = ref(false)

interface SourceTab { value: SignalSource | 'all'; label: string; icon: string; bg: string }

const sources: SourceTab[] = [
  { value: 'all', label: '全部', icon: '★', bg: '#10B981' },
  { value: 'binance', label: '币安', icon: 'B', bg: '#F0B90B' },
  { value: 'smart_money', label: '聪明钱', icon: 'Σ', bg: '#000' },
  { value: 'okx', label: '欧易', icon: 'O', bg: '#000' },
  { value: 'bitget', label: 'Bitget', icon: 'BG', bg: '#00C2C7' },
  { value: 'bicoin', label: '币Coin', icon: 'C', bg: '#3B82F6' },
  { value: 'hyperbot', label: 'Hyperbot', icon: 'H', bg: '#06D6A0' }
]

const activeSource = ref<SignalSource | 'all'>('all')

const currentAccount = computed(() => accStore.current)

onMounted(async () => {
  await accStore.load()
  await tradersStore.load()
})

watch(activeSource, async (v) => {
  tradersStore.source = v === 'all' ? null : v
  await tradersStore.load()
})

watch(() => tradersStore.q, async () => {
  await tradersStore.load()
})

watch(() => tradersStore.favoriteOnly, async () => {
  await tradersStore.load()
})

function onStart(t: Trader) {
  dialogTrader.value = t
  dialogReverse.value = false
  dialogOpen.value = true
}
function onReverse(t: Trader) {
  dialogTrader.value = t
  dialogReverse.value = true
  dialogOpen.value = true
}
</script>

<template>
  <div class="square-page">
    <div class="warning">
      注意事项：交易员广场中上架的交易员无论是否为隐藏持仓，开平仓均无延迟。
      平台是否上架取决于技术原因或其他成本考量，上架不构成任何投资建议，过往数据不代表未来表现。
    </div>

    <div class="account-row">
      <div class="lbl">请选择下单账户：</div>
      <el-select :model-value="accStore.currentId" style="width:260px" @update:model-value="(v: number) => accStore.select(v)">
        <el-option v-for="a in accStore.list" :key="a.id" :label="`${a.name}【${a.exchange.toUpperCase()}】`" :value="a.id" />
      </el-select>

      <span class="info">交易所账户余额 <b class="mono">{{ currentAccount?.futures_balance?.toFixed(2) || '——' }} USDT</b></span>
      <span class="info">当前账户剩余服务时长：<b>220 天 13 小时</b></span>
    </div>

    <div class="source-tabs">
      <div
        v-for="s in sources"
        :key="s.value"
        class="src-tab"
        :class="{ active: activeSource === s.value }"
        @click="activeSource = s.value"
      >
        <span class="src-radio" :class="{ on: activeSource === s.value }"></span>
        <span class="src-icon" :style="{ background: s.bg }">{{ s.icon }}</span>
        <span>{{ s.label }}</span>
      </div>
    </div>

    <div class="toolbar">
      <div class="view-switch">
        <button :class="{ active: view === 'grid' }" @click="view = 'grid'">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
        </button>
        <button :class="{ active: view === 'list' }" @click="view = 'list'">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><rect x="3" y="5" width="18" height="3"/><rect x="3" y="11" width="18" height="3"/><rect x="3" y="17" width="18" height="3"/></svg>
        </button>
      </div>

      <el-input
        v-model="tradersStore.q"
        placeholder="搜索本页交易员"
        clearable
        style="max-width:380px"
      >
        <template #prefix>
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        </template>
      </el-input>

      <div class="spacer"></div>

      <el-button :type="tradersStore.favoriteOnly ? 'primary' : ''" @click="tradersStore.favoriteOnly = !tradersStore.favoriteOnly">
        我的收藏
      </el-button>
    </div>

    <div v-loading="tradersStore.loading" class="content">
      <div v-if="!tradersStore.list.length && !tradersStore.loading" class="empty">暂无交易员</div>
      <div v-else-if="view === 'grid'" class="grid">
        <TraderCard
          v-for="t in tradersStore.list"
          :key="t.id"
          :trader="t"
          @start="onStart"
          @reverse="onReverse"
          @toggle-fav="(tr) => tradersStore.toggleFav(tr)"
        />
      </div>
      <el-table v-else :data="tradersStore.list" stripe>
        <el-table-column label="交易员" min-width="220">
          <template #default="{ row }">
            <div class="row-trader">
              <div class="row-avatar">{{ row.nickname.slice(0, 1) }}</div>
              <div>
                <div class="rn">{{ row.nickname }}</div>
                <div class="rid mono">{{ row.id }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="交易所" prop="exchange" />
        <el-table-column label="入驻天数" prop="enrolled_days" align="right" />
        <el-table-column label="总盈亏" align="right">
          <template #default="{ row }">
            <span class="mono ct-pos">{{ row.total_pnl.toLocaleString('en', { maximumFractionDigits: 2 }) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="收益率" align="right">
          <template #default="{ row }"><span class="mono ct-pos">{{ row.roi.toFixed(2) }}%</span></template>
        </el-table-column>
        <el-table-column label="夏普" align="right">
          <template #default="{ row }">{{ row.sharpe?.toFixed(2) ?? '--' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="onStart(row)">启动跟单</el-button>
            <el-button size="small" @click="onReverse(row)">反向跟单</el-button>
          </template>
        </el-table-column>
      </el-table>
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
.square-page { display: flex; flex-direction: column; gap: 16px; }
.warning {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.18);
  color: #B91C1C;
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 12px;
  line-height: 1.6;
}
.account-row { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.lbl { color: var(--ct-text-1); font-weight: 600; }
.info { color: var(--ct-text-2); font-size: 13px; }
.source-tabs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
}
.src-tab {
  display: flex; align-items: center; gap: 10px;
  background: var(--ct-bg-card);
  border: 1px solid var(--ct-border);
  border-radius: 10px;
  padding: 12px 16px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.src-tab:hover { border-color: var(--ct-primary); }
.src-tab.active {
  background: var(--ct-primary-50);
  border-color: var(--ct-primary);
  color: var(--ct-primary);
  font-weight: 600;
}
.src-radio {
  width: 14px; height: 14px; border-radius: 50%;
  border: 2px solid #D1D5DB;
  position: relative;
}
.src-radio.on { border-color: var(--ct-primary); }
.src-radio.on::after {
  content: '';
  position: absolute; inset: 2px;
  background: var(--ct-primary);
  border-radius: 50%;
}
.src-icon {
  width: 22px; height: 22px;
  border-radius: 50%;
  color: #fff;
  font-weight: 700;
  font-size: 11px;
  display: flex; align-items: center; justify-content: center;
}
.toolbar { display: flex; align-items: center; gap: 14px; }
.view-switch { display: inline-flex; border: 1px solid var(--ct-border); border-radius: 8px; overflow: hidden; }
.view-switch button { width: 36px; height: 36px; border: 0; background: transparent; cursor: pointer; color: var(--ct-text-2); }
.view-switch button.active { background: var(--ct-primary); color: #fff; }
.spacer { flex: 1; }
.empty {
  background: var(--ct-bg-card);
  padding: 60px 0;
  text-align: center;
  color: var(--ct-text-3);
  border-radius: var(--ct-r-lg);
  border: 1px solid var(--ct-border);
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}
.row-trader { display: flex; align-items: center; gap: 10px; }
.row-avatar {
  width: 32px; height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #34D399, #0D9488);
  color: #fff; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.rn { font-weight: 600; }
.rid { color: var(--ct-text-3); font-size: 11px; }
</style>
