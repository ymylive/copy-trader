import { defineStore } from 'pinia'
import { ref } from 'vue'
import { walletApi } from '@/api/wallet'

export const useWalletStore = defineStore('wallet', () => {
  const balance = ref(0)
  const withdrawn = ref(0)
  const resources = ref<any[]>([])
  const txns = ref<any[]>([])

  async function load() {
    const w = (await walletApi.balance()) as { balance: number; withdrawn: number }
    balance.value = w.balance
    withdrawn.value = w.withdrawn
    resources.value = (await walletApi.resources()) as any[]
    txns.value = (await walletApi.txns()) as any[]
  }

  return { balance, withdrawn, resources, txns, load }
})
