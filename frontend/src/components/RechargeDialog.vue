<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { walletApi } from '@/api/wallet'

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: boolean): void }>()

const open = computed({
  get: () => props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v)
})

const chain = ref<'TRC20' | 'ERC20'>('TRC20')
const trcAddr = ref('')
const ercAddr = ref('')

watch(open, async (v) => {
  if (v) {
    const r = (await walletApi.recharge()) as { tron_address: string; erc20_address: string }
    trcAddr.value = r.tron_address
    ercAddr.value = r.erc20_address
  }
})

const currentAddr = computed(() => (chain.value === 'TRC20' ? trcAddr.value : ercAddr.value))

async function copyAddr() {
  await navigator.clipboard.writeText(currentAddr.value)
  ElMessage.success('ADDRESS COPIED')
}
</script>

<template>
  <el-dialog v-model="open" :show-close="false" width="480px" align-center>
    <template #header>
      <div class="dlg-head">
        <span>WALLET // RECHARGE</span>
        <span class="badge amber"><span class="dot"></span>USDT</span>
      </div>
    </template>

    <div class="chain-tabs">
      <button class="chip-btn" :class="{ active: chain === 'TRC20' }" @click="chain = 'TRC20'">USDT · TRC20</button>
      <button class="chip-btn" :class="{ active: chain === 'ERC20' }" @click="chain = 'ERC20'">USDT · ERC20</button>
    </div>

    <div class="qr-block">
      <div class="qr-mock">
        <span>QR</span>
        <span>CODE</span>
      </div>
    </div>

    <div class="addr-row">
      <div class="lbl">DEPOSIT ADDRESS</div>
      <div class="addr-box">
        <span class="addr-text">{{ currentAddr || 'LOADING...' }}</span>
        <button class="copy" @click="copyAddr">COPY</button>
      </div>
    </div>

    <div class="tip">
      ⚠ VERIFY NETWORK BEFORE TRANSFER · WRONG-CHAIN TRANSFERS ARE UNRECOVERABLE · ONCHAIN CONFIRMATION ≈ 60S
    </div>

    <template #footer>
      <button class="btn-term" @click="open = false">CLOSE</button>
    </template>
  </el-dialog>
</template>

<style scoped>
.dlg-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--ct-text);
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.chain-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 18px;
  border: 1px solid var(--ct-divider);
}
.chip-btn {
  flex: 1;
  background: transparent;
  border: 0;
  border-right: 1px solid var(--ct-divider);
  padding: 10px 0;
  font-family: var(--ct-font-mono);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ct-text-2);
  cursor: pointer;
}
.chip-btn:last-child { border-right: 0; }
.chip-btn.active {
  background: var(--ct-amber);
  color: #0A0E14;
  font-weight: 600;
}
.qr-block {
  display: flex;
  justify-content: center;
  margin: 18px 0;
}
.qr-mock {
  width: 160px;
  height: 160px;
  background: repeating-conic-gradient(#FFB400 0 25%, #0A0E14 0 50%);
  background-size: 18px 18px;
  color: #0A0E14;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  letter-spacing: 0.16em;
  border: 1px solid var(--ct-amber);
}
.addr-row { margin-top: 12px; }
.lbl {
  color: var(--ct-text-3);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 6px;
}
.addr-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--ct-bg-2);
  padding: 10px 12px;
  border: 1px solid var(--ct-divider);
  word-break: break-all;
}
.addr-text {
  font-family: var(--ct-font-mono);
  font-size: 11px;
  color: var(--ct-amber);
  flex: 1;
  word-break: break-all;
}
.copy {
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
.copy:hover { color: var(--ct-amber); border-color: var(--ct-amber); }
.tip {
  margin-top: 14px;
  border: 1px solid rgba(255, 180, 0, 0.35);
  color: var(--ct-amber);
  background: rgba(255, 180, 0, 0.04);
  padding: 10px 12px;
  font-size: 10px;
  letter-spacing: 0.1em;
  line-height: 1.6;
  text-transform: uppercase;
}
.btn-term {
  border-radius: 0;
  font-family: var(--ct-font-mono);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-size: 12px;
  font-weight: 500;
  padding: 8px 18px;
  border: 1px solid var(--ct-divider-strong);
  background: transparent;
  color: var(--ct-text);
  cursor: pointer;
}
.btn-term:hover { border-color: var(--ct-amber); color: var(--ct-amber); }
</style>
