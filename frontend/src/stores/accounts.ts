import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { accountsApi, type ExchangeAccount } from '@/api/accounts'

export const useAccountsStore = defineStore('accounts', () => {
  const list = ref<ExchangeAccount[]>([])
  const currentId = ref<number | null>(null)

  const current = computed(() => list.value.find((a) => a.id === currentId.value) || null)

  async function load() {
    list.value = (await accountsApi.list()) as ExchangeAccount[]
    if (!currentId.value && list.value.length) currentId.value = list.value[0].id
  }

  function select(id: number) {
    currentId.value = id
  }

  return { list, currentId, current, load, select }
})
