<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { formatNum, formatSigned, formatPctSigned } from '@/utils/format'

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

function closeOne(p: Position) {
  ElMessage.success(`SUBMITTED ${p.symbol} CLOSE`)
}
</script>

<template>
  <div class="pos-wrap">
    <div class="pos-head">
      <span class="label">POSITIONS · {{ data.length }} OPEN</span>
      <el-popconfirm
        title="CONFIRM CLOSE ALL POSITIONS?"
        confirm-button-text="EXECUTE"
        cancel-button-text="ABORT"
        @confirm="emit('close-all')"
      >
        <template #reference>
          <button class="btn-flat-amber" :disabled="!data.length">
            ▌ CLOSE ALL
          </button>
        </template>
      </el-popconfirm>
    </div>

    <table class="pos-table">
      <thead>
        <tr>
          <th>SIDE</th>
          <th>SYMBOL</th>
          <th class="r">QTY</th>
          <th class="r">ENTRY</th>
          <th class="r">MARK</th>
          <th class="r">LIQ</th>
          <th class="r">MARGIN</th>
          <th class="r">MMR%</th>
          <th class="r">REALIZED</th>
          <th class="r">UNREALIZED</th>
          <th class="r">PNL%</th>
          <th>TP / SL</th>
          <th class="r">OPS</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="!data.length">
          <td colspan="13" class="empty">— NO OPEN POSITIONS —</td>
        </tr>
        <tr v-for="row in data" :key="row.id">
          <td>
            <span class="side" :class="row.side === 'long' ? 'pos' : 'neg'">
              {{ row.side === 'long' ? 'LONG' : 'SHORT' }}
            </span>
          </td>
          <td>{{ row.symbol }}</td>
          <td class="r num">{{ formatNum(row.qty, 4) }}</td>
          <td class="r num">{{ formatNum(row.entry, 2) }}</td>
          <td class="r num">{{ formatNum(row.mark, 2) }}</td>
          <td class="r num">{{ formatNum(row.liq, 2) }}</td>
          <td class="r num">{{ formatNum(row.margin, 2) }}</td>
          <td class="r num">{{ formatNum(row.margin_rate, 2) }}%</td>
          <td class="r num" :class="row.realized_pnl >= 0 ? 'pos' : 'neg'">
            {{ row.realized_pnl === 0 ? '0.00' : formatSigned(row.realized_pnl, 2) }}
          </td>
          <td class="r num" :class="row.unrealized_pnl >= 0 ? 'pos' : 'neg'">
            {{ formatSigned(row.unrealized_pnl, 2) }}
          </td>
          <td class="r num" :class="row.pnl_pct >= 0 ? 'pos' : 'neg'">
            {{ formatPctSigned(row.pnl_pct, 2) }}
          </td>
          <td>{{ row.tp }} / {{ row.sl }}</td>
          <td class="r ops">
            <button class="link" @click="closeOne(row)">CLOSE</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.pos-wrap {
  border: 1px solid var(--ct-divider);
  background: var(--ct-bg);
}
.pos-head {
  height: 36px;
  padding: 0 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--ct-divider);
}
.pos-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--ct-font-mono);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}
.pos-table th,
.pos-table td {
  height: 28px;
  padding: 0 10px;
  text-align: left;
  border-bottom: 1px solid var(--ct-divider);
  white-space: nowrap;
}
.pos-table th {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-weight: 500;
  background: var(--ct-bg-2);
}
.pos-table .r { text-align: right; }
.pos-table tbody tr:hover { background: var(--ct-bg-hover); }
.pos-table .num { font-variant-numeric: tabular-nums; }
.pos-table .pos { color: var(--ct-pos); }
.pos-table .neg { color: var(--ct-neg); }
.side {
  font-size: 10px;
  letter-spacing: 0.14em;
  font-weight: 700;
}
.pos-table .empty {
  text-align: center;
  color: var(--ct-text-3);
  padding: 40px 0;
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.btn-flat-amber {
  background: var(--ct-amber);
  color: #0A0E14;
  border: 1px solid var(--ct-amber);
  height: 28px;
  padding: 0 14px;
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-weight: 600;
  cursor: pointer;
  font-family: var(--ct-font-mono);
}
.btn-flat-amber:hover:not(:disabled) { filter: brightness(1.1); }
.btn-flat-amber:disabled { opacity: 0.4; cursor: not-allowed; }
.link {
  background: transparent;
  border: 0;
  color: var(--ct-neg);
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
  font-family: var(--ct-font-mono);
}
.link:hover { color: var(--ct-amber); }
.ops { padding-right: 12px; }
</style>
