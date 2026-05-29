<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { usePublicTraders } from '@/composables/usePublicTraders'
import type { Trader } from '@/api/traders'

const { t, locale } = useI18n()

/* CJK 态去掉 Newsreader faux-italic（中文斜体难看），改用 accent 强调。
   英文态保留原型的衬线斜体。模板里 :class="itClass" 控制。 */
const isZh = computed(() => locale.value === 'zh-CN')

/* ───────────────────────────────────────────────────────────────
   INSTITUTIONAL CLARITY — Home landing page (faithful port of
   design/marketing/direction_clarity.html). Light Swiss theme is
   inherited from the .marketing-site scope on this component's root;
   only --m-* tokens are used (never dark --ct-*).
   ─────────────────────────────────────────────────────────────── */

/* ── number formatting: space thousands separator, tabular figures ── */
function fmt(n: number, dp = 2): string {
  const neg = n < 0
  const abs = Math.abs(n)
  const [int, dec] = abs.toFixed(dp).split('.')
  const grouped = int.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
  const sign = neg ? '−' : '' // U+2212 minus
  return sign + grouped + (dec ? '.' + dec : '')
}
function pnlStr(n: number): string {
  return (n >= 0 ? '+' : '') + fmt(n, 2)
}
function roiStr(n: number): string {
  return (n >= 0 ? '+' : '') + fmt(n, 2) + '%'
}
function pctStr(n: number | null): string {
  return n === null ? '—' : fmt(n, 2) + '%'
}

/* ── reveal-on-scroll (progressive enhancement; visible by default) ── */
const reduceMotion =
  typeof window !== 'undefined' &&
  window.matchMedia &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches

let io: IntersectionObserver | null = null
let failsafe: ReturnType<typeof setTimeout> | null = null
let barTimer: ReturnType<typeof setTimeout> | null = null

/* ── trader leaderboard teaser ──
   Public leaderboard via the shared composable: mock-seeded so the board is
   never empty, then silently upgraded to live data when the backend answers. */
const { traders: allTraders } = usePublicTraders()

/* Honest teaser slice — the six desks shown in the prototype, including
   the negative sample MaximizeSR (−6.03%) displayed truthfully. */
const teaserOrder = ['茂茂大魔王', '风火山林Trader', '牛的青山在', '寒星日照', 'KNOTMAIN', 'MaximizeSR']
const teaser = computed<Trader[]>(() => {
  const byName = new Map(allTraders.value.map((t) => [t.nickname, t]))
  return teaserOrder
    .map((nm) => byName.get(nm))
    .filter((t): t is Trader => Boolean(t))
})

/* ── monogram: CJK identity wins (first glyph); else up-to-2 Latin initials ── */
function monogram(name: string): string {
  if (/^[㐀-鿿]/.test(name)) return Array.from(name)[0]
  const latin = name.match(/[A-Za-z][A-Za-z0-9]*/g)
  if (latin && latin.length) {
    if (latin.length >= 2) return (latin[0][0] + latin[1][0]).toUpperCase()
    const w = latin[0]
    const caps = w.match(/[A-Z]/g)
    if (caps && caps.length >= 2) return caps[0] + caps[1]
    return w.slice(0, 2).toUpperCase()
  }
  return Array.from(name)[0] || '·'
}
function isCJK(name: string): boolean {
  return /[㐀-鿿]/.test(name)
}
function isHidden(t: Trader): boolean {
  return t.tags.includes('HIDDEN')
}
function srcLabel(t: Trader): string {
  return t.exchange.toUpperCase() + ' · ' + (t.sharpe !== null ? '90D' : 'LIVE')
}

/* ── deterministic mini sparkline path from a trader's curve[] ── */
function sparkPath(curve: number[] | undefined): string {
  const pts = curve && curve.length ? curve : [1, 1, 1]
  const n = pts.length
  const h = 34
  const w = 100
  const min = Math.min(...pts)
  const max = Math.max(...pts)
  const rng = max - min || 1
  let d = ''
  for (let i = 0; i < n; i++) {
    const x = (i / (n - 1)) * w
    const y = h - 2 - ((pts[i] - min) / rng) * (h - 6)
    d += (i === 0 ? 'M' : 'L') + x.toFixed(1) + ' ' + y.toFixed(1) + ' '
  }
  return d.trim()
}

/* ── features (six capabilities, link to /features) ──
   no / fill are data; copy (live/title/body/stat) is keyed under
   marketing.home.features.items.<key>.* and resolved via t() in template. */
interface Feat {
  no: string
  key: string
  fill: number
}
const feats: Feat[] = [
  { no: 'F·01', key: 'sources', fill: 92 },
  { no: 'F·02', key: 'params', fill: 88 },
  { no: 'F·03', key: 'egress', fill: 78 },
  { no: 'F·04', key: 'risk', fill: 84 },
  { no: 'F·05', key: 'onchain', fill: 70 },
  { no: 'F·06', key: 'attribution', fill: 96 }
]
const filledBars = ref(false)

/* ── pricing rows (faithful to prototype hairline comparison table) ──
   label / cell text are i18n keys (marketing.home.pricing.rows.* +
   .values.*) resolved via t() in template; the on/off/accent flags
   are presentation data and stay here. */
interface PriceRow {
  label: string
  trial: string
  pro: string
  inst: string
  trialOff?: boolean
  proOff?: boolean
  instOff?: boolean
  trialOn?: boolean
  proOn?: boolean
  instOn?: boolean
  accent?: boolean
}
const priceRows: PriceRow[] = [
  { label: 'accounts', trial: 'oneAccount', pro: 'fourAccounts', inst: 'unlimited' },
  { label: 'copySlots', trial: 'oneSlot', pro: 'multipleSlots', inst: 'unlimited' },
  { label: 'execSpeed', trial: 'standard', pro: 'priorityFast', inst: 'priorityRpc' },
  { label: 'egressIp', trial: 'none', pro: 'included', inst: 'perAccount', trialOff: true, proOn: true, instOn: true },
  { label: 'signalSources', trial: 'core', pro: 'allSixSources', inst: 'allSixSources', proOn: true, instOn: true },
  { label: 'leadSeat', trial: 'none', pro: 'none', inst: 'eligible', trialOff: true, proOff: true, instOn: true },
  { label: 'selfHost', trial: 'none', pro: 'none', inst: 'included', trialOff: true, proOff: true, instOn: true },
  { label: 'perfFee', trial: 'zeroPct', pro: 'zeroPct', inst: 'zeroPct', accent: true }
]

/* ── hero equity chart (ECharts, light single-color orange) ── */
const equityEl = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

function resizeChart() {
  chart?.resize()
}

