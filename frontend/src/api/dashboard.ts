import http, { mockOr } from './axios'

export const dashboardApi = {
  overview: () => mockOr(
    () => http.get('/dashboard/overview'),
    () => ({
      total_assets: 82771.36,
      account_count: 1,
      cumulative_pnl: 209906.53,
      today_pnl: 0
    })
  ),
  pnlSeries: () => mockOr(
    () => http.get('/dashboard/pnl-series'),
    () => Array.from({ length: 60 }, (_, i) => ({
      date: `2026-04-${String((i % 30) + 1).padStart(2, '0')}`,
      value: 1000 + i * 60 + Math.sin(i / 3) * 200
    }))
  ),
  news: () => mockOr(
    () => http.get('/dashboard/news'),
    () => [
      { id: 1, time: '12:32', title: '美联储官员表态：考虑年内再降息一次', source: 'NS3' },
      { id: 2, time: '12:18', title: 'BTC ETF 周净流入 +5.4 亿美元', source: 'NS3' },
      { id: 3, time: '11:57', title: '链上数据：聪明钱钱包过去 24h 净买入 ETH 18,000 枚', source: 'On-chain' },
      { id: 4, time: '10:40', title: 'OKX 平台资金费率均值小幅回升至 +0.0098%', source: 'OKX' },
      { id: 5, time: '09:15', title: 'Hyperliquid Vault 24h TVL 增 +12%', source: 'HL' }
    ]
  ),
  marketWidgets: () => mockOr(
    () => http.get('/dashboard/market-widgets'),
    () => ({
      btc_price: { value: 95128.42, change_24h: 1.23 },
      fear_greed: { value: 64, label: '贪婪' },
      liquidation_24h: 412.7,
      liquidation_1h: 17.3,
      open_interest: { okx: 18.4, binance: 32.1, bitmex: 7.6 },
      premium_quarter: { okx: 1.34, binance: 1.18 },
      long_short_ratio: 1.42,
      funding_rate: 0.0098,
      usdt_netflow: 142.5,
      usdt_premium: 0.12,
      retail_long_short: { long_pct: 56.7, short_pct: 43.3 },
      weibo_sentiment: { long: 61, short: 39 },
      global_long_short: { long: 53.2, short: 46.8 }
    })
  )
}
