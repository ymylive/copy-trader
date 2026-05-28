import type { ExchangeAccount } from '@/api/accounts'
import type { Trader } from '@/api/traders'

/* =================================================================
   REAL DATA — sourced from /design/brand-spec.md
   Do not use lorem ipsum.
   ================================================================= */

export function mockUser() {
  return {
    id: 52494073,
    username: 'maietry',
    nickname: 'Maietry',
    email: 'demo@example.com',
    avatar: '',
    svip: true,
    points: 0
  }
}

export function mockLoginResp() {
  return {
    token: 'mock-jwt-' + Math.random().toString(36).slice(2),
    user: mockUser()
  }
}

/* ── 4 accounts — totals from brand-spec ─────────────────────────── */
export function mockAccounts(): ExchangeAccount[] {
  return [
    {
      id: 1,
      name: 'ACCOUNT_01 BINANCE',
      type: 'standard',
      active: true,
      exchange: 'binance',
      uid: '38219470',
      invited: false,
      api_key: '8d72•••••••••••••••••••••2c4f',
      secret_key: '7a91•••••••••••••••••••••e3b1',
      egress_ips: ['8.211.140.223', '43.153.149.108', '101.36.104.169', '47.245.8.141'],
      futures_balance: 12503.18,
      total_assets: 12871.91
    },
    {
      id: 2,
      name: 'ACCOUNT_02 OKX',
      type: 'standard',
      active: true,
      exchange: 'okx',
      uid: '18293021',
      invited: true,
      api_key: '3f01•••••••••••••••••••••cd11',
      secret_key: '7211•••••••••••••••••••••bb40',
      egress_ips: ['8.211.140.223', '43.153.149.108', '101.36.104.169', '47.245.8.141'],
      futures_balance: 8421.55,
      total_assets: 8503.27
    },
    {
      id: 3,
      name: 'ACCOUNT_03 BITGET',
      type: 'standard',
      active: false,
      exchange: 'bitget',
      uid: '52183741',
      invited: false,
      api_key: '——',
      secret_key: '——',
      egress_ips: ['8.211.140.223', '43.153.149.108', '101.36.104.169', '47.245.8.141'],
      futures_balance: 0,
      total_assets: 0
    },
    {
      id: 4,
      name: 'ACCOUNT_04 GATE',
      type: 'standard',
      active: true,
      exchange: 'gate',
      uid: '52494073',
      invited: true,
      api_key: '0045•••••••••••••••••••••berf7',
      secret_key: '979c•••••••••••••••••••••5d5fb',
      egress_ips: ['8.211.140.223', '43.153.149.108', '101.36.104.169', '47.245.8.141'],
      futures_balance: 30518.43,
      total_assets: 32771.79
    }
  ]
}

/* Deterministic equity curve for traders */
function curve(seed: number, n = 40, base = 1000, vol = 0.04): number[] {
  const r: number[] = []
  let v = base
  const s = (Math.sin(seed) + 1) / 2
  for (let i = 0; i < n; i++) {
    v += v * (Math.cos(i * 0.18 + seed) * vol * 0.7 + (s - 0.5) * vol * 0.3)
    r.push(+v.toFixed(2))
  }
  return r
}