function buildChart() {
  if (!equityEl.value) return
  if (chart) {
    chart.dispose()
    chart = null
  }
  chart = echarts.init(equityEl.value, undefined, { renderer: 'canvas' })

  /* Illustrative equity series compounded in log-space from many small
     bounded steps, anchored to the leader's headline metrics
     (茂茂大魔王: +14 539.61% ROI, 2.57% max drawdown). The series carries
     visible drawdown legs (no impossibly-smooth monotone climb) and lands
     exactly on the terminal equity. Labelled ILLUSTRATIVE in the card. */
  const N = 240
  const START = 9179
  const END = 1343829
  const DD_CAP = 0.0256
  const OSC = 0.024
  const mu = Math.log(END / START) / (N - 1)
  const osc: number[] = []
  for (let i = 0; i < N - 1; i++) {
    osc.push(
      Math.sin(i * 0.13) * 0.5 +
        Math.sin(i * 0.071 + 0.7) * 0.55 +
        Math.sin(i * 0.033 + 2.1) * 0.5 +
        Math.sin(i * 0.27 + 1.1) * 0.3 +
        Math.cos(i * 0.017) * 0.35
    )
  }
  const oscMean = osc.reduce((a, b) => a + b, 0) / (N - 1)
  const rets = osc.map((o) => mu + (o - oscMean) * OSC)
  const norm: number[] = [1]
  let peak = 1
  for (let i = 0; i < rets.length; i++) {
    let raw = norm[i] * Math.exp(rets[i])
    const floor = peak * (1 - DD_CAP)
    if (raw < floor) raw = floor
    if (raw > peak) peak = raw
    norm.push(raw)
  }
  const k = END / START / norm[norm.length - 1]
  const data = norm.map((x) => Math.round(x * k * START))

  chart.setOption({
    animation: !reduceMotion,
    animationDuration: 1400,
    animationEasing: 'cubicOut',
    grid: { left: 0, right: 0, top: 6, bottom: 0 },
    xAxis: {
      type: 'category',
      show: false,
      boundaryGap: false,
      data: data.map((_, i) => i)
    },
    yAxis: { type: 'value', show: false, scale: true, min: 0 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#14161A',
      borderColor: '#14161A',
      borderWidth: 0,
      padding: [7, 11],
      textStyle: { color: '#FCFCFA', fontFamily: 'Geist Mono, monospace', fontSize: 11 },
      formatter: (params: unknown) => {
        const arr = params as Array<{ value: number }>
        const v = arr[0].value
        return 'EQUITY  ' + v.toLocaleString('en-US').replace(/,/g, ' ') + ' USDT'
      },
      axisPointer: { type: 'line', lineStyle: { color: '#FF4D00', width: 1, type: 'solid' } }
    },
    series: [
      {
        type: 'line',
        data,
        showSymbol: false,
        smooth: 0.18,
        lineStyle: { color: '#FF4D00', width: 1.6 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255,77,0,0.13)' },
            { offset: 1, color: 'rgba(255,77,0,0.0)' }
          ])
        }
      }
    ]
  })
}

