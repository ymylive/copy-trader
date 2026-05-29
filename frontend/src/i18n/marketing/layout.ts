/* ───────────────────────────────────────────────────────────────
   marketing.layout.*  ——  MarketingLayout 自身的 nav / footer / 语言切换
   foundation 阶段完整填好 zh-CN + en 两套文案。
   翻译纪律：交易所名 / 版本号 / 数字保持原样(数据)，只译 label / 文案。
   ─────────────────────────────────────────────────────────────── */
export default {
  'zh-CN': {
    nav: {
      features: '功能',
      traders: '交易员',
      pricing: '定价',
      docs: '文档',
      console: '控制台',
      login: '登录',
      cta: '开启 7 天试用',
    },
    lang: {
      label: '语言',
      zh: '中文',
      en: 'EN',
    },
    footer: {
      status: {
        operational: '系统全部正常运行',
        operationalSuffix: '执行层 v4',
        latency: '执行延迟',
        latencyUnit: 'p50',
        subscribers: 'WS 订阅者',
        subscribersUnit: '实时在线',
      },
      product: {
        title: '产品',
        features: '功能',
        leaderboard: '排行榜',
        pricing: '定价',
        console: '控制台',
      },
      resources: {
        title: '资源',
        documentation: '文档',
        api: 'API 参考',
        status: '系统状态',
        changelog: '更新日志',
      },
      exchanges: {
        title: '交易所',
      },
      risk: {
        label: '风险提示。',
        body: '加密衍生品蕴含重大风险，并非适合所有投资者。杠杆会同时放大盈利与亏损，您的损失可能超出初始保证金。任何交易员的历史业绩——包括页面所示数据——都不构成对未来收益的保证。Copy Trader 仅提供执行基础设施，不构成投资建议。请量力而行。',
      },
      copyright: '© 2026 Copy Trader · 执行层',
    },
  },
  en: {
    nav: {
      features: 'Features',
      traders: 'Traders',
      pricing: 'Pricing',
      docs: 'Docs',
      console: 'Console',
      login: 'Login',
      cta: 'Start 7-Day Trial',
    },
    lang: {
      label: 'Language',
      zh: '中文',
      en: 'EN',
    },
    footer: {
      status: {
        operational: 'All systems operational',
        operationalSuffix: 'exec layer v4',
        latency: 'Execution latency',
        latencyUnit: 'p50',
        subscribers: 'WS subscribers',
        subscribersUnit: 'live',
      },
      product: {
        title: 'Product',
        features: 'Features',
        leaderboard: 'Leaderboard',
        pricing: 'Pricing',
        console: 'Console',
      },
      resources: {
        title: 'Resources',
        documentation: 'Documentation',
        api: 'API reference',
        status: 'System status',
        changelog: 'Changelog',
      },
      exchanges: {
        title: 'Exchanges',
      },
      risk: {
        label: 'Risk disclosure.',
        body: 'Crypto derivatives carry substantial risk and are not suitable for every investor. Leverage amplifies both gains and losses; you may lose more than your initial margin. Past performance of any leader — including figures shown — does not guarantee future results. Copy Trader provides execution infrastructure only and is not investment advice. Trade within your means.',
      },
      copyright: '© 2026 Copy Trader · Execution Layer',
    },
  },
}
