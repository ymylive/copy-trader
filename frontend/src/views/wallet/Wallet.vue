<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useWalletStore } from '@/stores/wallet'
import RechargeDialog from '@/components/RechargeDialog.vue'
import { walletApi } from '@/api/wallet'

const wallet = useWalletStore()
const rechargeOpen = ref(false)
const addrDialogOpen = ref(false)
const addresses = ref<any[]>([])

const newAddr = ref({ chain: 'TRC20', address: '' })

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
    ElMessage.warning('请输入地址')
    return
  }
  addresses.value.push({ id: Date.now(), ...newAddr.value })
  newAddr.value = { chain: 'TRC20', address: '' }
  ElMessage.success('地址已添加')
}

async function withdraw() {
  ElMessage.info('请输入金额并选择地址（演示）')
}
</script>

<template>
  <div class="wallet-page">
    <div class="grid">
      <div class="card wallet-card">
        <div class="card-head">
          <div class="title">我的钱包</div>
          <a class="link" @click="openAddrDialog">提现地址管理 ⚙</a>
        </div>
        <div class="wallet-body">
          <div class="balance-card">
            <div class="lbl">账户余额</div>
            <div class="num mono">${{ wallet.balance.toFixed(2) }}</div>
            <div class="hint">由于部分交易所限制，金额小于 5USDT 时暂不支持提现</div>
          </div>
          <div class="actions">
            <div class="withdrawn">
              <div class="lbl">已提现金额</div>
              <div class="num mono">${{ wallet.withdrawn.toFixed(2) }}</div>
            </div>
            <el-button type="success" size="large" class="btn" @click="rechargeOpen = true">充值</el-button>
            <el-button size="large" class="btn" @click="withdraw">提现</el-button>
          </div>
        </div>
      </div>

      <div class="card coupon-card">
        <div class="title">优惠券</div>
        <div class="empty">—— 暂无优惠券 ——</div>
      </div>
    </div>

    <div class="section-title">我的资源</div>
    <el-table :data="wallet.resources" empty-text="暂无资源" style="width:100%; margin-bottom:30px">
      <el-table-column label="购买时间" prop="bought_at" />
      <el-table-column label="商品" prop="product" />
      <el-table-column label="续费时间" prop="renew_at" />
      <el-table-column label="到期时间" prop="expire_at" />
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-switch v-model="row.auto_renew" size="small" />
          <span class="muted-sm" style="margin-left:6px">自动续费</span>
          <el-button text type="primary" size="small" style="margin-left:10px">续费</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="section-title">资金明细</div>
    <el-table :data="wallet.txns" empty-text="暂无流水" style="width:100%">
      <el-table-column label="类型" prop="type" width="100" />
      <el-table-column label="日期" prop="date" />
      <el-table-column label="金额">
        <template #default="{ row }">
          <span class="mono" :class="row.amount >= 0 ? 'ct-pos' : 'ct-neg'">
            {{ row.amount >= 0 ? '+' : '' }}{{ row.amount.toFixed(2) }} USDT
          </span>
        </template>
      </el-table-column>
      <el-table-column label="来源 / 目标" prop="source" />
    </el-table>

    <RechargeDialog v-model="rechargeOpen" />

    <el-dialog v-model="addrDialogOpen" title="提现地址管理" width="520px">
      <div class="addr-form">
        <el-select v-model="newAddr.chain" style="width:130px">
          <el-option label="TRC20" value="TRC20" />
          <el-option label="ERC20" value="ERC20" />
        </el-select>
        <el-input v-model="newAddr.address" placeholder="USDT 地址" />
        <el-button type="primary" @click="addAddress">添加</el-button>
      </div>
      <el-table :data="addresses" empty-text="暂无地址" style="margin-top:14px">
        <el-table-column label="链" prop="chain" width="100" />
        <el-table-column label="地址" prop="address" />
      </el-table>
    </el-dialog>
  </div>
</template>

<style scoped>
.wallet-page {
  max-width: 1180px;
  margin: 0 auto;
  padding: 40px 32px 80px;
  color: #e5e7eb;
}
.grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 22px;
}
.card {
  background: rgba(14, 20, 27, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 18px;
  padding: 26px;
}
.card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
.title { font-size: 17px; font-weight: 600; color: #fff; }
.link { color: #9CA3AF; font-size: 13px; cursor: pointer; }
.wallet-body { display: grid; grid-template-columns: 1.2fr 1fr; gap: 18px; align-items: center; }
.balance-card {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(0, 0, 0, 0.2));
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 14px;
  padding: 20px 22px;
}
.lbl { color: #9CA3AF; font-size: 13px; }
.balance-card .num { font-size: 30px; font-weight: 700; color: #fff; margin-top: 6px; }
.hint { color: #6B7280; font-size: 11px; margin-top: 12px; line-height: 1.5; }
.actions { display: flex; flex-direction: column; gap: 12px; }
.withdrawn .num { font-size: 22px; font-weight: 700; color: #fff; margin-top: 4px; }
.btn { width: 100%; }
.coupon-card { display: flex; flex-direction: column; }
.empty { color: #6B7280; text-align: center; padding: 36px 0; }
.section-title { font-size: 18px; color: #fff; margin: 28px 0 12px; font-weight: 600; }
.addr-form { display: flex; gap: 10px; }
.muted-sm { color: #6B7280; font-size: 12px; }
:deep(.el-table) {
  --el-table-bg-color: rgba(14, 20, 27, 0.55);
  --el-table-tr-bg-color: rgba(14, 20, 27, 0.55);
  --el-table-header-bg-color: rgba(14, 20, 27, 0.85);
  --el-table-text-color: #d1d5db;
  --el-table-header-text-color: #9CA3AF;
  --el-table-border-color: rgba(255, 255, 255, 0.05);
  border-radius: 14px;
  overflow: hidden;
}

@media (max-width: 900px) {
  .grid { grid-template-columns: 1fr; }
  .wallet-body { grid-template-columns: 1fr; }
}
</style>
