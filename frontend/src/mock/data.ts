import type { ExchangeAccount } from '@/api/accounts'
import type { Trader } from '@/api/traders'

export function mockUser() {
  return {
    id: 1401,
    username: 'demo_trader',
    nickname: 'Demo',
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

export function mockAccounts(): ExchangeAccount[] {
  return [
    {
      id: 1,
      name: '账户1(标准)',
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
      name: '账户2(标准)',
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
      name: '账户3(标准)',
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
      name: '账户4(标准)',
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

function curve(seed: number): number[] {
  const r: number[] = []
  let v = 100
  for (let i = 0; i < 60; i++) {
    v += Math.sin(i / 4 + seed) * 6 + (seed % 3) * 0.8 + (Math.random() - 0.4) * 4
    r.push(+v.toFixed(2))
  }
  return r
}

export function mockTraders(): Trader[] {
  return [
    {
      id: '4988811260243579393',
      source: 'smart_money',
      exchange: 'binance',
      nickname: '拉哪',
      avatar: '',
      tags: ['聪明钱', '隐藏持仓'],
      enrolled_days: 12,
      total_pnl: 204209.2,
      roi: 29.46,
      scale: 204209.2,
      sharpe: null,
      win_rate: null,
      max_drawdown: null,
      status: 'listed',
      favorited: false,
      curve: curve(1)
    },
    {
      id: 'BTC_STARDUST_001',
      source: 'binance',
      exchange: 'binance',
      nickname: 'BTC 星辰',
      avatar: '',
      tags: ['币安官方'],
      enrolled_days: 412,
      total_pnl: 1_482_318.55,
      roi: 78.9,
      scale: 980_000,
      sharpe: 3.4,
      win_rate: 64.1,
      max_drawdown: 18.7,
      status: 'listed',
      favorited: true,
      curve: curve(2)
    },
    {
      id: 'MAOMAO_DEMON',
      source: 'okx',
      exchange: 'okx',
      nickname: '茂茂大魔王',
      avatar: '',
      tags: ['欧易', '隐藏持仓'],
      enrolled_days: 287,
      total_pnl: 612_443.18,
      roi: 41.2,
      scale: 540_900,
      sharpe: 2.7,
      win_rate: 58.5,
      max_drawdown: 22.4,
      status: 'listed',
      favorited: false,
      curve: curve(3)
    },
    {
      id: 'WINDFIRE_TRADER',
      source: 'bitget',
      exchange: 'bitget',
      nickname: '风火山林Trader',
      avatar: '',
      tags: ['Bitget'],
      enrolled_days: 142,
      total_pnl: 92_184.7,
      roi: 19.4,
      scale: 220_500,
      sharpe: 1.9,
      win_rate: 55.8,
      max_drawdown: 14.1,
      status: 'listed',
      favorited: false,
      curve: curve(4)
    },
    {
      id: 'MAXIMIZE_SR',
      source: 'bicoin',
      exchange: 'binance',
      nickname: 'MaximizeSR（私域）',
      avatar: '',
      tags: ['币Coin', '私域'],
      enrolled_days: 95,
      total_pnl: 51_293.55,
      roi: 27.5,
      scale: 138_400,
      sharpe: 2.1,
      win_rate: 61.0,
      max_drawdown: 19.6,
      status: 'listed',
      favorited: false,
      curve: curve(5)
    },
    {
      id: '0xC0FFEE...8E5E',
      source: 'smart_money',
      exchange: 'evm',
      nickname: 'WhaleHunter_0xC0FFEE',
      avatar: '',
      tags: ['聪明钱', 'EVM'],
      enrolled_days: 38,
      total_pnl: 184_239.4,
      roi: 52.7,
      scale: 510_000,
      sharpe: 2.9,
      win_rate: 58.2,
      max_drawdown: 11.3,
      status: 'listed',
      favorited: true,
      curve: curve(6)
    },
    {
      id: 'HL_VAULT_FLARE',
      source: 'hyperbot',
      exchange: 'hyperliquid',
      nickname: 'HL Vault · Flare',
      avatar: '',
      tags: ['Hyperliquid'],
      enrolled_days: 64,
      total_pnl: 78_115.0,
      roi: 33.1,
      scale: 312_400,
      sharpe: 2.4,
      win_rate: 57.4,
      max_drawdown: 9.8,
      status: 'listed',
      favorited: false,
      curve: curve(7)
    },
    {
      id: 'BINANCE_DEFI_LEAD',
      source: 'binance',
      exchange: 'binance',
      nickname: 'DeFi Leader',
      avatar: '',
      tags: ['币安官方'],
      enrolled_days: 562,
      total_pnl: 894_120.5,
      roi: 38.4,
      scale: 1_100_000,
      sharpe: 3.1,
      win_rate: 60.2,
      max_drawdown: 21.8,
      status: 'invalid',
      favorited: false,
      curve: curve(8)
    }
  ]
}

export function mockPositions(trader_id: string) {
  return [
    {
      id: 1,
      side: 'long',
      symbol: 'BTC-USDT',
      qty: 0.15,
      entry: 93210.4,
      mark: 95128.5,
      liq: 71200.0,
      margin: 1398.16,
      margin_rate: 8.7,
      realized_pnl: 0,
      unrealized_pnl: 287.71,
      pnl_pct: 20.6,
      tp: '-',
      sl: '-',
      trader_id
    },
    {
      id: 2,
      side: 'short',
      symbol: 'ETH-USDT',
      qty: 1.5,
      entry: 3540.2,
      mark: 3502.4,
      liq: 4108.5,
      margin: 530.6,
      margin_rate: 5.3,
      realized_pnl: 0,
      unrealized_pnl: 56.7,
      pnl_pct: 10.7,
      tp: '-',
      sl: '-',
      trader_id
    }
  ]
}

export function mockLoginHistory() {
  return [
    { ip: '203.0.113.42', region: '中国·杭州', time: '2026-05-28 09:12:31' },
    { ip: '198.51.100.7', region: '美国·纽约', time: '2026-05-25 22:01:08' },
    { ip: '203.0.113.42', region: '中国·杭州', time: '2026-05-21 18:23:11' }
  ]
}
