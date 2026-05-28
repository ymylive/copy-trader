<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { Trader } from '@/api/traders'
import { copyConfigsApi, type CopyConfig } from '@/api/copyConfigs'

interface Props {
  modelValue: boolean
  trader: Trader | null
  accountId?: number
  reverse?: boolean
}
const props = withDefaults(defineProps<Props>(), { reverse: false, accountId: undefined })
const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'submitted', cfg: CopyConfig): void
}>()

const open = computed({
  get: () => props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v)
})

function defaultForm(): CopyConfig {
  return {
    account_id: props.accountId ?? 0,
    trader_id: props.trader?.id ?? '',
    reverse: !!props.reverse,
    capital_mode: 'fixed',
    fixed_amount: 500,
    multiplier: 1,
    start_mode: 'only_loss',
    direction: 'both',
    open_trigger: 'market',
    open_price_better_pct: 0.05,
    add_trigger: 'avg_price',
    add_price_better_pct: 0.10,
    tp_mode: 'cycle',
    tp_close_pct: 30,
    sl_mode: 'cycle',
    sl_close_pct: 100,
    loss_threshold_usdt: 2000,
    safety_floor: 3.5,
    refill_on_tp: true,
    refill_allow_retp: true,
    blacklist: ['DOGE', 'SHIB', 'PEPE'],
    whitelist: ['BTC', 'ETH', 'SOL', 'BNB'],
    notify_channels: ['telegram'],
    notify_types: ['order_success', 'order_fail', 'risk_trigger', 'tp_sl']
  }
}

const form = reactive<CopyConfig>(defaultForm())
const blacklistInput = ref('')
const whitelistInput = ref('')

watch(
  () => props.modelValue,
  (v) => {
    if (v) {
      Object.assign(form, defaultForm())
      blacklistInput.value = ''
      whitelistInput.value = ''
    }
  }
)

const submitting = ref(false)
const cfgHash = computed(() => {
  // pseudo-hash for cosmetic display
  const seed = (props.trader?.id || '') + form.capital_mode + form.fixed_amount + form.multiplier
  let h = 0
  for (let i = 0; i < seed.length; i++) h = ((h << 5) - h + seed.charCodeAt(i)) | 0
  const hex = (h >>> 0).toString(16).toUpperCase().padStart(8, '0')
  return `0x${hex.slice(0, 4)}.${hex.slice(4, 8)}`
})

function toggleArr(arr: string[], v: string) {
  const i = arr.indexOf(v)
  if (i >= 0) arr.splice(i, 1)
  else arr.push(v)
}

function removeChip(arr: string[], v: string) {
  const i = arr.indexOf(v)
  if (i >= 0) arr.splice(i, 1)
}

function addBlack() {
  const v = blacklistInput.value.trim().toUpperCase()
  if (v && !form.blacklist.includes(v)) form.blacklist.push(v)
  blacklistInput.value = ''
}
function addWhite() {
  const v = whitelistInput.value.trim().toUpperCase()
  if (v && !form.whitelist.includes(v)) form.whitelist.push(v)
  whitelistInput.value = ''
}

async function submit() {
  if (form.capital_mode === 'fixed' && (!form.fixed_amount || form.fixed_amount <= 0)) {
    ElMessage.warning('FIXED AMOUNT REQUIRED')
    return
  }
  submitting.value = true
  try {
    await copyConfigsApi.create(form)
    ElMessage.success('COPY JOB STARTED')
    emit('submitted', { ...form })
    open.value = false
  } finally {
    submitting.value = false
  }
}

const notifyChannel = computed({
  get: () => form.notify_channels[0] || 'none',
  set: (v: string) => { form.notify_channels = [v] }
})
</script>