onMounted(async () => {
  await nextTick()
  buildChart()
  window.addEventListener('resize', resizeChart, { passive: true })

  /* feature bars fill (CSS transition) */
  barTimer = setTimeout(() => {
    filledBars.value = true
  }, 650)

  /* reveal */
  if (reduceMotion) {
    document.querySelectorAll<HTMLElement>('.home-stage .rv').forEach((el) => el.classList.add('in'))
    return
  }
  if ('IntersectionObserver' in window) {
    io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add('in')
            io?.unobserve(e.target)
          }
        })
      },
      { threshold: 0.08, rootMargin: '0px 0px -6% 0px' }
    )
    document.querySelectorAll<HTMLElement>('.home-stage .rv').forEach((el) => io?.observe(el))
    /* failsafe: reveal everything after 2.6s no matter what */
    failsafe = setTimeout(() => {
      document.querySelectorAll<HTMLElement>('.home-stage .rv').forEach((el) => el.classList.add('in'))
    }, 2600)
  } else {
    document.querySelectorAll<HTMLElement>('.home-stage .rv').forEach((el) => el.classList.add('in'))
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart)
  if (io) io.disconnect()
  if (failsafe) clearTimeout(failsafe)
  if (barTimer) clearTimeout(barTimer)
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<template>
  <div class="home-stage">
    <!-- ░░ HERO ░░ -->
    <section class="hero m-wrap" id="top">
      <div class="hero-tag rv">
        <span class="pill"><span class="blink"></span>{{ t('marketing.home.hero.pill') }}</span>
        <span class="meta m-mono">{{ t('marketing.home.hero.meta') }}</span>
      </div>

      <div class="hero-grid">
        <div class="hero-left rv">
          <h1 class="display">
            {{ t('marketing.home.hero.title1') }}<br />
            <span class="it">{{ t('marketing.home.hero.title2') }}</span><br />
            {{ t('marketing.home.hero.title3Pre') }} <span class="mark">{{ t('marketing.home.hero.title3Mark') }}</span>
          </h1>
          <p class="hero-sub">
            {{ t('marketing.home.hero.sub') }} <span class="strong">{{ t('marketing.home.hero.subStrong') }}</span>
          </p>
          <div class="hero-actions">
            <router-link class="m-btn m-btn-accent btn-hero" to="/register">
              {{ t('marketing.home.hero.ctaPrimary') }} <span class="arw">→</span>
            </router-link>
            <router-link class="textlink" to="/#traders">
              {{ t('marketing.home.hero.ctaSecondary') }} <span class="arw">→</span>
            </router-link>
            <span class="fineprint m-mono">{{ t('marketing.home.hero.fineprint') }}</span>
          </div>
        </div>

        <div class="hero-right rv">
          <div class="ticker-strip">
            <div class="cell">
              <div class="k">{{ t('marketing.home.ticker.btc') }}</div>
              <div class="v m-num">$74 180</div>
              <div class="vs m-num m-neg">−1.97% 24h</div>
            </div>
            <div class="cell">
              <div class="k">{{ t('marketing.home.ticker.fearGreed') }}</div>
              <div class="v m-num">22</div>
              <div class="vs m-neg">{{ t('marketing.home.ticker.extremeFear') }}</div>
            </div>
            <div class="cell">
              <div class="k">{{ t('marketing.home.ticker.liquidated') }}</div>
              <div class="v m-num">$289M</div>
              <div class="vs m-num ink3">−1h $3.65M</div>
            </div>
            <div class="cell">
              <div class="k">{{ t('marketing.home.ticker.funding') }}</div>
              <div class="v m-num">+0.010%</div>
              <div class="vs m-num m-pos">L/S 1.69</div>
            </div>
          </div>

          <div class="chartcard">
            <div class="chead">
              <div class="who">
                <span class="nm" lang="zh">茂茂大魔王</span>
                <span class="ex">OKX · <span lang="zh">币Coin</span></span>
              </div>
              <span class="pnl m-num m-pos">+1 343 829.94</span>
            </div>
            <div class="csub m-mono">
              <span>{{ t('marketing.home.chartCard.equity') }}</span>
              <span>{{ t('marketing.home.chartCard.daysLivePre') }} 2 209 {{ t('marketing.home.chartCard.daysLiveSuffix') }}</span>
              <span class="ink4">{{ t('marketing.home.chartCard.illustrative') }}</span>
            </div>
            <div ref="equityEl" class="equity-chart"></div>
            <div class="cfoot">
              <div class="m"><div class="ml">{{ t('marketing.home.chartCard.roi') }}</div><div class="mv m-num m-pos">+14 539.61%</div></div>
              <div class="m"><div class="ml">{{ t('marketing.home.chartCard.winRate') }}</div><div class="mv m-num">34.40%</div></div>
              <div class="m"><div class="ml">{{ t('marketing.home.chartCard.maxDd') }}</div><div class="mv m-num">2.57%</div></div>
              <div class="m"><div class="ml">{{ t('marketing.home.chartCard.latency') }}</div><div class="mv m-num accent">1.8 ms</div></div>
            </div>
          </div>
        </div>
      </div>

      <!-- evidence badges -->
      <div class="badges rv">
        <div class="badge">
          <div class="bnum m-num"><span class="mark">&lt;2</span><span class="u">ms</span></div>
          <div class="blabel">{{ t('marketing.home.badges.latency') }}</div>
        </div>
        <div class="badge">
          <div class="bnum m-num">5<span class="u sep">×</span>6</div>
          <div class="blabel">{{ t('marketing.home.badges.sources') }}</div>
        </div>
        <div class="badge">
          <div class="bnum m-num"><span class="mark">0%</span></div>
          <div class="blabel">{{ t('marketing.home.badges.fee') }}</div>
        </div>
      </div>
    </section>

    <!-- ░░ TRUST BAND ░░ -->
    <section class="trust m-wrap rv">
      <div class="trust-head">
        <span class="eyebrow m-mono"><span class="dot">●</span> {{ t('marketing.home.trust.eyebrow') }}</span>
        <span class="lead">{{ t('marketing.home.trust.lead') }}</span>
      </div>
      <div class="trust-row">
        <div class="trust-grp">
          <div class="glabel m-mono">{{ t('marketing.home.trust.venuesLabel') }}</div>
          <div class="gitems">
            <span class="it">Binance Futures</span>
            <span class="it">OKX Perpetual</span>
            <span class="it">Gate.io Perp</span>
            <span class="it">Bitget Mix</span>
            <span class="it hl">Hyperliquid <span class="tag accent">{{ t('marketing.home.trust.onchainTag') }}</span></span>
          </div>
        </div>
        <div class="trust-grp">
          <div class="glabel m-mono">{{ t('marketing.home.trust.sourcesLabel') }}</div>
          <div class="gitems">
            <span class="it">{{ t('marketing.home.trust.binanceCopy') }}</span>
            <span class="it">{{ t('marketing.home.trust.onchainMoney') }}</span>
            <span class="it">{{ t('marketing.home.trust.okxCopy') }}</span>
            <span class="it">Bitget</span>
            <span class="it"><span lang="zh">币Coin</span></span>
            <span class="it">Hyperliquid</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ░░ FEATURES ░░ -->
    <section class="section m-wrap" id="features">
      <div class="sec-head rv">
        <div>
          <div class="sec-idx m-mono">{{ t('marketing.home.features.idx') }}</div>
          <h2>{{ t('marketing.home.features.titlePre') }}<br /><span class="it" :class="{ 'it-zh': isZh }">{{ t('marketing.home.features.titleIt') }}</span>{{ t('marketing.home.features.titlePost') }}</h2>
        </div>
        <p class="right">{{ t('marketing.home.features.right') }}</p>
      </div>

      <div class="feat-grid rv">
        <router-link v-for="f in feats" :key="f.no" class="feat" to="/features">
          <div class="fno m-mono"><span>{{ f.no }}</span><span class="live">{{ t(`marketing.home.features.items.${f.key}.live`) }}</span></div>
          <h3>{{ t(`marketing.home.features.items.${f.key}.title`) }}</h3>
          <p>{{ t(`marketing.home.features.items.${f.key}.body`) }}</p>
          <div class="fstat m-mono">{{ t(`marketing.home.features.items.${f.key}.stat`) }}</div>
          <div class="fbar"><i :style="{ width: filledBars ? f.fill + '%' : '0%' }"></i></div>
        </router-link>
      </div>
    </section>

    <!-- ░░ TRADERS LEADERBOARD TEASER ░░ -->
    <section class="section m-wrap" id="traders">
      <div class="sec-head rv">
        <div>
          <div class="sec-idx m-mono">{{ t('marketing.home.traders.idx') }}</div>
          <h2>{{ t('marketing.home.traders.titlePre') }}<br /><span class="it" :class="{ 'it-zh': isZh }">{{ t('marketing.home.traders.titleIt') }}</span>{{ t('marketing.home.traders.titlePost') }}</h2>
        </div>
        <p class="right">{{ t('marketing.home.traders.right') }}</p>
      </div>

      <div class="rv">
        <div class="traders">
          <div v-for="tr in teaser" :key="tr.id" class="tcard">
            <div class="thead">
              <div class="avatar m-mono" aria-hidden="true">{{ monogram(tr.nickname) }}</div>
              <div class="who">
                <div class="nm">
                  <span :lang="isCJK(tr.nickname) ? 'zh' : undefined">{{ tr.nickname }}</span>
                  <span v-if="isHidden(tr)" class="badge-h m-mono">{{ t('marketing.home.traders.hidden') }}</span>
                </div>
                <div class="src m-mono">{{ srcLabel(tr) }}</div>
              </div>
            </div>

            <div class="pnlrow">
              <div class="pnlbig m-num" :class="tr.total_pnl >= 0 ? 'm-pos' : 'm-neg'">{{ pnlStr(tr.total_pnl) }}</div>
              <div class="roi m-num" :class="tr.roi >= 0 ? 'm-pos' : 'm-neg'">{{ roiStr(tr.roi) }}</div>
            </div>

            <svg class="spark" viewBox="0 0 100 34" preserveAspectRatio="none">
              <path
                :d="sparkPath(tr.curve)"
                fill="none"
                :stroke="tr.total_pnl >= 0 ? 'var(--m-accent)' : 'var(--m-neg)'"
                stroke-width="1.2"
                vector-effect="non-scaling-stroke"
              />
            </svg>

            <div class="grid4">
              <div class="c"><div class="l m-mono">{{ t('marketing.home.traders.winRate') }}</div><div class="v m-num">{{ pctStr(tr.win_rate) }}</div></div>
              <div class="c"><div class="l m-mono">{{ t('marketing.home.traders.maxDd') }}</div><div class="v m-num">{{ pctStr(tr.max_drawdown) }}</div></div>
              <div class="c">
                <div class="l m-mono">{{ tr.sharpe !== null ? t('marketing.home.traders.window') : t('marketing.home.traders.daysLive') }}</div>
                <div class="v m-num">{{ tr.sharpe !== null ? '90d' : fmt(tr.enrolled_days, 0) }}</div>
              </div>
              <div class="c">
                <div class="l m-mono">{{ tr.sharpe !== null ? t('marketing.home.traders.sharpe') : t('marketing.home.traders.mirrored') }}</div>
                <div class="v m-num">{{ tr.sharpe !== null ? fmt(tr.sharpe, 2) : fmt(tr.scale, 2) }}</div>
              </div>
            </div>

            <div class="tfoot">
              <div class="scale m-mono">USDT · {{ tr.total_pnl >= 0 ? t('marketing.home.traders.eligible') : t('marketing.home.traders.studyOnly') }}</div>
              <router-link class="copybtn m-mono-ctrl" to="/#traders">
                {{ tr.total_pnl >= 0 ? t('marketing.home.traders.copyDesk') : t('marketing.home.traders.inspect') }} <span class="arw">→</span>
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ░░ PRINCIPLES / EDITORIAL QUOTE ░░ -->
    <section class="section m-wrap" id="why">
      <div class="rv idx-only">
        <div class="sec-idx m-mono">{{ t('marketing.home.principles.idx') }}</div>
      </div>
      <div class="principles">
        <div class="quote rv">
          <p class="pull">
            <span class="mark m-mono">“</span>{{ t('marketing.home.principles.quote') }} <span class="it accent" :class="{ 'it-zh': isZh }">{{ t('marketing.home.principles.quoteAccent') }}</span>{{ t('marketing.home.principles.quoteEnd') }}<span class="mark m-mono">”</span>
          </p>
          <div class="pull-cite m-mono">{{ t('marketing.home.principles.cite') }}</div>
        </div>
        <div class="prin-list rv">
          <div class="prin">
            <div class="pno m-mono">01</div>
            <div>
              <h4>{{ t('marketing.home.principles.list.hyperliquid.title') }}</h4>
              <p>{{ t('marketing.home.principles.list.hyperliquid.bodyPre') }}<span class="em">{{ t('marketing.home.principles.list.hyperliquid.bodyEm') }}</span>{{ t('marketing.home.principles.list.hyperliquid.bodyPost') }}</p>
            </div>
          </div>
          <div class="prin">
            <div class="pno m-mono">02</div>
            <div>
              <h4>{{ t('marketing.home.principles.list.fee.title') }}</h4>
              <p>{{ t('marketing.home.principles.list.fee.bodyPre') }}<span class="em">{{ t('marketing.home.principles.list.fee.bodyEm') }}</span>{{ t('marketing.home.principles.list.fee.bodyPost') }}</p>
            </div>
          </div>
          <div class="prin">
            <div class="pno m-mono">03</div>
            <div>
              <h4>{{ t('marketing.home.principles.list.selfHost.title') }}</h4>
              <p>{{ t('marketing.home.principles.list.selfHost.bodyPre') }}<span class="em">{{ t('marketing.home.principles.list.selfHost.bodyEm') }}</span>{{ t('marketing.home.principles.list.selfHost.bodyPost') }}</p>
            </div>
          </div>
          <div class="prin">
            <div class="pno m-mono">04</div>
            <div>
              <h4>{{ t('marketing.home.principles.list.smartMoney.title') }}</h4>
              <p>{{ t('marketing.home.principles.list.smartMoney.bodyPre') }}<span class="em">{{ t('marketing.home.principles.list.smartMoney.bodyEm') }}</span>{{ t('marketing.home.principles.list.smartMoney.bodyPost') }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ░░ PRICING ░░ -->
    <section class="section m-wrap" id="pricing">
      <div class="sec-head rv">
        <div>
          <div class="sec-idx m-mono">{{ t('marketing.home.pricing.idx') }}</div>
          <h2>{{ t('marketing.home.pricing.titlePre') }}<br /><span class="it" :class="{ 'it-zh': isZh }">{{ t('marketing.home.pricing.titleIt') }}</span></h2>
        </div>
        <p class="right">{{ t('marketing.home.pricing.right') }}</p>
      </div>

      <div class="pricing-table rv">
        <!-- column heads -->
        <div class="pricing-row head-row">
          <div class="pcell rowlabel blank"></div>
          <div class="pcol-head">
            <div class="pname m-mono">{{ t('marketing.home.pricing.cols.trialName') }}</div>
            <div class="pprice m-num">{{ t('marketing.home.pricing.cols.trialPrice') }}</div>
            <div class="pnote">{{ t('marketing.home.pricing.cols.trialNote') }}</div>
          </div>
          <div class="pcol-head recommend">
            <div class="pname m-mono">{{ t('marketing.home.pricing.cols.proName') }}</div>
            <div class="pprice m-num">$80<span class="per">{{ t('marketing.home.pricing.cols.proPer') }}</span></div>
            <div class="pnote">{{ t('marketing.home.pricing.cols.proNote') }}</div>
          </div>
          <div class="pcol-head">
            <div class="pname m-mono">{{ t('marketing.home.pricing.cols.instName') }}</div>
            <div class="pprice m-num">{{ t('marketing.home.pricing.cols.instPrice') }}</div>
            <div class="pnote">{{ t('marketing.home.pricing.cols.instNote') }}</div>
          </div>
        </div>

        <div v-for="row in priceRows" :key="row.label" class="pricing-row">
          <div class="pcell rowlabel m-mono">{{ t(`marketing.home.pricing.rows.${row.label}`) }}</div>
          <div
            class="pcell"
            :class="{ 'feat-off': row.trialOff, 'feat-on': row.trialOn, accentcell: row.accent }"
          >{{ t(`marketing.home.pricing.values.${row.trial}`) }}</div>
          <div
            class="pcell"
            :class="{ 'feat-off': row.proOff, 'feat-on': row.proOn, accentcell: row.accent }"
          >{{ t(`marketing.home.pricing.values.${row.pro}`) }}</div>
          <div
            class="pcell"
            :class="{ 'feat-off': row.instOff, 'feat-on': row.instOn, accentcell: row.accent }"
          >{{ t(`marketing.home.pricing.values.${row.inst}`) }}</div>
        </div>

        <div class="pricing-foot">
          <div class="pcell rowlabel blank"></div>
          <div class="pcell cta"><router-link class="m-btn btn-ghost" to="/register">{{ t('marketing.home.pricing.cta.free') }}</router-link></div>
          <div class="pcell cta"><router-link class="m-btn m-btn-accent" to="/register">{{ t('marketing.home.pricing.cta.pro') }}</router-link></div>
          <div class="pcell cta"><router-link class="m-btn btn-ghost" to="/pricing">{{ t('marketing.home.pricing.cta.talk') }}</router-link></div>
        </div>
      </div>

      <div class="pricing-strip rv">
        <div class="pi"><span class="marker m-mono">{{ t('marketing.home.pricing.strip.feeMarker') }}</span> {{ t('marketing.home.pricing.strip.fee') }}</div>
        <div class="pi"><span class="marker m-mono">{{ t('marketing.home.pricing.strip.rebateMarker') }}</span> {{ t('marketing.home.pricing.strip.rebate') }}</div>
        <div class="pi"><span class="marker m-mono">{{ t('marketing.home.pricing.strip.halfMarker') }}</span> {{ t('marketing.home.pricing.strip.half') }}</div>
      </div>
    </section>

    <!-- ░░ FINAL CTA ░░ -->
    <section class="m-wrap">
      <div class="finalcta rv">
        <div class="fc-watermark" aria-hidden="true">
          <span class="fw-fig m-mono"><span class="lt">&lt;</span>2</span>
          <span class="fw-unit m-mono">{{ t('marketing.home.finalCta.watermark') }}</span>
        </div>
        <div class="fc-grid">
          <div>
            <h2>{{ t('marketing.home.finalCta.titlePre') }}<br /><span class="it" :class="{ 'it-zh': isZh }">{{ t('marketing.home.finalCta.titleIt') }}</span> <span class="mark">{{ t('marketing.home.finalCta.titleMark') }}</span>{{ t('marketing.home.finalCta.titleSuffix') }}</h2>
          </div>
          <div>
            <p class="fc-sub">{{ t('marketing.home.finalCta.sub') }}</p>
            <router-link class="m-btn m-btn-accent" to="/register">{{ t('marketing.home.finalCta.cta') }}</router-link>
            <div class="fc-fine m-mono">{{ t('marketing.home.finalCta.fine') }}</div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* All selectors nested under .marketing-site so this light Swiss page
   never reaches the dark D1 console. The root .marketing-site wrapper is
   provided by MarketingLayout; .home-stage is this page's inner stage. */

.marketing-site .home-stage { position: relative; }

/* eyebrow / hairline helpers reused on this page */
.marketing-site .home-stage .eyebrow {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--m-ink-3);
}
.marketing-site .home-stage .eyebrow .dot { color: var(--m-accent); }
.marketing-site .home-stage .ink3 { color: var(--m-ink-3); }
.marketing-site .home-stage .ink4 { color: var(--m-ink-4); }
.marketing-site .home-stage .accent { color: var(--m-accent); }
.marketing-site .home-stage .strong { color: var(--m-ink); }

