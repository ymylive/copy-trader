/* ───────────────────────────────────────────────────────────────
   marketing.pricing.*  ——  Pricing 页文案（中英双语）
   翻译纪律：交易员名(茂茂大魔王/MaximizeSR)、交易所名、价格/数字/币种
   保持原样(它们是数据)；只译 label / 文案 / 标题 / CTA。
   中文为地道营销文案，非字面直译，保留 accent 强调与编辑节奏。
   ─────────────────────────────────────────────────────────────── */
export default {
  'zh-CN': {
    head: {
      idx: '04 / 定价',
      titleLine1: '只租轨道，',
      titleLine2: '利润全留。',
      // right paragraph，拆成三段以保留模板内联 <span class="ink"> 强调
      rightLead: '一笔固定月费，按月结算。每一档都是零业绩分成——',
      rightInk: '14 539% 的丰年，和持平的一年，缴一样的固定租金',
      rightTail: '。邀请同行可享 10% 返佣，对方半价入场。月付制，绝不锁仓。',
    },
    plans: {
      trial: {
        name: '试用',
        note: '7 天全功能，无需绑卡。',
      },
      pro: {
        name: 'Pro · 推荐',
        per: '/月',
        note: '为多账户活跃交易者打造。',
      },
      inst: {
        name: '机构版',
        price: '定制',
        note: '面向交易团队、基金与领单交易员。',
      },
    },
    matrix: {
      // 能力行 label
      accounts: { label: '账户数', trial: '1 个账户', pro: '4 个账户', inst: '不限' },
      slots: { label: '跟单席位', trial: '1 个席位', pro: '多个席位', inst: '不限' },
      speed: { label: '执行速度', trial: '标准', pro: '优先 < 2 ms', inst: '优先 RPC' },
      egress: { label: '专属出口 IP', trial: '—', pro: '已含', inst: '每账户独立' },
      sources: { label: '信号源', trial: '核心源', pro: '全部 6 个信号源', inst: '全部 6 个信号源' },
      leadSeat: { label: '领单席位', trial: '—', pro: '—', inst: '可申请' },
      selfHost: { label: '私有部署 + 专属风控', trial: '—', pro: '—', inst: '已含' },
      riskEngine: { label: '风控引擎', trial: '盘前拦截', pro: '盘前拦截', inst: '账户级规则' },
      sla: { label: 'SLA', trial: '尽力而为', pro: '99.9% 可用性', inst: '定制 SLA' },
      fee: { label: '业绩分成', trial: '0%', pro: '0%', inst: '0%' },
    },
    cta: {
      trial: '免费开始',
      pro: '开启 Pro 试用',
      inst: '联系我们',
    },
    strip: {
      zeroFee: '全档零业绩分成——利润留在你自己的钱包里。',
      rebate: '每邀请一位同行，终身享 10% 返佣。',
      half: '受邀同行半价入场。',
    },
    value: {
      // 引语拆段以保留内联 accent / 引号标记
      quoteLead: '我们收的是基础设施的租金，而非对你 alpha 征的税。一旦某个跟单平台开始分走你的上行，它就成了你',
      quoteAccent: '沉默的合伙人',
      quoteTail: '——而我们拒绝当这样的角色。',
      cite: 'Copy Trader — 运营原则 №3',
      // 收益卡 label（交易员名/交易所名保持硬编码）
      cardRoiUsdt: 'ROI · USDT',
      cardDaysLive: '天实盘', // 前缀数字硬编码，label 在数字之后
      cardIllustrative: '示意图',
      footHeadlineRoi: '主页 ROI',
      footFee: '业绩分成',
      footKeep: '你拿到',
      // 诚实负样本披露，拆段保留内联 m-neg / ink 强调
      honestLead: '并非每个交易员都在赚钱。我们诚实列出亏损的领单者——例如',
      honestSample: '保持可见、供研究复盘，绝不从排行榜上隐藏。上方曲线仅为',
      honestInk: '示意',
      honestTail: '，不构成对未来收益的承诺。',
    },
    faq: {
      idx: '05 / 常见问题',
      titleLine1: '交易团队',
      titleLine2: '真正会问的问题。',
      right: '没有利润分成，设计上非托管，五个交易所，可私有部署。直球回答——和我们对机构交易团队说的完全一致。',
      q1: {
        q: '为什么零业绩分成？',
        a: '我们收的是基础设施的租金，而不是对你 alpha 征的税。一旦跟单平台开始分走你的上行收益，它就成了你沉默的合伙人。14 539% 的丰年，和持平的一年，缴的是同一笔固定租金——你的每一个基点都不会离开钱包。',
      },
      q2: {
        q: '我的资金会被托管吗？',
        a: '不会。Copy Trader 是非托管的。你接入的是只读+交易权限的 API 密钥；私钥与余额从不离开你的交易所。密钥保存在你自己的本地边界内，信号管道只能下单——永远无法提币。',
      },
      q3: {
        q: '支持哪些交易所？',
        a: '五个执行场所——Binance Futures、OKX Perpetual、Gate.io Perp、Bitget Mix 与 Hyperliquid（原生链上）——由六个信号源驱动，涵盖隐藏与未公开的交易席位，以及链上聪明钱。',
      },
      q4: {
        q: '我能私有部署吗？',
        a: '可以，在机构版。把执行层跑在你自己的边界内——你的密钥、你的出口 IP、你的 RPC 端点。信号管道永远不会离开你掌控的基础设施。',
      },
    },
    final: {
      titleLine1: '别再为你的',
      titleLine2: 'alpha',
      titleMark: '交税了。',
      sub: '七天，全功能，无需绑卡。接入一个交易所，订阅一位领单者，看着成交在两毫秒内镜像复制——只付一笔固定月费，绝不分走你的上行。',
      cta: '开启 7 天试用',
      fine: '5 个交易所 · 6 个信号源 · 0% 业绩分成',
    },
  },
  en: {
    head: {
      idx: '04 / PRICING',
      titleLine1: 'Rent the rails.',
      titleLine2: 'Keep the returns.',
      rightLead: 'One flat subscription, billed monthly. Zero performance fee at every tier — a ',
      rightInk: '14 539% year costs the same flat rent as a flat one',
      rightTail: '. Invite a peer for a 10% rebate; they start at half price. Month-to-month, no lock-in.',
    },
    plans: {
      trial: {
        name: 'Trial',
        note: '7 days, full access. No card required.',
      },
      pro: {
        name: 'Pro · Recommended',
        per: '/MO',
        note: 'For active multi-desk traders.',
      },
      inst: {
        name: 'Institutional',
        price: 'Custom',
        note: 'Desks, funds & lead traders.',
      },
    },
    matrix: {
      accounts: { label: 'Accounts', trial: '1 account', pro: '4 accounts', inst: 'Unlimited' },
      slots: { label: 'Copy slots', trial: '1 slot', pro: 'Multiple slots', inst: 'Unlimited' },
      speed: { label: 'Execution speed', trial: 'Standard', pro: 'Priority < 2 ms', inst: 'Priority RPC' },
      egress: { label: 'Dedicated egress IP', trial: '—', pro: 'Included', inst: 'Per-account' },
      sources: { label: 'Signal sources', trial: 'Core', pro: 'All 6 sources', inst: 'All 6 sources' },
      leadSeat: { label: 'Lead-trader seat', trial: '—', pro: '—', inst: 'Eligible' },
      selfHost: { label: 'Self-host + dedicated risk', trial: '—', pro: '—', inst: 'Included' },
      riskEngine: { label: 'Risk engine', trial: 'Pre-trade gate', pro: 'Pre-trade gate', inst: 'Per-account rules' },
      sla: { label: 'SLA', trial: 'Best-effort', pro: '99.9% uptime', inst: 'Custom SLA' },
      fee: { label: 'Performance fee', trial: '0%', pro: '0%', inst: '0%' },
    },
    cta: {
      trial: 'Start free',
      pro: 'Start Pro trial',
      inst: 'Talk to us',
    },
    strip: {
      zeroFee: 'Performance fee, every tier — profit stays in your wallet.',
      rebate: 'Lifetime rebate on every peer you invite.',
      half: 'Invited peers start at half price.',
    },
    value: {
      quoteLead: 'We charge rent on infrastructure, not a tax on your alpha. The moment a copy platform takes a cut of your upside, it has become your ',
      quoteAccent: 'silent partner',
      quoteTail: ' — and we refuse to be one.',
      cite: 'Copy Trader — operating principle №3',
      cardRoiUsdt: 'ROI · USDT',
      cardDaysLive: 'DAYS LIVE',
      cardIllustrative: 'ILLUSTRATIVE',
      footHeadlineRoi: 'Headline ROI',
      footFee: 'Performance fee',
      footKeep: 'You keep',
      honestLead: 'Not every desk prints. We list losing leaders honestly — e.g. ',
      honestSample: 'remains visible for study, never hidden from the leaderboard. Curves above are ',
      honestInk: 'illustrative',
      honestTail: ', not a promise of future return.',
    },
    faq: {
      idx: '05 / FAQ',
      titleLine1: 'The questions',
      titleLine2: 'desks actually ask.',
      right: 'No profit share, non-custodial by design, five venues, self-hostable. Straight answers — the same ones we give institutional desks.',
      q1: {
        q: 'Why zero performance fee?',
        a: 'We charge rent on infrastructure, not a tax on your alpha. The moment a copy platform takes a cut of your upside it becomes your silent partner. A 14 539% year costs the same flat rent as a flat one — your basis points never leave your wallet.',
      },
      q2: {
        q: 'Are my funds custodied?',
        a: 'No. Copy Trader is non-custodial. You connect read-and-trade API keys; private keys and balances never leave your exchange. Keys are held locally inside your own perimeter, and the signal pipeline only ever places orders — it can never withdraw.',
      },
      q3: {
        q: 'Which exchanges are supported?',
        a: 'Five execution venues — Binance Futures, OKX Perpetual, Gate.io Perp, Bitget Mix and Hyperliquid (on-chain native) — fed by six signal sources, including hidden and unlisted desks plus on-chain smart money.',
      },
      q4: {
        q: 'Can I self-host?',
        a: 'Yes, on the Institutional tier. Run the execution layer inside your own perimeter — your keys, your egress IPs, your RPC endpoints. The signal pipeline never leaves infrastructure you control.',
      },
    },
    final: {
      titleLine1: 'Stop paying a tax',
      titleLine2: 'on your',
      titleMark: 'alpha.',
      sub: 'Seven days, full access, no card. Connect one venue, subscribe to one desk, and watch the fills mirror in under two milliseconds — at a flat monthly rent, never a cut of your upside.',
      cta: 'Start 7-Day Trial',
      fine: '5 EXCHANGES · 6 SIGNAL SOURCES · 0% PERFORMANCE FEE',
    },
  },
}
