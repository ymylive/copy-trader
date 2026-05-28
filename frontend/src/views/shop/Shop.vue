<script setup lang="ts">
import { onMounted, reactive, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { shopApi } from '@/api/shop'
import { formatNum, formatUTC } from '@/utils/format'

const products = ref<any[]>([])
const trialForm = reactive({ exchange: '', uid: '' })
const orderForm = reactive({
  period: '1m',
  exchange: '',
  uid: '',
  coupon: '',
  product_id: 'slot_order'
})
const verified = ref(false)
const renderTs = ref(formatUTC())

onMounted(async () => {
  products.value = (await shopApi.products()) as any[]
})

const periodLabel: Record<string, string> = {
  '1m': '/MO',  '3m': '/3MO', '6m': '/6MO',
  '1y': '/YR',  perm: 'ONE-TIME', contact: 'CONTACT'
}
const periodFull: Record<string, string> = {
  '1m': '1 MONTH', '3m': '3 MONTHS', '6m': '6 MONTHS',
  '1y': '12 MONTHS', perm: 'PERMANENT', contact: 'CONTACT ADMIN'
}

const exchanges = ['BINANCE', 'OKX', 'GATE', 'BITGET']

async function claimTrial() {
  if (!trialForm.exchange || !trialForm.uid) {
    ElMessage.warning('SELECT VENUE & ENTER UID')
    return
  }
  await shopApi.claimTrial(0, trialForm.exchange, trialForm.uid)
  ElMessage.success('TRIAL ISSUED · 7 DAYS')
}

function verifyInvite() {
  if (!orderForm.uid) {
    ElMessage.warning('UID REQUIRED')
    return
  }
  verified.value = true
  ElMessage.success(`RECEIVER UID ${orderForm.uid} VERIFIED · 50% OFF`)
}

async function buy(productId: string) {
  await shopApi.order({
    product_id: productId,
    period: orderForm.period,
    coupon: orderForm.coupon
  })
  ElMessage.success('ORDER PLACED')
}

const totalPrice = computed(() => {
  const periodMultiplier = { '1m': 1, '3m': 3, '6m': 6, '1y': 12 }
  const mult = periodMultiplier[orderForm.period as keyof typeof periodMultiplier] || 1
  const base = 80 * mult
  return verified.value ? base / 2 : base
})

function pricingOf(p: any): string {
  if (p.id === 'slot_fast') return '$999 999'
  return `$${p.price.toFixed(2)}`
}
</script>

<template>
  <div class="shop-page">
    <div class="sec-head">
      <div class="sec-title"><span class="amber">03 //</span> PRICING · ORDER SLOTS · ADD-ONS</div>
      <div class="sec-coord">{{ renderTs }}</div>
    </div>

    <!-- Trial + main order -->
    <div class="top-grid">
      <!-- TRIAL -->
      <div class="card trial-card">
        <div class="card-head">
          <span>// 7-DAY TRIAL · COMPLIMENTARY</span>
          <span class="badge amber"><span class="dot"></span>1 PER ACCOUNT</span>
        </div>
        <div class="card-body">
          <div class="field">
            <label>EXCHANGE</label>
            <el-select v-model="trialForm.exchange" placeholder="SELECT" style="width:100%">
              <el-option v-for="e in exchanges" :key="e" :label="e" :value="e" />
            </el-select>
          </div>
          <div class="field">
            <label>UID</label>
            <input v-model="trialForm.uid" class="inp-term" placeholder="" />
          </div>
          <button class="btn-cta primary" @click="claimTrial">CLAIM TRIAL →</button>
        </div>
      </div>

      <!-- ORDER SLOT -->
      <div class="card primary-card">
        <div class="card-head">
          <span>// ORDER_SLOT · PER ACCOUNT</span>
          <span class="dim">RENEWABLE · MONTH-TO-MONTH</span>
        </div>
        <div class="card-body">
          <div class="field">
            <label>BILLING PERIOD</label>
            <div class="radio-row">
              <div class="opt" :class="{ active: orderForm.period === '1m' }" @click="orderForm.period = '1m'">1 MO</div>
              <div class="opt" :class="{ active: orderForm.period === '3m' }" @click="orderForm.period = '3m'">3 MO</div>
              <div class="opt" :class="{ active: orderForm.period === '6m' }" @click="orderForm.period = '6m'">6 MO</div>
              <div class="opt" :class="{ active: orderForm.period === '1y' }" @click="orderForm.period = '1y'">1 YR</div>
            </div>
          </div>

          <div class="note">
            ⓘ PROVIDE REGISTERED EXCHANGE UID FOR <span class="amber">50% OFF</span> · LIMITED TO INVITED ACCOUNTS.
          </div>

          <div class="field">
            <label>EXCHANGE</label>
            <el-select v-model="orderForm.exchange" placeholder="SELECT" style="width:100%">
              <el-option v-for="e in exchanges" :key="e" :label="e" :value="e" />
            </el-select>
          </div>
          <div class="field">
            <label>RECEIVER UID</label>
            <div class="uid-row">
              <input v-model="orderForm.uid" class="inp-term" style="flex:1" placeholder="" />
              <button class="btn-term" @click="verifyInvite">VERIFY</button>
            </div>
          </div>
          <div v-if="verified" class="verified">[receiver UID verified · 50% off]</div>

          <div class="field">
            <label>COUPON</label>
            <el-select v-model="orderForm.coupon" placeholder="NONE" style="width:100%">
              <el-option label="NONE" value="" />
              <el-option label="DISC85 · 15% OFF" value="DISC85" />
            </el-select>
          </div>

          <div class="total-row">
            <div class="t-lhs">
              <div class="amber-tip">⚠ MONTHLY RENEWAL · CANCEL ANYTIME IN WALLET</div>
              <div class="dim">50% OFF SLOTS ARE LOCKED TO INVITED API KEYS</div>
            </div>
            <div class="t-rhs">
              <div class="total-line">
                <span class="lbl">TOTAL</span>
                <span class="amount">${{ formatNum(totalPrice, 2) }}<span class="period">{{ periodLabel[orderForm.period] }}</span></span>
              </div>
              <button class="btn-cta primary" @click="buy('slot_order')">PURCHASE →</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add-ons -->
    <div class="sec-head">
      <div class="sec-title"><span class="amber">03-B //</span> ADD-ONS</div>
    </div>
    <div class="addons">
      <div v-for="p in products.filter((x) => x.id !== 'slot_order')" :key="p.id" class="addon">
        <div class="ad-head">
          <span class="ad-name">{{ p.name }}</span>
          <span class="ad-price">{{ pricingOf(p) }}<span class="ad-period">{{ periodLabel[p.periods?.[0]] || '' }}</span></span>
        </div>
        <p class="ad-desc">{{ p.desc }}</p>
        <div class="ad-period-full">{{ periodFull[p.periods?.[0]] || '' }}</div>
        <button
          v-if="p.id === 'slot_fast'"
          class="btn-term"
          disabled
        >
          CONTACT ADMIN
        </button>
        <button
          v-else
          class="btn-term primary"
          @click="buy(p.id)"
        >
          PURCHASE →
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.shop-page {
  padding: 18px 18px 60px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 1280px;
  margin: 0 auto;
}

.top-grid {
  display: grid;
  grid-template-columns: 1fr 1.6fr;
  gap: 24px;
}

.card {
  border: 1px solid var(--ct-divider);
  background: var(--ct-bg-2);
}
.card-head {
  padding: 10px 14px;
  border-bottom: 1px solid var(--ct-divider);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-family: var(--ct-font-mono);
  font-size: 11px;
  color: var(--ct-amber);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.card-head .dim { color: var(--ct-text-3); text-transform: none; letter-spacing: 0.04em; font-size: 10px; }

.card-body { padding: 14px; display: flex; flex-direction: column; gap: 14px; }
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
.uid-row { display: flex; gap: 8px; align-items: center; }

.btn-cta {
  height: 36px;
  border: 1px solid var(--ct-divider-strong);
  background: transparent;
  color: var(--ct-text);
  font-family: var(--ct-font-mono);
  font-size: 12px;
  letter-spacing: 0.12em;
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
.btn-cta.primary:hover { filter: brightness(1.08); color: #0A0E14; }

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
.btn-term:hover:not(:disabled) { border-color: var(--ct-amber); color: var(--ct-amber); }
.btn-term:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-term.primary {
  background: var(--ct-amber);
  border-color: var(--ct-amber);
  color: #0A0E14;
  font-weight: 600;
}

.radio-row {
  display: flex;
  gap: 0;
  border: 1px solid var(--ct-divider);
}
.radio-row .opt {
  flex: 1;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: var(--ct-text-2);
  border-right: 1px solid var(--ct-divider);
  cursor: pointer;
  letter-spacing: 0.08em;
  font-family: var(--ct-font-mono);
  text-transform: uppercase;
  user-select: none;
}
.radio-row .opt:last-child { border-right: 0; }
.radio-row .opt.active { background: var(--ct-amber); color: #0A0E14; font-weight: 600; }

.note {
  border: 1px solid rgba(255, 180, 0, 0.35);
  background: rgba(255, 180, 0, 0.04);
  color: var(--ct-amber);
  padding: 8px 10px;
  font-size: 10px;
  letter-spacing: 0.06em;
  line-height: 1.6;
  text-transform: uppercase;
  font-family: var(--ct-font-mono);
}
.note .amber { font-weight: 700; }

.verified {
  color: var(--ct-pos);
  font-family: var(--ct-font-mono);
  font-size: 10px;
  letter-spacing: 0.06em;
}

.total-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 18px;
  align-items: end;
  margin-top: 6px;
  padding-top: 12px;
  border-top: 1px solid var(--ct-divider);
}
.t-lhs { font-family: var(--ct-font-mono); font-size: 10px; line-height: 1.6; }
.amber-tip { color: var(--ct-amber); letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 2px; }
.t-lhs .dim { color: var(--ct-text-3); letter-spacing: 0.04em; text-transform: uppercase; }
.t-rhs { display: flex; flex-direction: column; gap: 8px; align-items: flex-end; }
.total-line {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-family: var(--ct-font-mono);
}
.total-line .lbl {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.amount {
  font-size: 24px;
  color: var(--ct-amber);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.amount .period {
  font-size: 11px;
  color: var(--ct-text-3);
  margin-left: 4px;
  letter-spacing: 0.06em;
}

/* Addons */
.addons {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
  border: 1px solid var(--ct-divider);
}
.addon {
  padding: 18px;
  border-right: 1px solid var(--ct-divider);
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.addon:last-child { border-right: 0; }
.ad-head { display: flex; justify-content: space-between; align-items: baseline; }
.ad-name {
  color: var(--ct-amber);
  font-family: var(--ct-font-mono);
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-weight: 600;
}
.ad-price {
  color: var(--ct-text);
  font-family: var(--ct-font-mono);
  font-size: 22px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.ad-period {
  font-size: 10px;
  color: var(--ct-text-3);
  margin-left: 4px;
  letter-spacing: 0.06em;
}
.ad-desc {
  color: var(--ct-text-2);
  font-family: var(--ct-font-mono);
  font-size: 11px;
  line-height: 1.6;
  margin: 0;
}
.ad-period-full {
  color: var(--ct-text-3);
  font-family: var(--ct-font-mono);
  font-size: 10px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

@media (max-width: 1024px) {
  .top-grid { grid-template-columns: 1fr; }
  .addons { grid-template-columns: 1fr; }
  .addon { border-right: 0; border-bottom: 1px solid var(--ct-divider); }
}
</style>
