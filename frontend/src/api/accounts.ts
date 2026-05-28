import http, { mockOr } from './axios'
import { mockAccounts } from '@/mock/data'

export interface PnlPoint { date: string; value: number }

export interface ExchangeAccount {
  id: number
  name: string
  type: 'standard' | 'fast'
  active: boolean
  exchange: 'binance' | 'okx' | 'gate' | 'bitget' | 'hyperliquid'
  uid: string
  invited: boolean
  api_key: string
  secret_key: string
  egress_ips: string[]
  futures_balance: number
  total_assets: number
}

export const accountsApi = {
  list: (): Promise<ExchangeAccount[]> => mockOr(
    () => http.get<ExchangeAccount[]>('/accounts'),
    () => mockAccounts()
  ),
  update: (id: number, body: Partial<ExchangeAccount>) => mockOr(
    () => http.patch<{ ok: boolean }>(`/accounts/${id}`, body),
    () => ({ ok: true })
  ),
  remove: (id: number) => mockOr(
    () => http.delete<{ ok: boolean }>(`/accounts/${id}`),
    () => ({ ok: true })
  ),
  setLeverage: (id: number, symbol: string, leverage: number) => mockOr(
    () => http.post<{ ok: boolean }>(`/accounts/${id}/leverage`, { symbol, leverage }),
    () => ({ ok: true })
  ),
  pnlSeries: (id: number): Promise<PnlPoint[]> => mockOr(
    () => http.get<PnlPoint[]>(`/accounts/${id}/pnl-series`),
    () => Array.from({ length: 30 }, (_, i) => ({
      date: `2026-04-${28 + Math.floor(i / 30 * 30)}`,
      value: 100 + i * 35 + Math.random() * 50
    }))
  )
}
