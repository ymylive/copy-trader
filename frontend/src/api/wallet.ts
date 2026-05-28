import http, { mockOr } from './axios'

export const walletApi = {
  balance: () => mockOr(
    () => http.get('/wallet'),
    () => ({ balance: 128.55, withdrawn: 0 })
  ),
  resources: () => mockOr(
    () => http.get('/wallet/resources'),
    () => [
      { id: 1, product: '下单名额', bought_at: '2026-04-10', renew_at: '2026-05-10', expire_at: '2026-06-10', auto_renew: true },
      { id: 2, product: '跟单名额', bought_at: '2026-03-01', renew_at: '-', expire_at: '永久', auto_renew: false }
    ]
  ),
  txns: () => mockOr(
    () => http.get('/wallet/transactions'),
    () => [
      { id: 1, type: '充值', date: '2026-05-25', amount: 200, source: 'TRC20' },
      { id: 2, type: '消费', date: '2026-05-10', amount: -80, source: '下单名额（账户1）' }
    ]
  ),
  withdraw: (body: { amount: number; address: string }) => mockOr(
    () => http.post('/wallet/withdraw', body),
    () => ({ ok: true })
  ),
  recharge: () => mockOr(
    () => http.post('/wallet/recharge'),
    () => ({ tron_address: 'TXa...mockTRC20...QzE', erc20_address: '0xab...mockERC20...88' })
  ),
  withdrawAddresses: () => mockOr(
    () => http.get('/wallet/addresses'),
    () => [{ id: 1, chain: 'TRC20', address: 'TXa1xZmockaddress2025' }]
  )
}
