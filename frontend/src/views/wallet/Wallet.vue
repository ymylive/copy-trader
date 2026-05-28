<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useWalletStore } from '@/stores/wallet'
import RechargeDialog from '@/components/RechargeDialog.vue'
import { walletApi } from '@/api/wallet'
import { formatNum, formatSigned, formatUTC } from '@/utils/format'

const wallet = useWalletStore()
const rechargeOpen = ref(false)
const addrDialogOpen = ref(false)
const addresses = ref<any[]>([])
const newAddr = ref({ chain: 'TRC20', address: '' })
const renderTs = ref(formatUTC())

onMounted(async () => {
  await wallet.load()
  addresses.value = (await walletApi.withdrawAddresses()) as any[]
})

async function openAddrDialog() {
  addrDialogOpen.value = true
  addresses.value = (await walletApi.withdrawAddresses()) as any[]
}

function addAddress() {
  if (!newAddr.value.address) {
    ElMessage.warning('ADDRESS REQUIRED')
    return
  }
  addresses.value.push({ id: Date.now(), ...newAddr.value })
  newAddr.value = { chain: 'TRC20', address: '' }
  ElMessage.success('ADDRESS ADDED')
}

async function withdraw() {
  ElMessage.info('SPECIFY AMOUNT & ADDRESS (DEMO)')
}
</script>

<template>
  <div class="wallet-page">
    <div class="sec-head">
      <div class="sec-title"><span class="amber">04 //</span> WALLET · BALANCE · RESOURCES · LEDGER</div>
      <div class="sec-coord">{{ renderTs }}</div>
    </div>

    <div class="asset-row">
      <div class="asset-cell">
        <div class="k">USDT BALANCE</div>
        <div class="v amber">${{ formatNum(wallet.balance, 2) }}</div>
        <div class="sub">MIN WITHDRAWAL 5 USDT</div>
      </div>
      <div class="asset-cell">
        <div class="k">CUMULATIVE WITHDRAWN</div>
        <div class="v">${{ formatNum(wallet.withdrawn, 2) }}</div>
        <div class="sub">HISTORICAL TOTAL</div>
      </div>
      <div class="asset-cell actions">
        <div class="k">OPERATIONS</div>
        <div class="act-row">
          <button class="btn-cta primary" @click="rechargeOpen = true">RECHARGE</button>
          <button class="btn-cta" @click="withdraw">WITHDRAW</button>
          <button class="btn-cta" @click="openAddrDialog">ADDR MGT</button>
        </div>
      </div>
    </div>

    <!-- Resources -->
    <div class="block">
      <div class="block-head">
        <span><span class="amber">// RESOURCES</span> · ACTIVE SUBSCRIPTIONS</span>
        <span class="dim">{{ wallet.resources.length }} ITEMS</span>
      </div>
      <table v-if="wallet.resources.length" class="t-table">
        <thead>
          <tr>
            <th>PRODUCT</th>
            <th>PURCHASED</th>
            <th>LAST RENEWED</th>
            <th>EXPIRES</th>
            <th>AUTO RENEW</th>
            <th class="r">OPS</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in wallet.resources" :key="r.id">
            <td>{{ r.product }}</td>
            <td class="t">{{ r.bought_at }}</td>
            <td class="t">{{ r.renew_at }}</td>
            <td class="amber">{{ r.expire_at }}</td>
            <td>
              <el-switch v-model="r.auto_renew" size="small" />
            </td>
            <td class="r"><button class="link">RENEW</button></td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">— NO ACTIVE RESOURCES —</div>
    </div>

    <!-- Ledger -->
    <div class="block">
      <div class="block-head">
        <span><span class="amber">// LEDGER</span> · TRANSACTION HISTORY</span>
        <span class="dim">{{ wallet.txns.length }} ENTRIES</span>
      </div>
      <table v-if="wallet.txns.length" class="t-table">
        <thead>
          <tr>
            <th>TYPE</th>
            <th>DATE</th>
            <th class="r">AMOUNT (USDT)</th>
            <th>SOURCE / DESTINATION</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in wallet.txns" :key="t.id">
            <td class="amber">{{ t.type }}</td>
            <td class="t">{{ t.date }}</td>
            <td class="r" :class="t.amount >= 0 ? 'pos' : 'neg'">
              {{ formatSigned(t.amount, 2) }}
            </td>
            <td>{{ t.source }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">— NO TRANSACTIONS —</div>
    </div>

    <RechargeDialog v-model="rechargeOpen" />

    <el-dialog v-model="addrDialogOpen" :show-close="false" width="600px">
      <template #header>
        <div class="dlg-head">// WITHDRAW_ADDRESS_MGT</div>
      </template>
      <div class="addr-form">
        <el-select v-model="newAddr.chain" style="width:130px">
          <el-option label="TRC20" value="TRC20" />
          <el-option label="ERC20" value="ERC20" />
        </el-select>
        <input v-model="newAddr.address" class="inp-term" style="flex:1" placeholder="USDT ADDRESS" />
        <button class="btn-term primary" @click="addAddress">ADD</button>
      </div>
      <table class="t-table" style="margin-top:14px">
        <thead><tr><th>CHAIN</th><th>ADDRESS</th></tr></thead>
        <tbody>
          <tr v-for="a in addresses" :key="a.id">
            <td class="amber">{{ a.chain }}</td>
            <td class="addr">{{ a.address }}</td>
          </tr>
        </tbody>
      </table>
    </el-dialog>
  </div>
</template>

<style scoped>
.wallet-page {
  padding: 18px 18px 60px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 1280px;
  margin: 0 auto;
}

.asset-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
  border: 1px solid var(--ct-divider);
}
.asset-cell {
  padding: 18px 18px;
  border-right: 1px solid var(--ct-divider);
}
.asset-cell:last-child { border-right: 0; }
.asset-cell .k {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 8px;
}
.asset-cell .v {
  font-size: 26px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--ct-text);
  font-variant-numeric: tabular-nums;
}
.asset-cell .v.amber { color: var(--ct-amber); }
.asset-cell .sub {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-top: 6px;
}
.asset-cell.actions { display: flex; flex-direction: column; gap: 8px; }
.act-row { display: flex; gap: 8px; flex-wrap: wrap; }
.btn-cta {
  height: 32px;
  padding: 0 14px;
  border: 1px solid var(--ct-divider-strong);
  background: transparent;
  color: var(--ct-text);
  font-family: var(--ct-font-mono);
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
}
.btn-cta:hover { border-color: var(--ct-amber); color: var(--ct-amber); }
.btn-cta.primary {
  background: var(--ct-amber);
  border-color: var(--ct-amber);
  color: #0A0E14;
  font-weight: 600;
}