<template>
  <el-dialog
    v-model="open"
    :show-close="false"
    width="940px"
    :close-on-click-modal="false"
    append-to-body
    align-center
    class="cfg-modal"
  >
    <template #header>
      <div class="modal-head">
        <div class="left">
          <span>TASK CONFIG</span>
          <span class="dim">·</span>
          <span>TRADER <span class="amber">{{ trader?.exchange?.toUpperCase() }}:{{ trader?.id }} / {{ trader?.nickname }}</span></span>
          <span class="dim">·</span>
          <span>CFG_{{ reverse ? '02 · INVERSE' : '01' }}</span>
        </div>
        <div class="right">
          <span class="badge green"><span class="dot"></span>DRAFT</span>
          <span class="x" @click="open = false">[ X ]</span>
        </div>
      </div>
    </template>

    <div class="modal-body">

      <!-- GROUP 01 · CAPITAL MODE -->
      <div class="form-grp">
        <div>
          <div class="grp-title"><span class="num">01</span>CAPITAL MODE</div>
          <div class="grp-desc">how follower capital is allocated against each signal.</div>
        </div>
        <div class="form-rows">
          <div class="form-row">
            <div class="lbl">MODE <span class="req">*</span></div>
            <div class="val full">
              <div class="radio-row full">
                <div class="opt" :class="{ active: form.capital_mode === 'fixed' }" @click="form.capital_mode = 'fixed'">FIXED AMOUNT</div>
                <div class="opt" :class="{ active: form.capital_mode === 'full' }" @click="form.capital_mode = 'full'">FULL-MARGIN MIRROR</div>
                <div class="opt" :class="{ active: form.capital_mode === 'compound' }" @click="form.capital_mode = 'compound'">COMPOUND ROLL</div>
              </div>
            </div>
          </div>
          <div v-if="form.capital_mode === 'fixed'" class="form-row">
            <div class="lbl">FIXED AMOUNT PER ORDER</div>
            <div class="val">
              <span class="inp-grp">
                <input class="inp-term num" type="number" v-model.number="form.fixed_amount" />
                <span class="suffix-term">USDT</span>
              </span>
              <span class="dim">· MIN 50  MAX 10 000</span>
            </div>
          </div>
        </div>
      </div>

      <!-- GROUP 02 · BASIC SETTINGS -->
      <div class="form-grp">
        <div>
          <div class="grp-title"><span class="num">02</span>BASIC SETTINGS</div>
          <div class="grp-desc">multiplier, replication scope, direction limit, open / add triggers.</div>
        </div>
        <div class="form-rows">
          <div class="form-row">
            <div class="lbl">COPY MULTIPLIER</div>
            <div class="val">
              <span class="inp-grp">
                <input class="inp-term num" type="number" step="0.1" v-model.number="form.multiplier" />
                <span class="suffix-term">× LEVERAGE</span>
              </span>
            </div>
          </div>
          <div class="form-row">
            <div class="lbl">START-UP REPLICATION</div>
            <div class="val full">
              <div class="radio-row full">
                <div class="opt" :class="{ active: form.start_mode === 'none' }" @click="form.start_mode = 'none'">NO COPY EXISTING</div>
                <div class="opt" :class="{ active: form.start_mode === 'only_loss' }" @click="form.start_mode = 'only_loss'">COPY UNREALIZED LOSS ONLY</div>
                <div class="opt" :class="{ active: form.start_mode === 'all' }" @click="form.start_mode = 'all'">COPY ALL POSITIONS</div>
              </div>
            </div>
          </div>
          <div class="form-row">
            <div class="lbl">DIRECTION LIMIT</div>
            <div class="val full">
              <div class="radio-row full">
                <div class="opt" :class="{ active: form.direction === 'both' }" @click="form.direction = 'both'">NO LIMIT</div>
                <div class="opt" :class="{ active: form.direction === 'long' }" @click="form.direction = 'long'">LONG ONLY</div>
                <div class="opt" :class="{ active: form.direction === 'short' }" @click="form.direction = 'short'">SHORT ONLY</div>
              </div>
            </div>
          </div>
          <div class="form-row">
            <div class="lbl">OPEN TRIGGER · PRICE</div>
            <div class="val full inline">
              <div class="radio-row half">
                <div class="opt" :class="{ active: form.open_trigger === 'market' }" @click="form.open_trigger = 'market'">MARKET</div>
                <div class="opt" :class="{ active: form.open_trigger === 'avg_price' }" @click="form.open_trigger = 'avg_price'">LIMIT @ AVG</div>
                <div class="opt" :class="{ active: form.open_trigger === 'add_price' }" @click="form.open_trigger = 'add_price'">LIMIT @ LAST-ADD</div>
              </div>
              <span class="dim">·</span>
              <span class="inp-grp">
                <input class="inp-term num" type="number" step="0.01" v-model.number="form.open_price_better_pct" />
                <span class="suffix-term">% BETTER</span>
              </span>
            </div>
          </div>
          <div class="form-row">
            <div class="lbl">ADD-ON TRIGGER · PRICE</div>
            <div class="val full inline">
              <div class="radio-row half">
                <div class="opt" :class="{ active: form.add_trigger === 'market' }" @click="form.add_trigger = 'market'">MARKET</div>
                <div class="opt" :class="{ active: form.add_trigger === 'avg_price' }" @click="form.add_trigger = 'avg_price'">LIMIT @ AVG</div>
                <div class="opt" :class="{ active: form.add_trigger === 'add_price' }" @click="form.add_trigger = 'add_price'">LIMIT @ LAST-ADD</div>
              </div>
              <span class="dim">·</span>
              <span class="inp-grp">
                <input class="inp-term num" type="number" step="0.01" v-model.number="form.add_price_better_pct" />
                <span class="suffix-term">% BETTER</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- GROUP 03 · TP/SL + RISK -->
      <div class="form-grp">
        <div>
          <div class="grp-title"><span class="num">03</span>TAKE-PROFIT / STOP-LOSS</div>
          <div class="grp-desc">per-position and per-job risk envelope.</div>
        </div>
        <div class="form-rows">
          <div class="form-row">
            <div class="lbl">POSITION TAKE-PROFIT</div>
            <div class="val full inline">
              <div class="radio-row half2">
                <div class="opt" :class="{ active: form.tp_mode === 'off' }" @click="form.tp_mode = 'off'">DISABLED</div>
                <div class="opt" :class="{ active: form.tp_mode === 'cycle' }" @click="form.tp_mode = 'cycle'">CYCLIC TRIGGER</div>
              </div>
              <span class="dim">CLOSE</span>
              <span class="inp-grp">
                <input class="inp-term num" type="number" v-model.number="form.tp_close_pct" />
                <span class="suffix-term">% OF QTY</span>
              </span>
            </div>
          </div>
          <div class="form-row">
            <div class="lbl">POSITION STOP-LOSS</div>
            <div class="val full inline">
              <div class="radio-row half2">
                <div class="opt" :class="{ active: form.sl_mode === 'off' }" @click="form.sl_mode = 'off'">DISABLED</div>
                <div class="opt" :class="{ active: form.sl_mode === 'cycle' }" @click="form.sl_mode = 'cycle'">CYCLIC TRIGGER</div>
              </div>
              <span class="dim">CLOSE</span>
              <span class="inp-grp">
                <input class="inp-term num" type="number" v-model.number="form.sl_close_pct" />
                <span class="suffix-term">% OF QTY</span>
              </span>
            </div>
          </div>
          <div class="form-row">
            <div class="lbl">JOB LOSS THRESHOLD · USDT (ABS)</div>
            <div class="val">
              <span class="inp-grp">
                <input class="inp-term num" type="number" v-model.number="form.loss_threshold_usdt" />
                <span class="suffix-term">USDT</span>
              </span>
              <span class="dim">· AUTO-PAUSE WHEN BREACHED</span>
            </div>
          </div>
          <div class="form-row">
            <div class="lbl">SAFETY-CUSHION LOSS · MULT</div>
            <div class="val">
              <span class="inp-grp">
                <input class="inp-term num" type="number" step="0.1" v-model.number="form.safety_floor" />
                <span class="suffix-term">× LEADER MM</span>
              </span>
            </div>
          </div>
          <div class="form-row">
            <div class="lbl">POST-TP REFILL</div>
            <div class="val">
              <label class="chk-term" :class="{ on: form.refill_on_tp }" @click="form.refill_on_tp = !form.refill_on_tp">
                <span class="box">{{ form.refill_on_tp ? '✓' : '' }}</span>
                RE-FILL POSITION WHEN PRICE RETURNS TO AVG
              </label>
              <label class="chk-term" :class="{ on: form.refill_allow_retp }" @click="form.refill_allow_retp = !form.refill_allow_retp">
                <span class="box">{{ form.refill_allow_retp ? '✓' : '' }}</span>
                ALLOW SECOND TP AFTER RE-FILL
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- GROUP 04 · SYMBOL FILTER -->
      <div class="form-grp">
        <div>
          <div class="grp-title"><span class="num">04</span>SYMBOL FILTER</div>
          <div class="grp-desc">leave empty to follow leader fully.</div>
        </div>
        <div class="form-rows">
          <div class="form-row">
            <div class="lbl">BLACKLIST</div>
            <div class="val full">
              <div class="chip-input full">
                <span v-for="s in form.blacklist" :key="'b'+s" class="chip-term">
                  {{ s }}
                  <span class="x" @click="removeChip(form.blacklist, s)">×</span>
                </span>
                <input
                  v-model="blacklistInput"
                  placeholder="+ ADD SYMBOL"
                  @keyup.enter="addBlack"
                  @blur="addBlack"
                />
              </div>
            </div>
          </div>
          <div class="form-row">
            <div class="lbl">WHITELIST</div>
            <div class="val full">
              <div class="chip-input full">
                <span v-for="s in form.whitelist" :key="'w'+s" class="chip-term">
                  {{ s }}
                  <span class="x" @click="removeChip(form.whitelist, s)">×</span>
                </span>
                <input
                  v-model="whitelistInput"
                  placeholder="+ ADD SYMBOL"
                  @keyup.enter="addWhite"
                  @blur="addWhite"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- GROUP 05 · NOTIFICATIONS -->
      <div class="form-grp">
        <div>
          <div class="grp-title"><span class="num">05</span>NOTIFICATIONS</div>
          <div class="grp-desc">delivery channel + event subscriptions.</div>
        </div>
        <div class="form-rows">
          <div class="form-row">
            <div class="lbl">DELIVERY CHANNEL</div>
            <div class="val full">
              <div class="radio-row half">
                <div class="opt" :class="{ active: notifyChannel === 'none' }" @click="notifyChannel = 'none'">SILENT</div>
                <div class="opt" :class="{ active: notifyChannel === 'email' }" @click="notifyChannel = 'email'">EMAIL</div>
                <div class="opt" :class="{ active: notifyChannel === 'telegram' }" @click="notifyChannel = 'telegram'">TELEGRAM BOT</div>
              </div>
            </div>
          </div>
          <div class="form-row">
            <div class="lbl">EVENT SUBSCRIPTIONS</div>
            <div class="val">
              <div class="chk-row">
                <label
                  v-for="ev in [
                    { v: 'order_success', l: 'ORDER FILLED' },
                    { v: 'order_fail', l: 'ORDER REJECTED' },
                    { v: 'risk_trigger', l: 'RISK TRIGGER' },
                    { v: 'tp_sl', l: 'TP / SL HIT' },
                    { v: 'margin_change', l: 'LEADER MARGIN CHG' }
                  ]"
                  :key="ev.v"
                  class="chk-term"
                  :class="{ on: form.notify_types.includes(ev.v) }"
                  @click="toggleArr(form.notify_types, ev.v)"
                >
                  <span class="box">{{ form.notify_types.includes(ev.v) ? '✓' : '' }}</span>
                  {{ ev.l }}
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>

    <template #footer>
      <div class="modal-foot">
        <div class="lhs">CFG_HASH {{ cfgHash }} · DRY-RUN ENABLED · <span class="amber">VALIDATED ✓</span></div>
        <div class="btns">
          <button class="btn-term" @click="open = false">CANCEL</button>
          <button class="btn-term primary" :disabled="submitting" @click="submit">
            <span v-if="submitting">▌ SUBMITTING…</span>
            <span v-else>START COPY →</span>
          </button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
