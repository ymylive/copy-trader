<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { inviteApi } from '@/api/invite'
import { formatNum, formatUTC } from '@/utils/format'

const summary = ref<any>({ uid: 0, level: 1, rebate_pct: 10, total_rebate: 0, invite_link: '' })
const records = ref<any[]>([])
const renderTs = ref(formatUTC())

onMounted(async () => {
  summary.value = await inviteApi.summary()
  records.value = (await inviteApi.records()) as any[]
})

async function copyLink() {
  await navigator.clipboard.writeText(summary.value.invite_link)
  ElMessage.success('INVITE LINK COPIED')
}

async function withdraw() {
  await inviteApi.withdraw()
  ElMessage.success('WITHDRAWAL REQUESTED')
}
</script>

<template>
  <div class="inv-page">
    <div class="sec-head">
      <div class="sec-title"><span class="amber">05 //</span> REFERRAL · REBATE TIER · LINK</div>
      <div class="sec-coord">{{ renderTs }}</div>
    </div>

    <div class="asset-row">
      <div class="asset-cell">
        <div class="k">REBATE TIER</div>
        <div class="v amber">LEVEL {{ summary.level }}</div>
        <div class="sub">RATE {{ summary.rebate_pct }}%</div>
      </div>
      <div class="asset-cell">
        <div class="k">CUMULATIVE REBATE</div>
        <div class="v">${{ formatNum(summary.total_rebate, 2) }}</div>
        <div class="sub">LIFETIME · USDT EQ</div>
      </div>
      <div class="asset-cell">
        <div class="k">YOUR UID</div>
        <div class="v amber">{{ summary.uid }}</div>
        <div class="sub">SHARE LINK BELOW</div>
      </div>
      <div class="asset-cell actions">
        <div class="k">OPERATIONS</div>
        <div class="act-row">
          <button class="btn-cta primary" @click="copyLink">COPY LINK</button>
          <button class="btn-cta" @click="withdraw">WITHDRAW</button>
        </div>
      </div>
    </div>

    <!-- link block -->
    <div class="block">
      <div class="block-head">
        <span><span class="amber">// INVITE_LINK</span> · DISTRIBUTE TO PROSPECTIVE USERS</span>
        <span class="dim">+1 DISCOUNT COUPON / SIGNUP</span>
      </div>
      <div class="link-row">
        <span class="lbl">URL:</span>
        <span class="url">{{ summary.invite_link }}</span>
        <button class="link" @click="copyLink">COPY</button>
      </div>
      <div class="explain">
        ⓘ ON SUBSCRIPTION PURCHASE, YOU EARN {{ summary.rebate_pct }}% REBATE OF PAID AMOUNT.
        EACH UNIQUE INVITEE ALSO YIELDS ONE 15% DISCOUNT COUPON USABLE ON MAIN PLANS.
      </div>
    </div>

    <!-- records -->
    <div class="block">
      <div class="block-head">
        <span><span class="amber">// LEDGER</span> · INVITATION ACTIVITY</span>
        <span class="dim">{{ records.length }} ENTRIES</span>
      </div>
      <table v-if="records.length" class="t-table">
        <thead>
          <tr>
            <th>#</th>
            <th>INVITEE UID</th>
            <th>SIGNUP TS (UTC)</th>
            <th class="r">REBATE (USDT)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(r, i) in records" :key="r.id">
            <td>{{ String(i + 1).padStart(3, '0') }}</td>
            <td class="amber">{{ r.invitee_uid }}</td>
            <td class="t">{{ r.created_at }}</td>
            <td class="r pos">+{{ formatNum(r.reward, 2) }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">— NO REFERRALS YET · SHARE THE LINK ABOVE —</div>
    </div>
  </div>
</template>

<style scoped>
.inv-page {
  padding: 18px 18px 60px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 1280px;
  margin: 0 auto;
}

.asset-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1px solid var(--ct-divider);
}
.asset-cell {
  padding: 18px;
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
  font-size: 22px;
  font-weight: 600;
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

.link-row {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid var(--ct-divider);
  flex-wrap: wrap;
}
.link-row .lbl {
  color: var(--ct-text-3);
  font-family: var(--ct-font-mono);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.link-row .url {
  color: var(--ct-amber);
  font-family: var(--ct-font-mono);
  font-size: 12px;
  word-break: break-all;
  flex: 1;
}
.link {
  background: transparent;
  border: 1px solid var(--ct-divider-strong);
  color: var(--ct-text-2);
  font-family: var(--ct-font-mono);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 4px 10px;
  cursor: pointer;
}
.link:hover { color: var(--ct-amber); border-color: var(--ct-amber); }

.explain {
  padding: 12px 16px;
  font-family: var(--ct-font-mono);
  font-size: 11px;
  color: var(--ct-text-2);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  line-height: 1.6;
}

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
  font-weight: 500;
  background: var(--ct-bg-2);
}
.t-table .r { text-align: right; }
.t-table .pos { color: var(--ct-pos); }
.t-table .amber { color: var(--ct-amber); }
.t-table .t { color: var(--ct-text-dim); }
.empty {
  text-align: center;
  padding: 30px 0;
  color: var(--ct-text-3);
  font-family: var(--ct-font-mono);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

@media (max-width: 1024px) {
  .asset-row { grid-template-columns: repeat(2, 1fr); }
  .asset-cell:nth-child(2) { border-right: 0; }
}
</style>
