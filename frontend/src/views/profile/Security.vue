<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { mockLoginHistory } from '@/mock/data'
import { formatUTC } from '@/utils/format'

const ipHistory = ref(mockLoginHistory())
const pwdOpen = ref(false)
const phoneOpen = ref(false)
const emailOpen = ref(false)
const renderTs = ref(formatUTC())

const pwdForm = ref({ old: '', n1: '', n2: '' })
const phoneForm = ref({ phone: '', code: '' })
const emailForm = ref({ email: '', code: '' })

function changePwd() {
  if (!pwdForm.value.n1 || pwdForm.value.n1 !== pwdForm.value.n2) {
    ElMessage.warning('PASSWORD MISMATCH')
    return
  }
  pwdOpen.value = false
  ElMessage.success('PASSWORD UPDATED')
}
function bindPhone() {
  if (!phoneForm.value.phone) return
  phoneOpen.value = false
  ElMessage.success('PHONE BOUND')
}
function bindEmail() {
  if (!emailForm.value.email) return
  emailOpen.value = false
  ElMessage.success('EMAIL BOUND')
}
</script>

<template>
  <div class="sec-page">
    <div class="sec-head">
      <div class="sec-title"><span class="amber">06 //</span> SECURITY · CREDENTIALS · ACCESS LOG</div>
      <div class="sec-coord">{{ renderTs }}</div>
    </div>

    <!-- 3 actions row -->
    <div class="actions-row">
      <div class="act-cell">
        <div class="k">PASSWORD</div>
        <p class="desc">ROTATE PERIODICALLY · ENFORCE COMPLEXITY</p>
        <button class="btn-cta" @click="pwdOpen = true">CHANGE →</button>
      </div>
      <div class="act-cell">
        <div class="k">PHONE BINDING</div>
        <p class="desc">PRIMARY 2FA · SMS RECOVERY</p>
        <button class="btn-cta" @click="phoneOpen = true">UPDATE →</button>
      </div>
      <div class="act-cell">
        <div class="k">EMAIL BINDING</div>
        <p class="desc">NOTIFICATIONS · BACKUP CHANNEL</p>
        <button class="btn-cta" @click="emailOpen = true">UPDATE →</button>
      </div>
    </div>

    <!-- Login history -->
    <div class="block">
      <div class="block-head">
        <span><span class="amber">// LOGIN_HISTORY</span> · LAST 10 SESSIONS</span>
        <span class="dim">{{ ipHistory.length }} ENTRIES</span>
      </div>
      <table class="t-table">
        <thead>
          <tr>
            <th>#</th>
            <th>IP</th>
            <th>REGION</th>
            <th>TS (UTC)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in ipHistory" :key="row.ip + row.time">
            <td>{{ String(i + 1).padStart(2, '0') }}</td>
            <td class="amber">{{ row.ip }}</td>
            <td>{{ row.region }}</td>
            <td class="t">{{ row.time }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modals -->
    <el-dialog v-model="pwdOpen" :show-close="false" width="420px">
      <template #header><div class="dlg-h">// CHANGE_PASSWORD</div></template>
      <div class="dlg-body">
        <div class="field">
          <label>CURRENT PASSWORD</label>
          <input v-model="pwdForm.old" type="password" class="inp-term" />
        </div>
        <div class="field">
          <label>NEW PASSWORD</label>
          <input v-model="pwdForm.n1" type="password" class="inp-term" />
        </div>
        <div class="field">
          <label>CONFIRM NEW</label>
          <input v-model="pwdForm.n2" type="password" class="inp-term" />
        </div>
      </div>
      <template #footer>
        <button class="btn-term" @click="pwdOpen = false">CANCEL</button>
        <button class="btn-term primary" @click="changePwd">CONFIRM</button>
      </template>
    </el-dialog>

    <el-dialog v-model="phoneOpen" :show-close="false" width="420px">
      <template #header><div class="dlg-h">// BIND_PHONE</div></template>
      <div class="dlg-body">
        <div class="field">
          <label>PHONE NUMBER</label>
          <input v-model="phoneForm.phone" class="inp-term" />
        </div>
        <div class="field">
          <label>SMS CODE</label>
          <input v-model="phoneForm.code" class="inp-term" />
        </div>
      </div>
      <template #footer>
        <button class="btn-term" @click="phoneOpen = false">CANCEL</button>
        <button class="btn-term primary" @click="bindPhone">BIND</button>
      </template>
    </el-dialog>

    <el-dialog v-model="emailOpen" :show-close="false" width="420px">
      <template #header><div class="dlg-h">// BIND_EMAIL</div></template>
      <div class="dlg-body">
        <div class="field">
          <label>EMAIL</label>
          <input v-model="emailForm.email" class="inp-term" />
        </div>
        <div class="field">
          <label>EMAIL CODE</label>
          <input v-model="emailForm.code" class="inp-term" />
        </div>
      </div>
      <template #footer>
        <button class="btn-term" @click="emailOpen = false">CANCEL</button>
        <button class="btn-term primary" @click="bindEmail">BIND</button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.sec-page {
  padding: 18px 18px 60px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 1280px;
  margin: 0 auto;
}

.actions-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border: 1px solid var(--ct-divider);
}
.act-cell {
  padding: 18px;
  border-right: 1px solid var(--ct-divider);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.act-cell:last-child { border-right: 0; }
.act-cell .k {
  color: var(--ct-amber);
  font-family: var(--ct-font-mono);
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-weight: 600;
}
.act-cell .desc {
  color: var(--ct-text-2);
  font-family: var(--ct-font-mono);
  font-size: 11px;
  line-height: 1.6;
  margin: 0;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.btn-cta {
  margin-top: auto;
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
  align-self: flex-start;
}
.btn-cta:hover { border-color: var(--ct-amber); color: var(--ct-amber); }

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
  font-weight: 500;
}
.t-table .amber { color: var(--ct-amber); }
.t-table .t { color: var(--ct-text-dim); font-variant-numeric: tabular-nums; }

.dlg-h {
  font-family: var(--ct-font-mono);
  font-size: 11px;
  color: var(--ct-amber);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.dlg-body { display: flex; flex-direction: column; gap: 14px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-family: var(--ct-font-mono);
}
.inp-term {
  height: 30px;
  background: var(--ct-bg-2);
  border: 1px solid var(--ct-divider);
  color: var(--ct-text);
  padding: 0 10px;
  font-family: var(--ct-font-mono);
  font-size: 13px;
  outline: 0;
}
.inp-term:focus { border-color: var(--ct-amber); }
.btn-term {
  height: 32px;
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

@media (max-width: 900px) {
  .actions-row { grid-template-columns: 1fr; }
  .act-cell { border-right: 0; border-bottom: 1px solid var(--ct-divider); }
}
</style>