/* CJK 态：衬线 faux-italic 在中文下难看 —— 去斜体、回到展示字体栈、
   以 accent 橙强调，保留编辑式重点(不改设计方向)。仅作用于 .it.it-zh。 */
.marketing-site .home-stage .it.it-zh,
.marketing-site .home-stage h1.display .it.it-zh,
.marketing-site .home-stage .sec-head h2 .it.it-zh,
.marketing-site .home-stage .finalcta h2 .it.it-zh {
  font-family: var(--m-font-display);
  font-style: normal;
  color: var(--m-accent);
}
/* 编辑式引语内的 accent 斜体短语：中文去斜，已是 accent 色保持。 */
.marketing-site .home-stage .pull .it.accent.it-zh { font-style: normal; }

/* ── hero ── */
.marketing-site .home-stage .hero {
  padding-top: clamp(56px, 7vw, 96px);
  padding-bottom: 0;
  position: relative;
}
.marketing-site .home-stage .hero-tag {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 34px;
  flex-wrap: wrap;
}
.marketing-site .home-stage .hero-tag .pill {
  font-family: var(--m-font-mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  color: var(--m-ink);
  border: 1px solid var(--m-line-strong);
  border-radius: 999px;
  padding: 5px 12px;
  display: inline-flex;
  align-items: center;
  gap: 7px;
}
.marketing-site .home-stage .hero-tag .pill .blink {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--m-accent);
  animation: m-pulse 1.8s ease-in-out infinite;
}
@keyframes m-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.35; transform: scale(0.7); }
}
@media (prefers-reduced-motion: reduce) {
  .marketing-site .home-stage .hero-tag .pill .blink { animation: none; }
}
.marketing-site .home-stage .hero-tag .meta {
  font-size: 11px;
  color: var(--m-ink-3);
  letter-spacing: 0.04em;
}

