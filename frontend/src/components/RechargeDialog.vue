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
  ElMessage.success('地址已复制')
}
</script>

<template>
  <el-dialog v-model="open" title="充值 USDT" width="460px">
    <div class="chain-tabs">
      <el-radio-group v-model="chain">
        <el-radio-button label="TRC20">USDT-TRC20</el-radio-button>
        <el-radio-button label="ERC20">USDT-ERC20</el-radio-button>
      </el-radio-group>
    </div>

    <div class="qr-block">
      <div class="qr-mock">QR<br />CODE</div>
    </div>

    <div class="addr-row">
      <div class="lbl">充值地址</div>
      <div class="addr-box">
        <span class="mono">{{ currentAddr || '加载中...' }}</span>
        <el-button text type="primary" size="small" @click="copyAddr">复制</el-button>
      </div>
    </div>

    <div class="tip">
      ⚠ 请仔细核对网络，错链转账无法找回。链上确认后约 1 分钟到账。
    </div>

    <template #footer>
      <el-button @click="open = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.chain-tabs { text-align: center; margin-bottom: 16px; }
.qr-block { display: flex; justify-content: center; margin: 18px 0; }
.qr-mock {
  width: 160px; height: 160px;
  background: repeating-conic-gradient(#10B981 0 25%, #fff 0 50%);
  background-size: 18px 18px;
  border-radius: 12px;
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 14px;
  text-align: center;
  border: 2px solid var(--ct-primary);
}
.addr-row { margin-top: 12px; }
.lbl { color: var(--ct-text-3); font-size: 12px; margin-bottom: 6px; }
.addr-box {
  display: flex; align-items: center; gap: 8px;
  background: var(--ct-bg-elev);
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--ct-border);
  word-break: break-all;
  font-size: 12px;
}
.tip {
  margin-top: 14px;
  background: rgba(245, 158, 11, 0.08);
  color: #B45309;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 12px;
}
</style>
