import { ref, onMounted, type Ref } from 'vue'
import { tradersApi, type Trader } from '@/api/traders'
import { mockTraders } from '@/mock/data'

/**
 * Shared data source for the PUBLIC marketing site (no auth, backend often down).
 *
 * Graceful degradation is the iron law:
 *  - initial value is ALWAYS mockTraders() → first paint / SSR / screenshots
 *    are never empty (no blank leaderboard, ever);
 *  - on mount we attempt to fetch the LIVE list via tradersApi.list;
 *  - success AND non-empty → replace with live data;
 *  - failure / exception / empty → silently keep the mock (no throw, no toast).
 *
 * The fetch is marked `silent` so the axios response interceptor skips its
 * ElMessage.error — a public visitor must never see a "请求失败" popup.
 *
 * Do NOT import mockTraders() directly in pages; consume this composable and
 * derive whatever subset you need with computed().
 */
export function usePublicTraders(
  params?: Parameters<typeof tradersApi.list>[0]
): { traders: Ref<Trader[]>; loading: Ref<boolean> } {
  // Seed with mock so the榜 is never empty on first render / SSR / screenshot.
  const traders = ref<Trader[]>(mockTraders())
  const loading = ref(false)

  onMounted(async () => {
    loading.value = true
    try {
      const live = await tradersApi.list(params, { silent: true })
      // Only adopt live data when it actually has rows; otherwise keep mock.
      if (Array.isArray(live) && live.length > 0) {
        traders.value = live
      }
    } catch {
      // Silent fallback — retain the mock seed. Never throw, never toast.
    } finally {
      loading.value = false
    }
  })

  return { traders, loading }
}
