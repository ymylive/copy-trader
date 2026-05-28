<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAccountsStore } from '@/stores/accounts'

const accStore = useAccountsStore()
const loggedIn = ref(false)
const form = ref({ username: '', password: '' })
const traders = ref<any[]>([])

const currentAccount = computed(() => accStore.current)

onMounted(async () => {
  await accStore.load()
})

function login() {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请填写账号和密码')
    return
  }
  loggedIn.value = true
  traders.value = [
    { id: 'BC10293', nickname: '币Coin · 阿森的笔记', total_pnl: 12482, roi: 17.8 },
    { id: 'BC93421', nickname: '币Coin · 资深操盘', total_pnl: 30210, roi: 24.3 }
  ]
  ElMessage.success('登录成功，已获取交易员列表（mock）')
}

function logout() {
  loggedIn.value = false
  traders.value = []
}
</script>

<template>
  <div class="bicoin-page">
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

    <div v-if="!loggedIn" class="login-card ct-card">
      <div class="hdr">登录币Coin账户 <span class="muted">账户</span></div>
      <div class="form-line">
        <el-input v-model="form.username" placeholder="用户名 / 手机号" style="flex:1" />
        <span class="lbl">密码</span>
        <el-input v-model="form.password" type="password" show-password placeholder="密码" style="flex:1" />
        <el-button type="primary" @click="login">登录</el-button>
      </div>
      <div class="hint">登录信息仅用于代理登录币Coin获取交易员数据，不会上传或保存明文。</div>
    </div>

    <div v-else class="ct-card list-card">
      <div class="card-head">
        <span>已登录币Coin · 交易员列表</span>
        <el-button text type="primary" @click="logout">退出登录</el-button>
      </div>
      <el-table :data="traders">
        <el-table-column label="交易员" prop="nickname" />
        <el-table-column label="ID" prop="id" />
        <el-table-column label="总盈亏 (USDT)" align="right">
          <template #default="{ row }"><span class="mono ct-pos">{{ row.total_pnl.toLocaleString('en') }}</span></template>
        </el-table-column>
        <el-table-column label="收益率" align="right">
          <template #default="{ row }"><span class="mono ct-pos">{{ row.roi.toFixed(2) }}%</span></template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default>
            <el-button type="primary" size="small">启动跟单</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.bicoin-page { display: flex; flex-direction: column; gap: 14px; }
.warning {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.16);
  color: #B91C1C;
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 12px;
  line-height: 1.6;
}
.account-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.lbl { color: var(--ct-text-1); font-weight: 600; }
.info { color: var(--ct-text-2); font-size: 13px; }
.login-card { padding: 22px; }
.hdr { color: var(--ct-primary); font-weight: 600; margin-bottom: 14px; }
.muted { color: var(--ct-text-3); margin-left: 6px; }
.form-line { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.hint { color: var(--ct-text-3); font-size: 12px; margin-top: 12px; }
.list-card { padding: 20px; }
.card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-weight: 600; color: var(--ct-text-1); }
</style>
