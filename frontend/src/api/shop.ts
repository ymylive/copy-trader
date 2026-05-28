import http, { mockOr } from './axios'

export const shopApi = {
  products: () => mockOr(
    () => http.get('/shop/products'),
    () => [
      { id: 'slot_order', name: '下单名额', desc: '为账户增加下单名额', price: 80, periods: ['1m', '3m', '6m', '1y'] },
      { id: 'slot_copy', name: '跟单名额', desc: '增加可跟单交易员数量（初始 2 个）', price: 35, periods: ['perm'] },
      { id: 'trader_role', name: '带单员资格', desc: '允许带单员身份下单', price: 100, periods: ['1m', '3m', '6m', '1y'] },
      { id: 'slot_fast', name: '币安极速跟单', desc: '0.03 秒延迟，仅 Binance', price: 999999, periods: ['contact'] }
    ]
  ),
  claimTrial: (account_id: number, exchange: string, uid: string) => mockOr(
    () => http.post('/shop/trial', { account_id, exchange, uid }),
    () => ({ ok: true })
  ),
  order: (body: { product_id: string; period: string; account_id?: number; coupon?: string }) => mockOr(
    () => http.post('/shop/orders', body),
    () => ({ ok: true, order_id: Date.now() })
  )
}
