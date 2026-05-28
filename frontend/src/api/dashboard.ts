import http, { mockOr } from './axios'

/**
 * All mock values pulled from /design/brand-spec.md.
 */
export const dashboardApi = {
  overview: () => mockOr(
    () => http.get('/dashboard/overview'),
    () => ({
      total_assets: 32771.35,
      account_count: 4,
      active_count: 3,
      paused_count: 1,
      err_count: 0,
      cumulative_pnl: 269066.53,
      cumulative_pct: 820.65,
      today_pnl: 0,
      today_orders: 12,
      today_open: 0,
      since: '2024-08-12'
    })
  ),
  pnlSeries: () => mockOr(
    () => http.get('/dashboard/pnl-series'),
    () => {
      const base = new Date('2026-03-29T00:00:00Z').getTime()
      const arr = []
      let v = 3500
      for (let i = 0; i < 60; i++) {
        v += v * ((Math.sin(i / 4) * 0.04) + ((i % 5 === 0 ? 0.012 : -0.002)))
        const d = new Date(base + i * 86400000)
        arr.push({
          date: `${String(d.getUTCMonth() + 1).padStart(2, '0')}-${String(d.getUTCDate()).padStart(2, '0')}`,
          value: +v.toFixed(2)
        })
      }
      return arr
    }
  ),
  news: () => mockOr(
    () => http.get('/dashboard/news'),
    () => [
      { id: 1, time: '2026-05-28 10:32:14 UTC', src: 'CME', tone: 'neutral', body: 'Bitcoin futures basis narrows to 4.2% as institutional demand cools; CME large traders trim long exposure 1.8B notional.', pct: -1.97 },
      { id: 2, time: '2026-05-28 10:28:55 UTC', src: 'LIQUIDATE', tone: 'red', body: 'Hyperliquid · whale wallet 0x4af...e21 liquidated $42.8M ETH-PERP long at 2 404.18 · cascade triggered 19 sub-orders.', pct: -3.41 },
      { id: 3, time: '2026-05-28 10:21:03 UTC', src: 'SEC', tone: 'green', body: 'SEC commissioner signals openness to spot-ETH staking ETF amendment; comment window closes 06-14.', pct: 0.84 },
      { id: 4, time: '2026-05-28 10:14:47 UTC', src: 'COINGLASS', tone: 'neutral', body: 'Aggregate perp open interest reaches $76.67B, +4.1% w/w; BTC dominance of OI back to 58.3%.', pct: 4.10 },
      { id: 5, time: '2026-05-28 09:58:12 UTC', src: 'FED', tone: 'neutral', body: 'Fed minutes show divided committee on QT taper pace · September dot-plot revision expected · USD index +0.31%.', pct: 0.31 },
      { id: 6, time: '2026-05-28 09:42:30 UTC', src: 'EXPLOIT', tone: 'red', body: 'Cross-chain bridge "Stargate-v3" suspends withdrawals after 3 800 ETH suspicious outflow · team investigating.', pct: -12.40 },
      { id: 7, time: '2026-05-28 09:30:00 UTC', src: 'MACRO', tone: 'green', body: 'US Q1 GDP final +1.4% vs consensus +1.2% · core PCE 3.7% · DXY rallies 0.4%.', pct: 0.40 }
    ]
  ),
  marketWidgets: () => mockOr(
    () => http.get('/dashboard/market-widgets'),
    () => ({
      btc_price: { value: 74180, change_24h: -1.97, change_usd: -1489, src: 'BINANCE' },
      fear_greed: { value: 22, label: 'EXTREME FEAR', prev: 31 },
      liquidation_24h: { total: 289, last_1h: 3.65, long_pct: 71, short_pct: 29 },
      open_interest: { binance: 75.05, bitmex: 1.62, okx: 0, total: 76.67 },
      premium_quarter: { okx: 795, binance: 203, ann_pct: 1.07 },
      long_short_ratio: { value: 1.69, long_pct: 62.8, short_pct: 37.2 },
      funding_rate: { value: 0.010, ann_apr: 10.95 },
      usdt_premium: { otc_cny: 6.780, change_pct: 0.01, flow_1h: 8.4 }
    })
  ),
  execFeed: () => mockOr(
    () => http.get('/dashboard/exec-feed'),
    () => [
      { ts: '10:32:56.412', kind: 'FILL',   body: 'BTC-USDT-SWAP', meta: 'LONG  0.025  ENTRY 74 180.50  px@mkt' },
      { ts: '10:32:56.218', kind: 'SIGNAL', body: 'okx:79346',     meta: 'open  short  ETH-USDT-SWAP  3.20x' },
      { ts: '10:32:55.901', kind: 'SUBSCR', body: 'hyperliquid:0xab...c3', meta: 'positions  ws://...' },
      { ts: '10:32:55.704', kind: 'FILL',   body: 'SOL-USDT-SWAP', meta: 'LONG  12.4   ENTRY 158.42   px@mkt' },
      { ts: '10:32:55.501', kind: 'SIGNAL', body: 'binance:369319', meta: 'add  long  BTC-USDT-SWAP  +0.5x' },
      { ts: '10:32:55.319', kind: 'WARN',   body: 'okx:1030294',    meta: 'slippage 0.08% < tol 0.15%' },
      { ts: '10:32:55.102', kind: 'FILL',   body: 'ETH-USDT-SWAP', meta: 'CLOSE SHORT  1.50  EXIT  2 412.10  pnl +$42.18' },
      { ts: '10:32:54.918', kind: 'SUBSCR', body: 'binance:smart-money', meta: 'top-50 wallets' },
      { ts: '10:32:54.711', kind: 'SIGNAL', body: 'okx:951891',     meta: 'reduce  long  SOL-USDT-SWAP  -0.30x' },
      { ts: '10:32:54.502', kind: 'FILL',   body: 'DOGE-USDT-SWAP', meta: 'SHORT  2840  ENTRY 0.142 09  px-better 0.04%' },
      { ts: '10:32:54.317', kind: 'REJECT', body: 'bitmex:XBTUSD',  meta: 'insufficient margin · skipped' },
      { ts: '10:32:54.118', kind: 'SUBSCR', body: 'redis://signal-bus', meta: '3187 ops/s · OK' }
    ] as Array<{ ts: string; kind: 'FILL' | 'SIGNAL' | 'SUBSCR' | 'WARN' | 'REJECT'; body: string; meta: string }>
  )
}