.marketing-site .home-stage .hero-grid {
  display: grid;
  grid-template-columns: 7fr 5fr;
  gap: 56px;
  align-items: end;
}
.marketing-site .home-stage h1.display {
  font-size: clamp(44px, 6.6vw, 92px);
  line-height: 0.96;
  font-weight: 600;
  letter-spacing: -0.035em;
  text-wrap: balance;
}
.marketing-site .home-stage h1.display .it {
  font-family: var(--m-font-serif);
  font-style: italic;
  font-weight: 400;
  letter-spacing: -0.01em;
}
.marketing-site .home-stage h1.display .mark { color: var(--m-accent); }
.marketing-site .home-stage .hero-sub {
  font-size: 18px;
  line-height: 1.55;
  color: var(--m-ink-2);
  max-width: 46ch;
  margin-top: 30px;
  letter-spacing: -0.01em;
  text-wrap: pretty;
}
.marketing-site .home-stage .hero-actions {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-top: 34px;
  flex-wrap: wrap;
}
.marketing-site .home-stage .hero-actions .btn-hero {
  font-size: 15px;
  padding: 13px 22px;
}
.marketing-site .home-stage .hero-actions .textlink {
  font-size: 14px;
  font-weight: 500;
  color: var(--m-ink-2);
  letter-spacing: -0.01em;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  border-bottom: 1px solid transparent;
  padding-bottom: 1px;
  transition: color 0.15s, border-color 0.15s;
}
.marketing-site .home-stage .hero-actions .textlink .arw {
  font-family: var(--m-font-mono);
  font-weight: 400;
  color: var(--m-ink-3);
  transition: color 0.15s, transform 0.15s;
}
.marketing-site .home-stage .hero-actions .textlink:hover {
  color: var(--m-ink);
  border-bottom-color: var(--m-ink-4);
}
.marketing-site .home-stage .hero-actions .textlink:hover .arw {
  color: var(--m-accent);
  transform: translateX(2px);
}
.marketing-site .home-stage .hero-actions .fineprint {
  font-size: 11px;
  color: var(--m-ink-3);
  letter-spacing: 0.02em;
}

.marketing-site .home-stage .hero-right { position: relative; }
.marketing-site .home-stage .ticker-strip {
  border: 1px solid var(--m-line);
  border-radius: 3px;
  background: var(--m-paper);
  display: grid;
  grid-template-columns: repeat(4, 1fr);
}
.marketing-site .home-stage .ticker-strip .cell {
  padding: 13px 14px;
  border-right: 1px solid var(--m-line);
}
.marketing-site .home-stage .ticker-strip .cell:last-child { border-right: 0; }
.marketing-site .home-stage .ticker-strip .k {
  font-family: var(--m-font-mono);
  font-size: 9.5px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--m-ink-3);
  margin-bottom: 6px;
}
.marketing-site .home-stage .ticker-strip .v {
  font-size: 15px;
  font-weight: 500;
  letter-spacing: -0.01em;
}
.marketing-site .home-stage .ticker-strip .vs {
  font-size: 10px;
  margin-top: 2px;
}

.marketing-site .home-stage .chartcard {
  border: 1px solid var(--m-line);
  border-radius: 3px;
  background: var(--m-paper);
  margin-top: 14px;
  overflow: hidden;
}
.marketing-site .home-stage .chartcard .chead {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 14px 16px 6px;
}
.marketing-site .home-stage .chartcard .chead .who {
  display: flex;
  align-items: baseline;
  gap: 9px;
}
.marketing-site .home-stage .chartcard .chead .who .nm {
  font-weight: 600;
  font-size: 14px;
  letter-spacing: -0.01em;
}
.marketing-site .home-stage .chartcard .chead .who .ex {
  font-family: var(--m-font-mono);
  font-size: 10px;
  color: var(--m-ink-3);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.marketing-site .home-stage .chartcard .chead .pnl {
  font-size: 17px;
  font-weight: 600;
  letter-spacing: -0.01em;
}
.marketing-site .home-stage .chartcard .csub {
  padding: 0 16px 8px;
  font-size: 10px;
  color: var(--m-ink-3);
  letter-spacing: 0.03em;
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.marketing-site .home-stage .equity-chart {
  width: 100%;
  height: 188px;
}
.marketing-site .home-stage .chartcard .cfoot {
  display: flex;
  border-top: 1px solid var(--m-line);
}
.marketing-site .home-stage .chartcard .cfoot .m {
  flex: 1;
  padding: 10px 16px;
  border-right: 1px solid var(--m-line);
}
.marketing-site .home-stage .chartcard .cfoot .m:last-child { border-right: 0; }
.marketing-site .home-stage .chartcard .cfoot .m .ml {
  font-family: var(--m-font-mono);
  font-size: 9px;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--m-ink-3);
}
.marketing-site .home-stage .chartcard .cfoot .m .mv {
  font-size: 13.5px;
  font-weight: 500;
  margin-top: 3px;
}

/* evidence badges */
.marketing-site .home-stage .badges {
  margin-top: clamp(56px, 7vw, 90px);
  border-top: 1px solid var(--m-ink);
  border-bottom: 1px solid var(--m-line);
  display: grid;
  grid-template-columns: repeat(3, 1fr);
}
.marketing-site .home-stage .badge {
  padding: 30px 8px 30px 0;
  border-right: 1px solid var(--m-line);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.marketing-site .home-stage .badge:nth-child(3n) { border-right: 0; }
.marketing-site .home-stage .badge .bnum {
  font-size: clamp(30px, 3.5vw, 44px);
  font-weight: 600;
  letter-spacing: -0.03em;
  line-height: 1;
  display: flex;
  align-items: baseline;
  gap: 4px;
}
.marketing-site .home-stage .badge .bnum .u {
  font-size: 0.42em;
  color: var(--m-ink-3);
  font-weight: 500;
  letter-spacing: 0;
}
.marketing-site .home-stage .badge .bnum .u.sep { color: var(--m-ink-4); }
.marketing-site .home-stage .badge .bnum .mark { color: var(--m-accent); }
.marketing-site .home-stage .badge .blabel {
  font-size: 13.5px;
  color: var(--m-ink-2);
  max-width: 30ch;
  letter-spacing: -0.01em;
  text-wrap: pretty;
}

/* ── section rhythm ── */
.marketing-site .home-stage .section { padding-top: clamp(64px, 8vw, 118px); }

/* ── trust band ── */
.marketing-site .home-stage .trust {
  padding-top: clamp(54px, 6vw, 84px);
  padding-bottom: clamp(54px, 6vw, 84px);
}
.marketing-site .home-stage .trust-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 30px;
  flex-wrap: wrap;
  gap: 12px;
}
.marketing-site .home-stage .trust-head .lead {
  font-family: var(--m-font-serif);
  font-style: italic;
  font-size: 19px;
  color: var(--m-ink-2);
  letter-spacing: -0.01em;
}
.marketing-site .home-stage .trust-row {
  display: flex;
  flex-direction: column;
  border-top: 1px solid var(--m-line);
}
.marketing-site .home-stage .trust-grp {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 24px;
  padding: 22px 0;
  border-bottom: 1px solid var(--m-line);
  align-items: center;
}
.marketing-site .home-stage .trust-grp .glabel {
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--m-ink-3);
}
.marketing-site .home-stage .trust-grp .gitems {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 28px;
}
.marketing-site .home-stage .trust-grp .gitems .it {
  font-size: 18px;
  font-weight: 500;
  letter-spacing: -0.02em;
  color: var(--m-ink);
  display: inline-flex;
  align-items: center;
  gap: 9px;
}
.marketing-site .home-stage .trust-grp .gitems .it .tag {
  font-family: var(--m-font-mono);
  font-size: 9.5px;
  color: var(--m-ink-3);
  letter-spacing: 0.05em;
  border: 1px solid var(--m-line);
  border-radius: 999px;
  padding: 2px 7px;
  text-transform: uppercase;
}
.marketing-site .home-stage .trust-grp .gitems .it .tag.accent {
  border-color: var(--m-accent);
  color: var(--m-accent);
}
.marketing-site .home-stage .trust-grp .gitems .it.hl { color: var(--m-accent); }