.block { border: 1px solid var(--ct-divider); }
.block-head {
  padding: 8px 12px;
  background: var(--ct-bg-2);
  border-bottom: 1px solid var(--ct-divider);
  display: flex;
  justify-content: space-between;
  font-family: var(--ct-font-mono);
  font-size: 11px;
  color: var(--ct-text-2);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.block-head .amber { color: var(--ct-amber); }
.block-head .dim { color: var(--ct-text-3); }

.t-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--ct-font-mono);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}
.t-table th,
.t-table td {
  height: 30px;
  padding: 0 12px;
  text-align: left;
  border-bottom: 1px solid var(--ct-divider);
}
.t-table th {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  background: var(--ct-bg-2);
  font-weight: 500;
}
.t-table .r { text-align: right; }
.t-table .t { color: var(--ct-text-dim); }
.t-table .amber { color: var(--ct-amber); }
.t-table .pos { color: var(--ct-pos); }
.t-table .neg { color: var(--ct-neg); }
.t-table .addr { color: var(--ct-amber); word-break: break-all; }
.empty {
  text-align: center;
  padding: 30px 0;
  color: var(--ct-text-3);
  font-family: var(--ct-font-mono);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.link {
  background: transparent;
  border: 0;
  color: var(--ct-amber);
  font-family: var(--ct-font-mono);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  cursor: pointer;
}

.dlg-head {
  font-family: var(--ct-font-mono);
  font-size: 11px;
  color: var(--ct-amber);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.addr-form { display: flex; gap: 10px; align-items: center; }
.inp-term {
  height: 30px;
  background: var(--ct-bg-2);
  border: 1px solid var(--ct-divider);
  color: var(--ct-text);
  padding: 0 10px;
  font-family: var(--ct-font-mono);
  font-size: 12px;
  outline: 0;
}
.inp-term:focus { border-color: var(--ct-amber); }
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
.btn-term.primary {
  background: var(--ct-amber);
  border-color: var(--ct-amber);
  color: #0A0E14;
  font-weight: 600;
}

@media (max-width: 768px) {
  .asset-row { grid-template-columns: 1fr; }
  .asset-cell { border-right: 0; border-bottom: 1px solid var(--ct-divider); }
}
</style>
