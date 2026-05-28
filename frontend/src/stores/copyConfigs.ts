import { defineStore } from 'pinia'
import { ref } from 'vue'
import { copyConfigsApi, type CopyConfig } from '@/api/copyConfigs'

export const useCopyConfigsStore = defineStore('copyConfigs', () => {
  const list = ref<CopyConfig[]>([])

  async function load() {
    list.value = (await copyConfigsApi.list()) as CopyConfig[]
  }

  async function create(c: CopyConfig) {
    await copyConfigsApi.create(c)
    list.value.push(c)
  }

  return { list, load, create }
})