/* ── section header ── */
.marketing-site .home-stage .sec-head {
  display: grid;
  grid-template-columns: 7fr 5fr;
  gap: 40px;
  align-items: end;
  margin-bottom: 46px;
}
.marketing-site .home-stage .sec-head h2 {
  font-size: clamp(30px, 3.6vw, 46px);
  line-height: 1.02;
  font-weight: 600;
  letter-spacing: -0.03em;
  text-wrap: balance;
}
.marketing-site .home-stage .sec-head h2 .it {
  font-family: var(--m-font-serif);
  font-style: italic;
  font-weight: 400;
}
.marketing-site .home-stage .sec-head .right {
  font-size: 15px;
  color: var(--m-ink-2);
  line-height: 1.55;
  letter-spacing: -0.01em;
  text-wrap: pretty;
  padding-bottom: 4px;
}
.marketing-site .home-stage .sec-idx {
  font-size: 11px;
  color: var(--m-accent);
  letter-spacing: 0.1em;
  margin-bottom: 18px;
}
.marketing-site .home-stage .idx-only { margin-bottom: 46px; }

/* ── features ── */
.marketing-site .home-stage .feat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border-top: 1px solid var(--m-ink);
  border-left: 1px solid var(--m-line);
}
.marketing-site .home-stage .feat {
  padding: 32px 30px 36px;
  border-right: 1px solid var(--m-line);
  border-bottom: 1px solid var(--m-line);
  position: relative;
  background: var(--m-paper);
  transition: background 0.2s;
  display: block;
  color: inherit;
}
.marketing-site .home-stage .feat:hover { background: var(--m-paper-2); }
.marketing-site .home-stage .feat .fno {
  font-size: 11px;
  color: var(--m-ink-4);
  letter-spacing: 0.08em;
  margin-bottom: 22px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.marketing-site .home-stage .feat .fno .live { color: var(--m-accent); }
.marketing-site .home-stage .feat h3 {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin-bottom: 11px;
  line-height: 1.2;
}
.marketing-site .home-stage .feat p {
  font-size: 14px;
  color: var(--m-ink-2);
  line-height: 1.6;
  letter-spacing: -0.005em;
  text-wrap: pretty;
}
.marketing-site .home-stage .feat .fstat {
  margin-top: 18px;
  font-size: 11px;
  color: var(--m-ink-3);
  letter-spacing: 0.03em;
}
.marketing-site .home-stage .feat .fbar {
  margin-top: 13px;
  height: 2px;
  background: var(--m-line);
  position: relative;
  overflow: hidden;
}
.marketing-site .home-stage .feat .fbar i {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  background: var(--m-accent);
  width: 0;
  transition: width 1.1s cubic-bezier(0.2, 0.8, 0.2, 1);
}
@media (prefers-reduced-motion: reduce) {
  .marketing-site .home-stage .feat .fbar i { transition: none; }
}

/* ── traders leaderboard teaser ── */
.marketing-site .home-stage .traders {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border-left: 1px solid var(--m-line);
  border-top: 1px solid var(--m-ink);
}
.marketing-site .home-stage .tcard {
  border-right: 1px solid var(--m-line);
  border-bottom: 1px solid var(--m-line);
  padding: 22px 22px 0;
  display: flex;
  flex-direction: column;
  background: var(--m-paper);
  transition: background 0.18s;
}
.marketing-site .home-stage .tcard:hover { background: var(--m-paper-2); }
.marketing-site .home-stage .tcard .thead {
  display: flex;
  align-items: center;
  gap: 13px;
  margin-bottom: 16px;
}
.marketing-site .home-stage .tcard .avatar {
  width: 42px;
  height: 42px;
  border-radius: 2px;
  border: 1px solid var(--m-line);
  background: var(--m-paper-2);
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 500;
  color: var(--m-ink-3);
  letter-spacing: 0.02em;
  line-height: 1;
  text-transform: uppercase;
}
.marketing-site .home-stage .tcard .who .nm {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.1;
  display: flex;
  align-items: center;
  gap: 7px;
}
.marketing-site .home-stage .tcard .who .nm .badge-h {
  font-size: 8.5px;
  letter-spacing: 0.05em;
  color: var(--m-accent);
  border: 1px solid var(--m-accent);
  border-radius: 999px;
  padding: 1px 6px;
  text-transform: uppercase;
  font-weight: 500;
}
.marketing-site .home-stage .tcard .who .src {
  font-size: 10px;
  color: var(--m-ink-3);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-top: 4px;
}
.marketing-site .home-stage .tcard .pnlbig {
  font-weight: 600;
  font-size: 26px;
  letter-spacing: -0.03em;
  line-height: 1;
  margin-bottom: 3px;
}
.marketing-site .home-stage .tcard .pnlrow {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 14px;
  gap: 12px;
}
.marketing-site .home-stage .tcard .roi {
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
}
.marketing-site .home-stage .tcard .spark {
  height: 34px;
  margin: 0 -22px 14px;
  width: calc(100% + 44px);
  display: block;
}
.marketing-site .home-stage .tcard .grid4 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  border-top: 1px solid var(--m-line);
}
.marketing-site .home-stage .tcard .grid4 .c {
  padding: 10px 0;
  border-bottom: 1px solid var(--m-line);
}
.marketing-site .home-stage .tcard .grid4 .c:nth-child(odd) {
  padding-right: 12px;
  border-right: 1px solid var(--m-line);
  padding-left: 0;
}
.marketing-site .home-stage .tcard .grid4 .c:nth-child(even) { padding-left: 14px; }
.marketing-site .home-stage .tcard .grid4 .c .l {
  font-size: 9px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--m-ink-3);
}
.marketing-site .home-stage .tcard .grid4 .c .v {
  font-size: 13.5px;
  font-weight: 500;
  margin-top: 3px;
}
.marketing-site .home-stage .tcard .tfoot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0;
  margin-top: auto;
  gap: 10px;
}
.marketing-site .home-stage .tcard .tfoot .scale {
  font-size: 10px;
  color: var(--m-ink-3);
  letter-spacing: 0.03em;
}
.marketing-site .home-stage .tcard .copybtn {
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  border: 1px solid var(--m-ink);
  background: transparent;
  color: var(--m-ink);
  padding: 7px 13px;
  border-radius: var(--m-radius);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
  white-space: nowrap;
}
.marketing-site .home-stage .tcard .copybtn:hover {
  background: var(--m-accent);
  border-color: var(--m-accent);
  color: var(--m-paper);
}
.marketing-site .home-stage .tcard .copybtn .arw { font-size: 13px; }