:deep(.cfg-modal) {
  border: 1px solid var(--ct-divider) !important;
  background: rgba(10, 14, 20, 0.96) !important;
  border-radius: 0 !important;
}
:deep(.cfg-modal .el-dialog__header) {
  padding: 0 !important;
  border-bottom: 1px solid var(--ct-divider);
  margin: 0 !important;
}
:deep(.cfg-modal .el-dialog__body) {
  padding: 0 !important;
  max-height: 70vh;
  overflow-y: auto;
}
:deep(.cfg-modal .el-dialog__footer) {
  padding: 0 !important;
  border-top: 1px solid var(--ct-divider);
}

.modal-head {
  height: 38px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: var(--ct-text-2);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-family: var(--ct-font-mono);
}
.modal-head .left,
.modal-head .right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.modal-head .dim { color: var(--ct-text-dim); }
.modal-head .amber { color: var(--ct-amber); }
.modal-head .x {
  font-size: 14px;
  color: var(--ct-text-3);
  cursor: pointer;
  padding-left: 4px;
}
.modal-head .x:hover { color: var(--ct-neg); }

.modal-body { padding: 0; }

.form-grp {
  border-bottom: 1px solid var(--ct-divider);
  padding: 14px 16px;
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 18px;
}
.form-grp:last-child { border-bottom: 0; }
.grp-title {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-family: var(--ct-font-mono);
}
.grp-title .num {
  color: var(--ct-amber);
  margin-right: 6px;
}
.grp-desc {
  font-size: 10px;
  color: var(--ct-text-dim);
  letter-spacing: 0.02em;
  margin-top: 6px;
  text-transform: none;
  line-height: 1.5;
}

