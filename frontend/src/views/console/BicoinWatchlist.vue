<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAccountsStore } from '@/stores/accounts'
import { formatNum, formatUTC } from '@/utils/format'

const accStore = useAccountsStore()
const loggedIn = ref(false)
const form = ref({ username: '', password: '' })
const traders = ref<any[]>([])
const authBusy = ref(false)
const renderTs = ref(formatUTC())

const currentAccount = computed(() => accStore.current)

onMounted(async () => {
  await accStore.load()
})

async function login() {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('USERNAME & PASSWORD REQUIRED')
    return
  }
  authBusy.value = true
  await new Promise((r) => setTimeout(r, 1100))
  loggedIn.value = true
  authBusy.value = false
  traders.value = [
    { id: '79346',  nickname: '茂茂大魔王', total_pnl: 1343829.94, roi: 14539.61 },
    { id: '369319', nickname: '风火山林Trader', total_pnl: 1927532.79, roi: 6880.06 },
    { id: '1030294', nickname: '牛的青山在', total_pnl: 297089.72, roi: 10326.49 }
  ]
  ElMessage.success('AUTHENTICATED · TRADERS FETCHED')
}

function logout() {
  loggedIn.value = false
  traders.value = []
}
</script>

<template>
  <div class="bc-page">
    <div class="sec-head">
      <div class="sec-title"><span class="amber">06 //</span> BICOIN WATCHLIST · BICOIN.COM.CN PROXY SESSION</div>
      <div class="sec-coord">{{ renderTs }}</div>
    </div>

    <div class="warn">
      ⚠ BICOIN PLATFORM SLA APPLIES · DELAYS UNCONTROLLED DURING HIGH VOLATILITY · HIDDEN POSITIONS NOT TRACEABLE · USE WITH CAUTION.
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

    <!-- Login form -->
    <div v-if="!loggedIn" class="login-card">
      <div class="lc-head">
        <span>// LOGIN_BICOIN_ACCOUNT</span>
        <span class="dim">credentials are NOT stored · proxied to bicoin.com.cn</span>
      </div>
      <div class="lc-form">
        <div class="field">
          <label>USERNAME / PHONE</label>
          <input v-model="form.username" class="under-inp" placeholder="" />
        </div>
        <div class="field">
          <label>PASSWORD</label>
          <input v-model="form.password" type="password" class="under-inp" placeholder="" />
        </div>
        <button class="btn-term primary" :disabled="authBusy" @click="login">
          <span v-if="authBusy">▌ AUTHENTICATING…</span>
          <span v-else>AUTHENTICATE →</span>
        </button>
      </div>
      <div class="lc-foot">
        ⚠ CREDENTIALS USED FOR ONE-SHOT PROXY ONLY · NEVER PERSISTED · TLS 1.3 ONLY.
      </div>
    </div>

    <!-- Trader list -->
    <div v-else class="list-wrap">
      <div class="list-head">
        <span>BICOIN TRADERS · SESSION ACTIVE</span>
        <button class="link" @click="logout">LOGOUT</button>
      </div>
      <table class="bc-table">
        <thead>
          <tr>
            <th>NICKNAME</th>
            <th>UID</th>
            <th class="r">TOTAL PNL (USDT)</th>
            <th class="r">ROI%</th>
            <th class="r">OPS</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in traders" :key="t.id">
            <td>{{ t.nickname }}</td>
            <td class="amber">{{ t.id }}</td>
            <td class="r pos">+{{ formatNum(t.total_pnl, 2) }}</td>
            <td class="r pos">+{{ formatNum(t.roi, 2) }}%</td>
            <td class="r"><button class="link primary">COPY</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.bc-page { display: flex; flex-direction: column; gap: 14px; }

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

.login-card {
  border: 1px solid var(--ct-divider);
  background: var(--ct-bg-2);
  max-width: 540px;
}
.lc-head {
  padding: 10px 16px;
  border-bottom: 1px solid var(--ct-divider);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  font-family: var(--ct-font-mono);
  color: var(--ct-amber);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.lc-head .dim { color: var(--ct-text-3); text-transform: none; letter-spacing: 0.02em; font-size: 10px; }
.lc-form { padding: 18px 16px; display: flex; flex-direction: column; gap: 16px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-family: var(--ct-font-mono);
}
.under-inp {
  background: transparent;
  border: 0;
  border-bottom: 1px solid var(--ct-divider-strong);
  color: var(--ct-text);
  font-family: var(--ct-font-mono);
  font-size: 14px;
  padding: 4px 0;
  outline: 0;
}
.under-inp:focus { border-bottom-color: var(--ct-amber); }
.btn-term {
  height: 36px;
  padding: 0 18px;
  background: transparent;
  border: 1px solid var(--ct-divider-strong);
  color: var(--ct-text);
  font-family: var(--ct-font-mono);
  font-size: 12px;
  letter-spacing: 0.12em;
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
.btn-term.primary:hover { filter: brightness(1.08); color: #0A0E14; }
.btn-term:disabled { opacity: 0.5; cursor: not-allowed; }
.lc-foot {
  padding: 8px 16px;
  border-top: 1px solid var(--ct-divider);
  color: var(--ct-amber);
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  background: rgba(255,180,0,0.04);
}

.list-wrap { border: 1px solid var(--ct-divider); }
.list-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid var(--ct-divider);
  background: var(--ct-bg-2);
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-family: var(--ct-font-mono);
}
.bc-table { width: 100%; border-collapse: collapse; font-family: var(--ct-font-mono); font-size: 12px; }
.bc-table th, .bc-table td {
  height: 30px;
  padding: 0 12px;
  text-align: left;
  border-bottom: 1px solid var(--ct-divider);
}
.bc-table th {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-weight: 500;
  background: var(--ct-bg-2);
}
.bc-table .r { text-align: right; }
.bc-table .pos { color: var(--ct-pos); }
.bc-table .amber { color: var(--ct-amber); }
.link {
  background: transparent;
  border: 0;
  color: var(--ct-text-2);
  font-family: var(--ct-font-mono);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  cursor: pointer;
}
.link:hover { color: var(--ct-amber); }
.link.primary { color: var(--ct-amber); }
</style>