/* ── principles / editorial quote ── */
.marketing-site .home-stage .principles {
  display: grid;
  grid-template-columns: 5fr 7fr;
  gap: 64px;
  align-items: start;
}
.marketing-site .home-stage .principles .quote {
  position: sticky;
  top: 96px;
}
.marketing-site .home-stage .pull {
  font-family: var(--m-font-serif);
  font-style: italic;
  font-size: clamp(26px, 2.9vw, 38px);
  line-height: 1.28;
  letter-spacing: -0.01em;
  color: var(--m-ink);
  text-wrap: pretty;
}
.marketing-site .home-stage .pull .mark {
  color: var(--m-accent);
  font-style: normal;
  font-size: 0.62em;
  vertical-align: 0.18em;
}
.marketing-site .home-stage .pull .it.accent {
  color: var(--m-accent);
}
.marketing-site .home-stage .pull-cite {
  margin-top: 26px;
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--m-ink-3);
  display: flex;
  align-items: center;
  gap: 10px;
}
.marketing-site .home-stage .pull-cite::before {
  content: "";
  width: 28px;
  height: 1px;
  background: var(--m-accent);
}
.marketing-site .home-stage .prin-list {
  display: flex;
  flex-direction: column;
  border-top: 1px solid var(--m-ink);
}
.marketing-site .home-stage .prin {
  display: grid;
  grid-template-columns: 48px 1fr;
  gap: 20px;
  padding: 26px 0;
  border-bottom: 1px solid var(--m-line);
}
.marketing-site .home-stage .prin .pno {
  font-size: 12px;
  color: var(--m-accent);
  letter-spacing: 0.04em;
  padding-top: 3px;
}
.marketing-site .home-stage .prin h4 {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin-bottom: 7px;
}
.marketing-site .home-stage .prin p {
  font-size: 14px;
  color: var(--m-ink-2);
  line-height: 1.6;
  letter-spacing: -0.005em;
  text-wrap: pretty;
  max-width: 54ch;
}
.marketing-site .home-stage .prin p .em { color: var(--m-ink); font-weight: 500; }

/* ── pricing ── */
.marketing-site .home-stage .pricing-table {
  border-top: 1px solid var(--m-ink);
  border-left: 1px solid var(--m-line);
}
.marketing-site .home-stage .pricing-row,
.marketing-site .home-stage .pricing-foot {
  display: grid;
  grid-template-columns: 1.4fr 1fr 1fr 1fr;
  border-bottom: 1px solid var(--m-line);
}
.marketing-site .home-stage .pcell {
  padding: 18px 22px;
  border-right: 1px solid var(--m-line);
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.marketing-site .home-stage .pcell.rowlabel {
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--m-ink-3);
  background: var(--m-paper-2);
}
.marketing-site .home-stage .pcell.rowlabel.blank { background: var(--m-paper); }
.marketing-site .home-stage .pcell.feat-on { color: var(--m-ink); }
.marketing-site .home-stage .pcell.feat-off { color: var(--m-ink-4); }
.marketing-site .home-stage .pcell.accentcell { color: var(--m-accent); font-weight: 500; }
.marketing-site .home-stage .pcol-head { padding: 26px 22px 24px; }
.marketing-site .home-stage .pcol-head.recommend { background: var(--m-ink); color: var(--m-paper); }
.marketing-site .home-stage .pcol-head .pname {
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--m-ink-3);
  margin-bottom: 14px;
}
.marketing-site .home-stage .pcol-head.recommend .pname { color: var(--m-accent); }
.marketing-site .home-stage .pcol-head .pprice {
  font-size: 34px;
  font-weight: 600;
  letter-spacing: -0.03em;
  line-height: 1;
  display: flex;
  align-items: baseline;
  gap: 3px;
}
.marketing-site .home-stage .pcol-head .pprice .per {
  font-size: 12px;
  color: var(--m-ink-3);
  font-weight: 500;
  letter-spacing: 0.04em;
}
.marketing-site .home-stage .pcol-head.recommend .pprice .per { color: var(--m-ink-4); }
.marketing-site .home-stage .pcol-head .pnote {
  font-size: 13px;
  color: var(--m-ink-2);
  margin-top: 11px;
  letter-spacing: -0.01em;
  line-height: 1.4;
}
.marketing-site .home-stage .pcol-head.recommend .pnote { color: var(--m-ink-4); }
.marketing-site .home-stage .pcell.cta { padding: 18px 22px; }
.marketing-site .home-stage .pcell.cta .m-btn { width: 100%; justify-content: center; }
.marketing-site .home-stage .m-btn.btn-ghost {
  background: transparent;
  color: var(--m-ink);
  border: 1px solid var(--m-line-strong);
}
.marketing-site .home-stage .m-btn.btn-ghost:hover {
  background: var(--m-ink);
  color: var(--m-paper);
  border-color: var(--m-ink);
}
.marketing-site .home-stage .pricing-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 24px;
  padding: 18px 22px;
  border: 1px solid var(--m-line);
  border-radius: 3px;
  background: var(--m-paper-2);
}
.marketing-site .home-stage .pricing-strip .pi {
  display: flex;
  align-items: center;
  gap: 11px;
  font-size: 13.5px;
  color: var(--m-ink-2);
  letter-spacing: -0.01em;
}
.marketing-site .home-stage .pricing-strip .pi .marker {
  font-size: 11px;
  color: var(--m-accent);
  border: 1px solid var(--m-accent);
  border-radius: 999px;
  padding: 2px 8px;
  letter-spacing: 0.04em;
}

/* ── final cta ── */
.marketing-site .home-stage .finalcta {
  background: var(--m-ink);
  color: var(--m-paper);
  border-radius: 4px;
  padding: clamp(48px, 6vw, 84px) var(--m-pad);
  margin-top: clamp(64px, 8vw, 118px);
  position: relative;
  overflow: hidden;
}
.marketing-site .home-stage .finalcta .fc-grid {
  display: grid;
  grid-template-columns: 7fr 5fr;
  gap: 48px;
  align-items: end;
  position: relative;
  z-index: 2;
}
.marketing-site .home-stage .finalcta h2 {
  font-size: clamp(34px, 4.6vw, 62px);
  line-height: 0.98;
  font-weight: 600;
  letter-spacing: -0.035em;
  text-wrap: balance;
}
.marketing-site .home-stage .finalcta h2 .it {
  font-family: var(--m-font-serif);
  font-style: italic;
  font-weight: 400;
}
.marketing-site .home-stage .finalcta h2 .mark { color: var(--m-accent); }
.marketing-site .home-stage .finalcta .fc-sub {
  font-size: 16px;
  color: rgba(252, 252, 250, 0.62);
  line-height: 1.55;
  margin-bottom: 26px;
  letter-spacing: -0.01em;
  text-wrap: pretty;
}
.marketing-site .home-stage .finalcta .m-btn-accent {
  font-size: 15px;
  padding: 13px 22px;
}
.marketing-site .home-stage .finalcta .fc-fine {
  font-size: 11px;
  color: rgba(252, 252, 250, 0.45);
  letter-spacing: 0.03em;
  margin-top: 18px;
}
.marketing-site .home-stage .fc-watermark {
  position: absolute;
  right: clamp(-12px, -1vw, 0px);
  bottom: clamp(-28px, -3vw, -12px);
  z-index: 1;
  pointer-events: none;
  user-select: none;
  line-height: 0.82;
  text-align: right;
}
.marketing-site .home-stage .fc-watermark .fw-fig {
  font-weight: 500;
  font-size: clamp(120px, 21vw, 300px);
  letter-spacing: -0.04em;
  color: rgba(255, 77, 0, 0.085);
  display: block;
}
.marketing-site .home-stage .fc-watermark .fw-fig .lt {
  font-family: var(--m-font-serif);
  font-style: italic;
  font-weight: 400;
}
.marketing-site .home-stage .fc-watermark .fw-unit {
  font-weight: 500;
  font-size: clamp(22px, 3.4vw, 46px);
  letter-spacing: 0.04em;
  color: rgba(255, 77, 0, 0.1);
  display: block;
  margin-top: clamp(-18px, -1.4vw, -8px);
  padding-right: clamp(8px, 1vw, 18px);
}

/* ── reveal (progressive enhancement; visible by default) ── */
.marketing-site .home-stage .rv { opacity: 1; }
@media (prefers-reduced-motion: no-preference) {
  .marketing-site .home-stage .rv {
    opacity: 0;
    transform: translateY(14px);
    transition: opacity 0.7s cubic-bezier(0.2, 0.7, 0.2, 1), transform 0.7s cubic-bezier(0.2, 0.7, 0.2, 1);
  }
  .marketing-site .home-stage .rv.in {
    opacity: 1;
    transform: none;
  }
}

