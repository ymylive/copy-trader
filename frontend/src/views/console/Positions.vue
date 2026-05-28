<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAccountsStore } from '@/stores/accounts'
import { mockPositions } from '@/mock/data'
import PositionTable from '@/components/PositionTable.vue'

const accStore = useAccountsStore()
const activeTrader = ref('BTC_STARDUST_001')
const activeTab = ref<'positions' | 'history' | 'analysis'>('positions')

const traderList = [
  { id: 'BTC_STARDUST_001', name: 'BTC 星辰', has_alert: true },
  { id: 'MAOMAO_DEMON', name: '茂茂大魔王', has_alert: false }
]

const positions = ref<any[]>([])
const operations = ref<any[]>([])
const analysis = ref({ trades: 0, win: 0, lose: 0, total_pnl: 0, max_dd: 0 })

const currentAccount = computed(() => accStore.current)

onMounted(async () => {
  await accStore.load()
  await loadData()
})

async function loadData() {
  positions.value = mockPositions(activeTrader.value)
  operations.value = [
    { id: 1, time: '2026-05-28 09:12:31', action: '开多', symbol: 'BTC-USDT', qty: 0.15, price: 93210.4 },
    { id: 2, time: '2026-05-28 09:08:11', action: '开空', symbol: 'ETH-USDT', qty: 1.5, price: 3540.2 }
  ]
  const winning = positions.value.filter((p) => p.unrealized_pnl > 0).length
  analysis.value = {
    trades: positions.value.length,
    win: winning,
    lose: positions.value.length - winning,
    total_pnl: positions.value.reduce((s, p) => s + p.unrealized_pnl, 0),
    max_dd: 6.4
  }
}

function selectTrader(t: string) {
  activeTrader.value = t
  loadData()
}

function closeAll() {
  positions.value = []
  ElMessage.success('已提交一键全平指令（mock）')
}
</script>

<template>
  <div class="positions-page">
    <div class="account-row">
      <div class="lbl">请选择下单账户：</div>
      <el-select :model-value="accStore.currentId" style="width:260px" @update:model-value="(v: number) => accStore.select(v)">
        <el-option v-for="a in accStore.list" :key="a.id" :label="`${a.name}【${a.exchange.toUpperCase()}】`" :value="a.id" />
      </el-select>
      <span class="info">交易所账户余额 <b class="mono">{{ currentAccount?.futures_balance?.toFixed(2) || '——' }} USDT</b></span>
      <span class="info">当前账户剩余服务时长：<b>220 天 13 小时</b></span>
    </div>

    <div class="trader-chips">
      <div
        v-for="t in traderList"
        :key="t.id"
        class="chip"
        :class="{ active: activeTrader === t.id }"
        @click="selectTrader(t.id)"
      >
        <div class="ch-avatar">{{ t.name.slice(0, 1) }}</div>
        <span>{{ t.name }}</span>
        <span v-if="t.has_alert" class="dot" />
      </div>
    </div>

    <el-tabs v-model="activeTab" class="pos-tabs">
      <el-tab-pane :label="`持仓列表`" name="positions">
        <PositionTable :data="positions" @close-all="closeAll" />
      </el-tab-pane>

      <el-tab-pane label="操作记录" name="history">
        <el-table :data="operations" empty-text="暂无操作记录">
          <el-table-column label="时间" prop="time" />
          <el-table-column label="动作" prop="action" />
          <el-table-column label="交易对" prop="symbol" />
          <el-table-column label="数量" align="right">
            <template #default="{ row }"><span class="mono">{{ row.qty }}</span></template>
          </el-table-column>
          <el-table-column label="成交价" align="right">
            <template #default="{ row }"><span class="mono">{{ row.price }}</span></template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="跟单分析" name="analysis">
        <div class="analysis-grid">
          <div class="an-card">
            <div class="an-label">总交易数</div>
            <div class="an-val mono">{{ analysis.trades }}</div>
          </div>
          <div class="an-card">
            <div class="an-label">胜 / 负</div>
            <div class="an-val mono">{{ analysis.win }} / {{ analysis.lose }}</div>
          </div>
          <div class="an-card">
            <div class="an-label">累计盈亏</div>
            <div class="an-val mono ct-pos">+{{ analysis.total_pnl.toFixed(2) }}</div>
          </div>
          <div class="an-card">
            <div class="an-label">最大回撤</div>
            <div class="an-val mono">{{ analysis.max_dd.toFixed(2) }}%</div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.positions-page { display: flex; flex-direction: column; gap: 14px; }
.account-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.lbl { color: var(--ct-text-1); font-weight: 600; }
.info { color: var(--ct-text-2); font-size: 13px; }
.trader-chips { display: flex; gap: 12px; flex-wrap: wrap; }
.chip {
  position: relative;
  display: flex; align-items: center; gap: 8px;
  background: var(--ct-bg-card);
  border: 1px solid var(--ct-border);
  border-radius: 999px;
  padding: 6px 18px 6px 6px;
  cursor: pointer;
  transition: border-color 0.15s;
}
.chip:hover { border-color: var(--ct-primary); }
.chip.active { background: var(--ct-primary-50); border-color: var(--ct-primary); color: var(--ct-primary); }
.ch-avatar {
  width: 28px; height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #34D399, #0D9488);
  color: #fff; font-weight: 700; font-size: 12px;
  display: flex; align-items: center; justify-content: center;
}
.chip .dot {
  position: absolute; top: 4px; right: 8px;
  width: 8px; height: 8px;
  background: var(--ct-danger);
  border-radius: 50%;
}
.pos-tabs {
  background: var(--ct-bg-card);
  border-radius: var(--ct-r-lg);
  border: 1px solid var(--ct-border);
  padding: 8px 16px 16px;
}
.analysis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
  padding: 14px 0;
}
.an-card {
  background: var(--ct-bg-elev);
  border-radius: 10px;
  padding: 18px;
}
.an-label { color: var(--ct-text-3); font-size: 12px; }
.an-val { font-size: 22px; font-weight: 700; margin-top: 6px; color: var(--ct-text-1); }
</style>
