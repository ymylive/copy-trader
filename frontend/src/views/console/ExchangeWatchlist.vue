<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAccountsStore } from '@/stores/accounts'
import type { SignalSource } from '@/api/traders'

const accStore = useAccountsStore()
const search = ref('')
const mode = ref<'global' | 'cookie'>('global')
const activeSource = ref<SignalSource | 'all'>('all')

const sources = [
  { value: 'all', label: '全部', icon: '★', bg: '#10B981' },
  { value: 'binance', label: '币安', icon: 'B', bg: '#F0B90B' },
  { value: 'smart_money', label: '聪明钱', icon: 'Σ', bg: '#000' },
  { value: 'hyperbot', label: 'Hyperbot', icon: 'H', bg: '#06D6A0' }
] as const

interface WatchItem {
  id: string
  source: SignalSource
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
    ElMessage.warning('请输入交易员链接、ID 或昵称')
    return
  }
  list.value.unshift({
    id: search.value,
    source: 'binance',
    exchange: currentAccount.value?.exchange || 'binance',
    nickname: '搜索结果 · ' + search.value,
    added_at: new Date().toLocaleString()
  })
  ElMessage.success('已加入自选列表')
  search.value = ''
}

function remove(id: string) {
  list.value = list.value.filter((x) => x.id !== id)
}
</script>

<template>
  <div class="watch-page">
    <div class="warning">
      注意事项：全域跟单模式下 Binance 公开持仓的交易员开平仓均可无延迟跟单，
      若交易员为隐藏持仓则开仓平仓将存在 2~3 分钟延迟。
    </div>
    <div class="warning red">
      注意事项：因币 coin 平台自身因素，在行情波动剧烈时跟单延迟将不可控，
      用户需时常留意自身仓位；若交易员已隐藏持仓及操作，则无法跟单，
      并且买卖模式交易员无法爬取操作记录，仅支持爬取持仓信息。
    </div>

    <div class="account-row">
      <div class="lbl">请选择下单账户：</div>
      <el-select :model-value="accStore.currentId" style="width:260px" @update:model-value="(v: number) => accStore.select(v)">
        <el-option v-for="a in accStore.list" :key="a.id" :label="`${a.name}【${a.exchange.toUpperCase()}】`" :value="a.id" />
      </el-select>
      <span class="info">交易所账户余额 <b class="mono">{{ currentAccount?.futures_balance?.toFixed(2) || '——' }} USDT</b></span>
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

    <div class="mode-row">
      <div class="mode-switch">
        <button :class="{ active: mode === 'global' }" @click="mode = 'global'">全域跟单</button>
        <button :class="{ active: mode === 'cookie' }" @click="mode = 'cookie'">
          Cookie 跟单
          <span class="svip-tag">SVIP</span>
        </button>
      </div>

      <div class="search-row">
        <el-input v-model="search" placeholder="输入交易员链接 / 身份 ID / 昵称以搜索交易员" style="width:460px">
          <template #prefix>
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          </template>
        </el-input>
        <el-button type="primary" @click="doSearch">搜索</el-button>
        <el-button>我的收藏</el-button>
      </div>
    </div>

    <div class="ct-card list-card">
      <div class="card-head"><span>自选列表</span><span class="muted">{{ list.length }} 项</span></div>
      <el-table :data="list" empty-text="暂无自选交易员，使用上方搜索框添加">
        <el-table-column label="信号源" prop="source" width="120" />
        <el-table-column label="交易员" prop="nickname" />
        <el-table-column label="ID" prop="id" />
        <el-table-column label="添加时间" prop="added_at" />
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button text type="primary" size="small">启动跟单</el-button>
            <el-button text type="danger" size="small" @click="remove(row.id)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.watch-page { display: flex; flex-direction: column; gap: 14px; }
.warning {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.16);
  color: #B91C1C;
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 12px;
  line-height: 1.6;
}
.warning.red { background: rgba(244, 63, 94, 0.06); }
.account-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
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
}
.src-tab.active { background: var(--ct-primary-50); border-color: var(--ct-primary); color: var(--ct-primary); font-weight: 600; }
.src-radio { width: 14px; height: 14px; border-radius: 50%; border: 2px solid #D1D5DB; position: relative; }
.src-radio.on { border-color: var(--ct-primary); }
.src-radio.on::after { content: ''; position: absolute; inset: 2px; background: var(--ct-primary); border-radius: 50%; }
.src-icon {
  width: 22px; height: 22px;
  border-radius: 50%; color: #fff; font-weight: 700; font-size: 11px;
  display: flex; align-items: center; justify-content: center;
}
.mode-row { display: flex; justify-content: center; gap: 18px; flex-wrap: wrap; align-items: center; padding: 8px 0; }
.mode-switch {
  display: inline-flex;
  background: var(--ct-bg-card);
  border: 1px solid var(--ct-border);
  border-radius: 12px;
  padding: 4px;
  gap: 4px;
}
.mode-switch button {
  position: relative;
  background: transparent; border: 0;
  padding: 10px 28px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: var(--ct-text-2);
  font-weight: 500;
}
.mode-switch button.active {
  background: var(--ct-primary);
  color: #fff;
}
.svip-tag {
  position: absolute;
  top: -8px; right: -6px;
  background: #FBBF24;
  color: #78350F;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 700;
}
.search-row { display: flex; gap: 8px; flex-wrap: wrap; }
.list-card { padding: 20px; }
.card-head { display: flex; justify-content: space-between; margin-bottom: 12px; font-weight: 600; color: var(--ct-text-1); }
.muted { color: var(--ct-text-3); font-weight: 400; }
</style>