/* ── 8 traders — exact data from brand-spec ─────────────────────── */
export function mockTraders(): Trader[] {
  return [
    {
      id: '79346',
      source: 'bicoin',
      exchange: 'okx',
      nickname: '茂茂大魔王',
      avatar: '',
      tags: ['OKX', 'BICOIN'],
      enrolled_days: 2209,
      total_pnl: 1343829.94,
      roi: 14539.61,
      scale: 7618.91,
      sharpe: null,
      win_rate: 34.40,
      max_drawdown: 2.57,
      status: 'listed',
      favorited: false,
      curve: curve(1)
    },
    {
      id: '369319',
      source: 'bicoin',
      exchange: 'binance',
      nickname: '风火山林Trader',
      avatar: '',
      tags: ['BINANCE', 'BICOIN'],
      enrolled_days: 1705,
      total_pnl: 1927532.79,
      roi: 6880.06,
      scale: 89999.16,
      sharpe: null,
      win_rate: 45.45,
      max_drawdown: 6.86,
      status: 'listed',
      favorited: false,
      curve: curve(2, 40, 1000, 0.045)
    },
    {
      id: '1030294',
      source: 'bicoin',
      exchange: 'okx',
      nickname: '牛的青山在',
      avatar: '',
      tags: ['OKX', 'BICOIN'],
      enrolled_days: 899,
      total_pnl: 297089.72,
      roi: 10326.49,
      scale: 13292.43,
      sharpe: null,
      win_rate: 75.00,
      max_drawdown: 1.15,
      status: 'listed',
      favorited: true,
      curve: curve(3, 40, 1000, 0.03)
    },
    {
      id: '951891',
      source: 'bicoin',
      exchange: 'okx',
      nickname: '寒星日照',
      avatar: '',
      tags: ['OKX', 'BICOIN'],
      enrolled_days: 1218,
      total_pnl: 408565.96,
      roi: 343.37,
      scale: 138001.32,
      sharpe: null,
      win_rate: 43.33,
      max_drawdown: 14.51,
      status: 'listed',
      favorited: false,
      curve: curve(4, 40, 1000, 0.038)
    },
    {
      id: '4120066087544364033',
      source: 'binance',
      exchange: 'binance',
      nickname: 'MaximizeSR',
      avatar: '',
      tags: ['BINANCE', 'HIDDEN'],
      enrolled_days: 653,
      total_pnl: -319.96,
      roi: -6.03,
      scale: 46358.66,
      sharpe: 0.06,
      win_rate: 51.29,
      max_drawdown: 9.15,
      status: 'listed',
      favorited: false,
      curve: curve(5, 40, 1000, 0.025)
    },
    {
      id: '3779422221599733504',
      source: 'binance',
      exchange: 'binance',
      nickname: 'KNOTMAIN',
      avatar: '',
      tags: ['BINANCE', 'LEAD', 'HIDDEN'],
      enrolled_days: 0,
      total_pnl: 365404.77,
      roi: 53.51,
      scale: NaN,
      sharpe: 3.20,
      win_rate: 57.83,
      max_drawdown: 13.32,
      status: 'listed',
      favorited: true,
      curve: curve(6, 40, 1000, 0.035)
    },
    {
      id: '4030560779244867073',
      source: 'binance',
      exchange: 'binance',
      nickname: '穩定暴擊 Crit',
      avatar: '',
      tags: ['BINANCE', 'HIDDEN'],
      enrolled_days: 715,
      total_pnl: -102513.70,
      roi: -57.91,
      scale: 69091.23,
      sharpe: -0.05,
      win_rate: 32.76,
      max_drawdown: 69.91,
      status: 'invalid',
      favorited: false,
      curve: curve(7, 40, 1000, 0.06)
    },
    {
      id: '3904393221729556225',
      source: 'binance',
      exchange: 'binance',
      nickname: 'Melanya',
      avatar: '',
      tags: ['BINANCE', 'HIDDEN'],
      enrolled_days: 802,
      total_pnl: 0.00,
      roi: 0.00,
      scale: 10177.62,
      sharpe: -0.13,
      win_rate: 0.00,
      max_drawdown: 0.00,
      status: 'listed',
      favorited: false,
      curve: curve(8, 40, 1000, 0.001)
    }
  ]
}

export function mockPositions(trader_id: string) {
  return [
    {
      id: 1,
      side: 'long' as const,
      symbol: 'BTC-USDT-SWAP',
      qty: 0.15,
      entry: 74180.50,
      mark: 75128.40,
      liq: 71200.00,
      margin: 1398.16,
      margin_rate: 8.7,
      realized_pnl: 0,
      unrealized_pnl: 142.18,
      pnl_pct: 10.16,
      tp: '—',
      sl: '—',
      trader_id
    },
    {
      id: 2,
      side: 'short' as const,
      symbol: 'ETH-USDT-SWAP',
      qty: 1.5,
      entry: 2540.20,
      mark: 2412.10,
      liq: 4108.50,
      margin: 530.60,
      margin_rate: 5.3,
      realized_pnl: 42.18,
      unrealized_pnl: 192.15,
      pnl_pct: 36.21,
      tp: '—',
      sl: '—',
      trader_id
    },
    {
      id: 3,
      side: 'long' as const,
      symbol: 'SOL-USDT-SWAP',
      qty: 12.4,
      entry: 158.42,
      mark: 159.10,
      liq: 142.18,
      margin: 196.44,
      margin_rate: 4.2,
      realized_pnl: 0,
      unrealized_pnl: 8.43,
      pnl_pct: 4.29,
      tp: '—',
      sl: '—',
      trader_id
    }
  ]
}

export function mockLoginHistory() {
  return [
    { ip: '43.153.149.108', region: 'HK · BGP', time: '2026-05-28 09:12:31 UTC' },
    { ip: '8.211.140.223', region: 'SG · AWS', time: '2026-05-25 22:01:08 UTC' },
    { ip: '101.36.104.169', region: 'JP · Tokyo', time: '2026-05-21 18:23:11 UTC' },
    { ip: '47.245.8.141', region: 'US · LA', time: '2026-05-18 04:48:33 UTC' }
  ]
}