/* ── responsive ──
   Breakpoint contract (matches MarketingLayout): desktop base ≥961;
   tablet ≤960; intermediate ≤768; mobile ≤640; fine ≤420. The Swiss
   "graceful shed": 2-up grids → 1-up, side-by-side editorial splits
   stack, the hero data panel drops below the headline, hairline grids
   reflow their borders so nothing overflows or double-rules. All giant
   display titles are clamp()-fluid (declared above) so no breakpoint
   font overrides are needed — they shrink continuously in both
   zh-CN (denser) and en (wider) without horizontal scroll. */

/* ── tablet ≤960: editorial splits stack; 3-up grids → 2-up ── */
@media (max-width: 960px) {
  /* hero: headline above, data panel (ticker + chart card) below */
  .marketing-site .home-stage .hero-grid {
    grid-template-columns: 1fr;
    gap: clamp(34px, 5vw, 48px);
    align-items: start;
  }
  /* editorial 2-col splits collapse to single column */
  .marketing-site .home-stage .sec-head,
  .marketing-site .home-stage .principles,
  .marketing-site .home-stage .finalcta .fc-grid {
    grid-template-columns: 1fr;
    gap: clamp(28px, 4vw, 44px);
  }
  /* sticky pull-quote releases once the column collapses */
  .marketing-site .home-stage .principles .quote { position: static; }

  /* 3-up card grids → 2-up; restore the right rule that 3n removed */
  .marketing-site .home-stage .feat-grid,
  .marketing-site .home-stage .traders {
    grid-template-columns: repeat(2, 1fr);
  }
  .marketing-site .home-stage .feat:nth-child(3n) { border-right: 1px solid var(--m-line); }
}

/* ── intermediate ≤768: pricing table folds; 2-up grids → 1-up ── */
@media (max-width: 768px) {
  /* card grids → single column (avatars + 26px PnL would crowd at 2-up) */
  .marketing-site .home-stage .feat-grid,
  .marketing-site .home-stage .traders {
    grid-template-columns: 1fr;
  }
  /* with one column the 3n right-rule reset is no longer relevant */
  .marketing-site .home-stage .feat:nth-child(3n) { border-right: 1px solid var(--m-line); }

  /* pricing comparison table can no longer hold 4 columns on a phone:
     fold to a stacked tier list (label row + 3 tier cells per row). */
  .marketing-site .home-stage .pricing-row,
  .marketing-site .home-stage .pricing-foot {
    grid-template-columns: 1fr;
  }
  .marketing-site .home-stage .pricing-row .pcell,
  .marketing-site .home-stage .pricing-foot .pcell,
  .marketing-site .home-stage .pcol-head {
    border-right: 0;
  }
  /* keep the row-label visible as a stacked group heading */
  .marketing-site .home-stage .pricing-row .pcell.rowlabel { background: var(--m-paper-2); }
  /* head row: 3 tier columns side-by-side above the stacked value rows */
  .marketing-site .home-stage .pricing-row.head-row {
    grid-template-columns: repeat(3, 1fr);
  }
  .marketing-site .home-stage .pricing-row.head-row .rowlabel.blank { display: none; }
  .marketing-site .home-stage .pcol-head { padding: 20px 16px; }
  .marketing-site .home-stage .pcol-head .pprice { font-size: 28px; }
  /* CTA footer: 3 buttons in a row, full-width each */
  .marketing-site .home-stage .pricing-foot {
    grid-template-columns: repeat(3, 1fr);
  }
  .marketing-site .home-stage .pricing-foot .rowlabel.blank { display: none; }
  .marketing-site .home-stage .pricing-foot .pcell.cta { padding: 14px; }
}

/* ── mobile ≤640: single-column everything; hairline grids reflow ── */
@media (max-width: 640px) {
  /* ticker strip 4 → 2 columns; bottom row keeps a top hairline */
  .marketing-site .home-stage .ticker-strip { grid-template-columns: repeat(2, 1fr); }
  .marketing-site .home-stage .ticker-strip .cell { padding: 11px 12px; }
  .marketing-site .home-stage .ticker-strip .cell:nth-child(2n) { border-right: 0; }
  .marketing-site .home-stage .ticker-strip .cell:nth-child(1),
  .marketing-site .home-stage .ticker-strip .cell:nth-child(2) { border-bottom: 1px solid var(--m-line); }

  /* evidence badges 3 → 1 column, stacked with bottom hairlines */
  .marketing-site .home-stage .badges { grid-template-columns: 1fr; }
  .marketing-site .home-stage .badge {
    border-right: 0;
    border-bottom: 1px solid var(--m-line);
    padding: 22px 0;
  }
  .marketing-site .home-stage .badge:last-child { border-bottom: 0; }

  /* trust groups: label above items (160px fixed label would crush) */
  .marketing-site .home-stage .trust-grp { grid-template-columns: 1fr; gap: 12px; }
  .marketing-site .home-stage .trust-grp .gitems { gap: 8px 20px; }

  /* pricing tier heads stack to one column too (3-up too tight <640) */
  .marketing-site .home-stage .pricing-row.head-row,
  .marketing-site .home-stage .pricing-foot {
    grid-template-columns: 1fr;
  }
  .marketing-site .home-stage .pcol-head { padding: 22px; }
  .marketing-site .home-stage .pcol-head .pprice { font-size: 32px; }
  /* pricing strip stacks its three claims */
  .marketing-site .home-stage .pricing-strip { flex-direction: column; align-items: flex-start; }

  /* hero actions: keep CTA + link readable, allow wrap with tighter gap */
  .marketing-site .home-stage .hero-actions { gap: 16px; }
  .marketing-site .home-stage .hero-sub { font-size: 16px; margin-top: 22px; }

  /* chart card foot: 4 metrics would crush at <640 — wrap to 2×2 */
  .marketing-site .home-stage .chartcard .cfoot { flex-wrap: wrap; }
  .marketing-site .home-stage .chartcard .cfoot .m {
    flex: 1 0 50%;
    border-bottom: 1px solid var(--m-line);
  }
  .marketing-site .home-stage .chartcard .cfoot .m:nth-child(2n) { border-right: 0; }
  .marketing-site .home-stage .chartcard .cfoot .m:nth-child(3),
  .marketing-site .home-stage .chartcard .cfoot .m:nth-child(4) { border-bottom: 0; }
}

/* ── fine ≤420: trim chrome so nothing wraps awkwardly on small phones ── */
@media (max-width: 420px) {
  /* shorten the equity chart a touch so the hero card isn't too tall */
  .marketing-site .home-stage .equity-chart { height: 150px; }
  /* chart head: name + big PnL can collide — let the PnL drop below */
  .marketing-site .home-stage .chartcard .chead {
    flex-wrap: wrap;
    gap: 4px 10px;
  }
  .marketing-site .home-stage .chartcard .chead .pnl { font-size: 15px; }
  /* trader card PnL: shrink the giant figure so long values don't clip */
  .marketing-site .home-stage .tcard .pnlbig { font-size: 22px; }
  .marketing-site .home-stage .tcard { padding: 18px 18px 0; }
  .marketing-site .home-stage .tcard .spark {
    margin: 0 -18px 14px;
    width: calc(100% + 36px);
  }
  /* hero CTA full-width for a clean tap target; link below it */
  .marketing-site .home-stage .hero-actions { gap: 14px; }
  .marketing-site .home-stage .hero-actions .btn-hero {
    width: 100%;
    justify-content: center;
  }
  /* badges: keep the giant numerals from overflowing the viewport */
  .marketing-site .home-stage .badge .bnum { font-size: clamp(26px, 9vw, 36px); }
}
</style>
