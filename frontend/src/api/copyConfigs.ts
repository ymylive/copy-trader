import http, { mockOr } from './axios'

export type CapitalMode = 'fixed' | 'full' | 'compound'
export type StartMode = 'none' | 'only_loss' | 'all'
export type DirectionFilter = 'both' | 'long' | 'short'
export type TriggerMode = 'market' | 'avg_price' | 'add_price'
export type StopMode = 'off' | 'cycle'

export interface CopyConfig {
  account_id: number
  trader_id: string
  reverse: boolean
  capital_mode: CapitalMode
  fixed_amount?: number
  multiplier: number
  start_mode: StartMode
  direction: DirectionFilter
  open_trigger: TriggerMode
  open_price_better_pct: number
  add_trigger: TriggerMode
  add_price_better_pct: number
  tp_mode: StopMode
  tp_close_pct: number
  sl_mode: StopMode
  sl_close_pct: number
  loss_threshold_usdt: number
  safety_floor: number
  refill_on_tp: boolean
  refill_allow_retp: boolean
  blacklist: string[]
  whitelist: string[]
  notify_channels: string[]
  notify_types: string[]
}

export const copyConfigsApi = {
  list: () => mockOr(
    () => http.get<CopyConfig[]>('/copy-configs'),
    () => []
  ),
  create: (body: CopyConfig) => mockOr(
    () => http.post('/copy-configs', body),
    () => ({ ok: true, id: Date.now() })
  ),
  update: (id: number, body: Partial<CopyConfig>) => mockOr(
    () => http.patch(`/copy-configs/${id}`, body),
    () => ({ ok: true })
  ),
  stop: (id: number) => mockOr(
    () => http.post(`/copy-configs/${id}/stop`),
    () => ({ ok: true })
  )
}
