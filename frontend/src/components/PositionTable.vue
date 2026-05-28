<script setup lang="ts">
import { ElMessage } from 'element-plus'

interface Position {
  id: number
  side: 'long' | 'short'
  symbol: string
  qty: number
  entry: number
  mark: number
  liq: number
  margin: number
  margin_rate: number
  realized_pnl: number
  unrealized_pnl: number
  pnl_pct: number
  tp: string
  sl: string
}

defineProps<{ data: Position[] }>()
const emit = defineEmits<{ (e: 'close-all'): void }>()

function num(v: number) {
  return v.toLocaleString('en', { maximumFractionDigits: 4 })
}

function closeOne(p: Position) {
  ElMessage.success(`已提交 ${p.symbol} 平仓单（mock）`)
}
</script>

<template>
  <el-table :data="data" empty-text="暂无数据" stripe>
    <el-table-column label="多 / 空" width="80">
      <template #default="{ row }">
        <span :class="row.side === 'long' ? 'ct-pos' : 'ct-neg'" class="dir-tag">
          {{ row.side === 'long' ? '多' : '空' }}
        </span>
      </template>
    </el-table-column>
    <el-table-column label="交易对" prop="symbol" />
    <el-table-column label="数量" align="right">
      <template #default="{ row }"><span class="mono">{{ num(row.qty) }}</span></template>
    </el-table-column>
    <el-table-column label="开仓均价" align="right">
      <template #default="{ row }"><span class="mono">{{ num(row.entry) }}</span></template>
    </el-table-column>
    <el-table-column label="标记价格" align="right">
      <template #default="{ row }"><span class="mono">{{ num(row.mark) }}</span></template>
    </el-table-column>
    <el-table-column label="强平价格" align="right">
      <template #default="{ row }"><span class="mono">{{ num(row.liq) }}</span></template>
    </el-table-column>
    <el-table-column label="保证金" align="right">
      <template #default="{ row }"><span class="mono">{{ num(row.margin) }}</span></template>
    </el-table-column>
    <el-table-column label="保证金率" align="right">
      <template #default="{ row }"><span class="mono">{{ row.margin_rate.toFixed(2) }}%</span></template>
    </el-table-column>
    <el-table-column label="已实现盈亏" align="right">
      <template #default="{ row }">
        <span class="mono" :class="row.realized_pnl >= 0 ? 'ct-pos' : 'ct-neg'">
          {{ row.realized_pnl >= 0 ? '+' : '' }}{{ num(row.realized_pnl) }}
        </span>
      </template>
    </el-table-column>
    <el-table-column label="盈亏及回报率" align="right">
      <template #default="{ row }">
        <span class="mono" :class="row.unrealized_pnl >= 0 ? 'ct-pos' : 'ct-neg'">
          {{ row.unrealized_pnl >= 0 ? '+' : '' }}{{ num(row.unrealized_pnl) }}
        </span>
        <div class="pct mono" :class="row.pnl_pct >= 0 ? 'ct-pos' : 'ct-neg'">
          ({{ row.pnl_pct >= 0 ? '+' : '' }}{{ row.pnl_pct.toFixed(2) }}%)
        </div>
      </template>
    </el-table-column>
    <el-table-column label="止盈 / 止损" width="120">
      <template #default="{ row }">{{ row.tp }} / {{ row.sl }}</template>
    </el-table-column>
    <el-table-column label="操作" width="140" fixed="right">
      <template #default="{ row }">
        <el-button text type="primary" size="small">新增跟平订单</el-button>
        <el-button text type="danger" size="small" @click="closeOne(row)">平仓</el-button>
      </template>
    </el-table-column>
  </el-table>

  <div class="footer-bar">
    <el-popconfirm title="确认一键全平所有持仓？" @confirm="emit('close-all')">
      <template #reference>
        <el-button type="primary" :disabled="!data.length">一键全平</el-button>
      </template>
    </el-popconfirm>
  </div>
</template>

<style scoped>
.dir-tag { font-weight: 700; }
.pct { font-size: 11px; }
.footer-bar { display: flex; justify-content: flex-end; padding: 12px 0; }
</style>
