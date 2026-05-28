import { defineStore } from 'pinia'
import { ref } from 'vue'
import { tradersApi, type Trader, type SignalSource } from '@/api/traders'

export const useTradersStore = defineStore('traders', () => {
  const list = ref<Trader[]>([])
  const loading = ref(false)
  const source = ref<SignalSource | null>(null)
  const q = ref('')
  const favoriteOnly = ref(false)

  async function load() {
    loading.value = true
    try {
      list.value = (await tradersApi.list({
        source: source.value || undefined,
        favorite_only: favoriteOnly.value || undefined,
        q: q.value || undefined
      })) as Trader[]
    } finally {
      loading.value = false
    }
  }

  async function toggleFav(t: Trader) {
    t.favorited = !t.favorited
    await tradersApi.favorite(t.id, !!t.favorited)
  }

  return { list, loading, source, q, favoriteOnly, load, toggleFav }
})