.form-rows {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.form-row {
  display: grid;
  grid-template-columns: 1fr;
  gap: 6px;
}
.form-row .lbl {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--ct-font-mono);
}
.form-row .req { color: var(--ct-amber); }
.form-row .val {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.form-row .val.full { width: 100%; }
.form-row .val.inline { flex-wrap: wrap; }
.form-row .dim { color: var(--ct-text-3); font-size: 11px; letter-spacing: 0.04em; }

.radio-row {
  display: flex;
  gap: 0;
  border: 1px solid var(--ct-divider);
  background: var(--ct-bg-2);
}
.radio-row.full { width: 100%; }
.radio-row.half { width: 60%; }
.radio-row.half2 { width: 50%; }
.radio-row .opt {
  flex: 1;
  height: 30px;
  padding: 0 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: var(--ct-text-2);
  border-right: 1px solid var(--ct-divider);
  cursor: pointer;
  letter-spacing: 0.04em;
  font-family: var(--ct-font-mono);
  text-transform: uppercase;
  white-space: nowrap;
  user-select: none;
}
.radio-row .opt:last-child { border-right: 0; }
.radio-row .opt.active {
  background: var(--ct-amber);
  color: #0A0E14;
  font-weight: 600;
}
.radio-row .opt:not(.active):hover {
  background: var(--ct-bg-hover);
  color: var(--ct-text);
}

.inp-grp { display: inline-flex; align-items: center; }
.inp-term {
  height: 30px;
  background: var(--ct-bg-2);
  border: 1px solid var(--ct-divider);
  color: var(--ct-text);
  padding: 0 10px;
  font-size: 13px;
  font-family: var(--ct-font-mono);
  font-variant-numeric: tabular-nums;
  outline: none;
  width: 120px;
}
.inp-term.num { text-align: right; }
.inp-term:focus { border-color: var(--ct-amber); }
.suffix-term {
  height: 30px;
  padding: 0 10px;
  display: inline-flex;
  align-items: center;
  background: var(--ct-bg-3);
  border: 1px solid var(--ct-divider);
  border-left: 0;
  font-size: 11px;
  color: var(--ct-text-3);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  font-family: var(--ct-font-mono);
}

.chip-input {
  min-height: 30px;
  background: var(--ct-bg-2);
  border: 1px solid var(--ct-divider);
  padding: 5px 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.chip-input.full { width: 100%; }
.chip-input input {
  background: transparent;
  border: 0;
  outline: 0;
  color: var(--ct-text);
  font-family: var(--ct-font-mono);
  font-size: 11px;
  min-width: 100px;
  flex: 1;
  letter-spacing: 0.04em;
}
.chip-input input::placeholder {
  color: var(--ct-text-dim);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.chip-term {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--ct-bg-3);
  border: 1px solid var(--ct-divider-strong);
  padding: 2px 8px;
  font-size: 11px;
  color: var(--ct-text-2);
  letter-spacing: 0.04em;
  font-family: var(--ct-font-mono);
}
.chip-term .x {
  color: var(--ct-text-dim);
  cursor: pointer;
  padding-left: 2px;
}
.chip-term .x:hover { color: var(--ct-neg); }

.chk-row {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
}
.chk-term {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  color: var(--ct-text-2);
  cursor: pointer;
  letter-spacing: 0.02em;
  user-select: none;
  font-family: var(--ct-font-mono);
}
.chk-term .box {
  width: 13px;
  height: 13px;
  border: 1px solid var(--ct-text-dim);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--ct-amber);
  font-size: 11px;
  line-height: 1;
}
.chk-term.on .box { border-color: var(--ct-amber); }
.chk-term.on { color: var(--ct-text); }

.modal-foot {
  padding: 14px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.modal-foot .lhs {
  font-size: 10px;
  color: var(--ct-text-dim);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-family: var(--ct-font-mono);
}
.modal-foot .lhs .amber { color: var(--ct-amber); }
.modal-foot .btns { display: flex; gap: 10px; }
.btn-term {
  height: 36px;
  padding: 0 18px;
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-family: var(--ct-font-mono);
  font-weight: 500;
  border: 1px solid var(--ct-divider-strong);
  background: transparent;
  color: var(--ct-text);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
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
</style>
