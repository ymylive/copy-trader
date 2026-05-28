import http, { mockOr } from './axios'
import { mockTraders } from '@/mock/data'

export type SignalSource = 'binance' | 'okx' | 'bitget' | 'bicoin' | 'smart_money' | 'hyperbot'

export interface Trader {
  id: string
  source: SignalSource
  exchange: 'binance' | 'okx' | 'bitget' | 'hyperliquid' | 'evm'
  nickname: string
  avatar: string
  tags: string[]
  enrolled_days: number
  total_pnl: number
  roi: number
  scale: number
  sharpe: number | null
  win_rate: number | null
  max_drawdown: number | null
  status: 'listed' | 'invalid'
  favorited?: boolean
  curve?: number[]
}

export const tradersApi = {
  list: (params?: { source?: SignalSource; favorite_only?: boolean; q?: string }) => mockOr(
    () => http.get<Trader[]>('/traders', { params }),
    () => {
      let list = mockTraders()
      if (params?.source) list = list.filter((t) => t.source === params.source)
      if (params?.favorite_only) list = list.filter((t) => t.favorited)
      if (params?.q) {
        const q = params.q.toLowerCase()
        list = list.filter((t) => t.nickname.toLowerCase().includes(q) || t.id.includes(q))
      }
      return list
    }
  ),
  favorite: (id: string, fav: boolean) => mockOr(
    () => http.post(`/traders/${id}/favorite`, { fav }),
    () => ({ ok: true })
  ),
  detail: (id: string) => mockOr(
    () => http.get<Trader>(`/traders/${id}`),
    () => mockTraders().find((t) => t.id === id)!
  )
}
