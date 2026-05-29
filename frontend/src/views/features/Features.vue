<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { usePublicTraders } from '@/composables/usePublicTraders'

const { t } = useI18n()

/* ── types ──────────────────────────────────────────────────── */
/* `name` is real data (exchange / source proper nouns) → stays hardcoded.
   `badgeKey` resolves to marketing.features.sources.badge.* ; the source
   copy (body/stat) is keyed positionally as sources.s0NBody / s0NStat. */
interface SignalSource {
  no: string
  name: string
  badgeKey: string
  hl?: boolean
  tag?: string
  bodyKey: string
  statKey: string
}
interface EngineGroup {
  no: string
  /* gKey = i18n group key (engine.g01 …); fKeys = leaf suffixes per row */
  gKey: string
  fields: { k: string; v: string }[]
}
interface Principle {
  no: string
  pKey: string
}

/* ── 06 signal sources (names = data; copy keyed) ─────────────── */
const sources: SignalSource[] = [
  {
    no: 'S·01',
    name: 'Hyperliquid',
    badgeKey: 'onchainNative',
    hl: true,
    tag: '<200ms',
    bodyKey: 's01Body',
    statKey: 's01Stat'
  },
  {
    no: 'S·02',
    name: 'OKX copy desks',
    badgeKey: 'publicApi',
    bodyKey: 's02Body',
    statKey: 's02Stat'
  },
  {
    no: 'S·03',
    name: 'On-chain smart money',
    badgeKey: 'multiChain',
    bodyKey: 's03Body',
    statKey: 's03Stat'
  },
  {
    no: 'S·04',
    name: 'Binance copy desks',
    badgeKey: 'leadTraders',
    bodyKey: 's04Body',
    statKey: 's04Stat'
  },
  {
    no: 'S·05',
    name: 'Bitget',
    badgeKey: 'mixPerp',
    bodyKey: 's05Body',
    statKey: 's05Stat'
  },
  {
    no: 'S·06',
    name: '币Coin',
    badgeKey: 'rankings',
    bodyKey: 's06Body',
    statKey: 's06Stat'
  }
]

/* ── 20+ copy-engine parameters, grouped (keyed by position) ──── */
const engineGroups: EngineGroup[] = [
  {
    no: 'P·01',
    gKey: 'g01',
    fields: [{ k: 'f1k', v: 'f1v' }, { k: 'f2k', v: 'f2v' }, { k: 'f3k', v: 'f3v' }, { k: 'f4k', v: 'f4v' }]
  },
  {
    no: 'P·02',
    gKey: 'g02',
    fields: [{ k: 'f1k', v: 'f1v' }, { k: 'f2k', v: 'f2v' }, { k: 'f3k', v: 'f3v' }, { k: 'f4k', v: 'f4v' }]
  },
  {
    no: 'P·03',
    gKey: 'g03',
    fields: [{ k: 'f1k', v: 'f1v' }, { k: 'f2k', v: 'f2v' }, { k: 'f3k', v: 'f3v' }, { k: 'f4k', v: 'f4v' }]
  },
  {
    no: 'P·04',
    gKey: 'g04',
    fields: [{ k: 'f1k', v: 'f1v' }, { k: 'f2k', v: 'f2v' }, { k: 'f3k', v: 'f3v' }, { k: 'f4k', v: 'f4v' }]
  },
  {
    no: 'P·05',
    gKey: 'g05',
    fields: [{ k: 'f1k', v: 'f1v' }, { k: 'f2k', v: 'f2v' }, { k: 'f3k', v: 'f3v' }, { k: 'f4k', v: 'f4v' }]
  },
  {
    no: 'P·06',
    gKey: 'g06',
    fields: [{ k: 'f1k', v: 'f1v' }, { k: 'f2k', v: 'f2v' }, { k: 'f3k', v: 'f3v' }, { k: 'f4k', v: 'f4v' }]
  }
]

/* ── 04 differentiators / first principles (copy keyed) ──────── */
const principles: Principle[] = [
  { no: '01', pKey: 'p1' },
  { no: '02', pKey: 'p2' },
  { no: '03', pKey: 'p3' },
  { no: '04', pKey: 'p4' }
]

/* ── multi-account / risk infra static metrics (account data) ── */
const egressIps = ['8.211.140.223', '43.153.149.108', '101.36.104.169', '47.245.8.141']

/* risk controls: IDs only; k/v/m copy resolves via marketing.features.isolation.* */
const riskControls = [{ id: 'r1' }, { id: 'r2' }, { id: 'r3' }, { id: 'r4' }]

/* ── attribution: real curve from the top leader (illustrative) ─
   Public data via the shared composable: mock-seeded (never empty), then
   silently upgraded to live rows. Derivations stay reactive via computed. */
const { traders } = usePublicTraders()
const lead = computed(() => traders.value.find((t) => t.nickname === '茂茂大魔王') ?? traders.value[0])
const negSample = computed(() => traders.value.find((t) => t.nickname === 'MaximizeSR'))

const leadWinRate = computed(() => lead.value.win_rate ?? 0)
const leadMaxDd = computed(() => lead.value.max_drawdown ?? 0)

const attributionMetrics = computed(() => {
  const knot = traders.value.find((t) => t.nickname === 'KNOTMAIN')
  return [
    { k: 'Sharpe', v: knot && knot.sharpe != null ? knot.sharpe.toFixed(2) : '3.20' },
    { k: 'Calmar', v: '4.02' },
    { k: 'MAR', v: '2.71' },
    { k: 'Max DD', v: fmtPct(leadMaxDd.value) }
  ]
})

/* ── formatting helpers (千分位空格, tabular) ─────────────────── */
function fmtNum(n: number, dp = 2): string {
  const fixed = Math.abs(n).toFixed(dp)
  const [int, dec] = fixed.split('.')
  const grouped = int.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
  const sign = n < 0 ? '−' : ''
  return sign + grouped + (dec ? '.' + dec : '')
}
function fmtSigned(n: number, dp = 2): string {
  const sign = n < 0 ? '−' : '+'
  return sign + fmtNum(Math.abs(n), dp)
}
function fmtPct(n: number): string {
  const sign = n < 0 ? '−' : '+'
  return sign + fmtNum(Math.abs(n), 2) + '%'
}

const leadPnl = computed(() => fmtSigned(lead.value.total_pnl, 2))
const leadRoi = computed(() => fmtPct(lead.value.roi))
const leadWin = computed(() => fmtNum(leadWinRate.value, 2) + '%')
const leadDd = computed(() => fmtNum(leadMaxDd.value, 2) + '%')
const leadDays = computed(() => fmtNum(lead.value.enrolled_days, 0))

/* ── ECharts: illustrative equity (light, single orange line) ── */
const chartEl = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null
let onResize: (() => void) | null = null

function buildSeries(): number[] {
  const N = 200
  const START = 9179
  const END = lead.value.total_pnl
  const DD_CAP = leadMaxDd.value / 100
  const OSC = 0.024
  const mu = Math.log(END / START) / (N - 1)
  const osc: number[] = []
  for (let i = 0; i < N - 1; i++) {
    osc.push(
      Math.sin(i * 0.13) * 0.5 +
        Math.sin(i * 0.071 + 0.7) * 0.55 +
        Math.sin(i * 0.033 + 2.1) * 0.5 +
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
  return norm.map((x) => Math.round(x * k * START))
}

function drawChart(): void {
  if (!chartEl.value) return
  chart = echarts.init(chartEl.value, undefined, { renderer: 'canvas' })
  const data = buildSeries()
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  chart.setOption({
    animation: !reduce,
    animationDuration: 1200,
    animationEasing: 'cubicOut',
    backgroundColor: 'transparent',
    grid: { left: 0, right: 0, top: 8, bottom: 0 },
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
      formatter: (params: unknown): string => {
        const arr = params as { value: number }[]
        const v = arr && arr[0] ? Number(arr[0].value) : 0
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

/* ── reveal on scroll (progressive enhancement; visible by default) ── */
const root = ref<HTMLElement | null>(null)
let io: IntersectionObserver | null = null
let failsafe: ReturnType<typeof setTimeout> | null = null

onMounted(async () => {
  await nextTick()
  drawChart()
  onResize = () => chart?.resize()
  window.addEventListener('resize', onResize)

  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (!reduce && 'IntersectionObserver' in window && root.value) {
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
    root.value.querySelectorAll('.rv').forEach((el) => io?.observe(el))
    failsafe = setTimeout(() => {
      root.value?.querySelectorAll('.rv').forEach((el) => el.classList.add('in'))
    }, 2600)
  }
})

onBeforeUnmount(() => {
  if (onResize) window.removeEventListener('resize', onResize)
  if (io) io.disconnect()
  if (failsafe) clearTimeout(failsafe)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div ref="root" class="m-features">
    <!-- ░░ HERO ░░ -->
    <section class="m-wrap fx-hero">
      <div class="fx-tag rv">
        <span class="eyebrow"><span class="dot">●</span> {{ t('marketing.features.hero.eyebrow') }}</span>
        <span class="meta m-mono">{{ t('marketing.features.hero.meta') }}</span>
      </div>
      <div class="fx-hero-grid">
        <div class="rv">
          <h1 class="display">
            {{ t('marketing.features.hero.titleA') }}<br />
            {{ t('marketing.features.hero.titleB') }}<span class="it">{{ t('marketing.features.hero.titleItalic') }}</span>{{ t('marketing.features.hero.titleC') }}<br />
            {{ t('marketing.features.hero.titlePre') }}<span class="mark">{{ t('marketing.features.hero.titleMark') }}</span>
          </h1>
        </div>
        <p class="fx-hero-sub rv">
          {{ t('marketing.features.hero.sub') }}
        </p>
      </div>
    </section>

    <!-- ░░ 01 · SIGNAL SOURCES ░░ -->
    <section class="m-wrap section">
      <div class="sec-head rv">
        <div>
          <div class="sec-idx">{{ t('marketing.features.sources.idx') }}</div>
          <h2>{{ t('marketing.features.sources.titleA') }}<br /><span class="it">{{ t('marketing.features.sources.titleItalic') }}</span> {{ t('marketing.features.sources.titleB') }}</h2>
        </div>
        <p class="right">
          {{ t('marketing.features.sources.lead') }}
        </p>
      </div>

      <div class="src-grid rv">
        <article v-for="s in sources" :key="s.no" class="src" :class="{ hl: s.hl }">
          <div class="src-no m-mono">
            <span>{{ s.no }}</span>
            <span class="badge" :class="{ on: s.hl }">{{ t('marketing.features.sources.badge.' + s.badgeKey) }}</span>
          </div>
          <h3>
            <span :lang="/[㐀-鿿]/.test(s.name) ? 'zh' : undefined">{{ s.name }}</span>
            <span v-if="s.tag" class="lat m-mono">{{ s.tag }}</span>
          </h3>
          <p>{{ t('marketing.features.sources.' + s.bodyKey) }}</p>
          <div class="src-stat m-mono">{{ t('marketing.features.sources.' + s.statKey) }}</div>
        </article>
      </div>
    </section>

    <!-- ░░ 02 · COPY ENGINE ░░ -->
    <section class="m-wrap section">
      <div class="sec-head rv">
        <div>
          <div class="sec-idx">{{ t('marketing.features.engine.idx') }}</div>
          <h2>{{ t('marketing.features.engine.titleA') }}<br /><span class="it">{{ t('marketing.features.engine.titleItalic') }}</span> {{ t('marketing.features.engine.titleB') }}</h2>
        </div>
        <p class="right">
          {{ t('marketing.features.engine.lead') }}
        </p>
      </div>

      <div class="eng-grid rv">
        <article v-for="g in engineGroups" :key="g.no" class="eng">
          <div class="eng-head">
            <span class="eng-no m-mono">{{ g.no }}</span>
            <h4>{{ t('marketing.features.engine.' + g.gKey + '.title') }}</h4>
            <span class="eng-count m-mono">{{ t('marketing.features.engine.' + g.gKey + '.count') }}</span>
          </div>
          <dl class="eng-fields">
            <div v-for="f in g.fields" :key="f.k" class="ef">
              <dt>{{ t('marketing.features.engine.' + g.gKey + '.' + f.k) }}</dt>
              <dd class="m-mono">{{ t('marketing.features.engine.' + g.gKey + '.' + f.v) }}</dd>
            </div>
          </dl>
        </article>
      </div>
    </section>

    <!-- ░░ 03 · ISOLATION + RISK ░░ -->
    <section class="m-wrap section">
      <div class="sec-head rv">
        <div>
          <div class="sec-idx">{{ t('marketing.features.isolation.idx') }}</div>
          <h2>{{ t('marketing.features.isolation.titleA') }}<br /><span class="it">{{ t('marketing.features.isolation.titleItalic') }}</span> {{ t('marketing.features.isolation.titleB') }}</h2>
        </div>
        <p class="right">
          {{ t('marketing.features.isolation.lead') }}
        </p>
      </div>

      <div class="split rv">
        <!-- multi-account / egress IP -->
        <div class="panel">
          <div class="panel-head m-mono">
            <span>{{ t('marketing.features.isolation.multiHead') }}</span>
            <span class="phl">{{ t('marketing.features.isolation.multiPhl') }}</span>
          </div>
          <div class="ip-rows">
            <div v-for="(ip, i) in egressIps" :key="ip" class="ip-row">
              <span class="ip-acct m-mono">{{ t('marketing.features.isolation.acct') }}_0{{ i + 1 }}</span>
              <span class="ip-val m-mono">{{ ip }}</span>
              <span class="ip-state m-mono pos">{{ t('marketing.features.isolation.stateEncrypted') }}</span>
            </div>
          </div>
          <div class="panel-foot m-mono">
            {{ t('marketing.features.isolation.multiFoot') }}
          </div>
        </div>

        <!-- risk engine -->
        <div class="panel">
          <div class="panel-head m-mono">
            <span>{{ t('marketing.features.isolation.riskHead') }}</span>
            <span class="phl">{{ t('marketing.features.isolation.riskPhl') }}</span>
          </div>
          <div class="risk-rows">
            <div v-for="r in riskControls" :key="r.id" class="risk-row">
              <div class="rk">
                <span class="rk-name">{{ t('marketing.features.isolation.' + r.id + 'k') }}</span>
                <span class="rk-mode m-mono">{{ t('marketing.features.isolation.' + r.id + 'm') }}</span>
              </div>
              <span class="rk-v">{{ t('marketing.features.isolation.' + r.id + 'v') }}</span>
            </div>
          </div>
          <div class="panel-foot m-mono">
            {{ t('marketing.features.isolation.riskFoot') }}
          </div>
        </div>
      </div>
    </section>

    <!-- ░░ 04 · ATTRIBUTION ░░ -->
    <section class="m-wrap section">
      <div class="sec-head rv">
        <div>
          <div class="sec-idx">{{ t('marketing.features.attribution.idx') }}</div>
          <h2>{{ t('marketing.features.attribution.titleA') }}<br />{{ t('marketing.features.attribution.titleMid') }}<span class="it">{{ t('marketing.features.attribution.titleItalic') }}</span></h2>
        </div>
        <p class="right">
          {{ t('marketing.features.attribution.lead') }}
        </p>
      </div>

      <div class="attr rv">
        <!-- equity card (real leader, illustrative curve) -->
        <div class="chartcard">
          <div class="chead">
            <div class="who">
              <span class="nm" lang="zh">{{ lead.nickname }}</span>
              <span class="ex m-mono">{{ lead.exchange.toUpperCase() }} · 币Coin</span>
            </div>
            <span class="pnl m-mono pos">{{ leadPnl }}</span>
          </div>
          <div class="csub m-mono">
            <span>{{ t('marketing.features.attribution.equityLabel') }}</span>
            <span>{{ leadDays }} {{ t('marketing.features.attribution.daysLive') }}</span>
            <span class="muted">{{ t('marketing.features.attribution.illustrative') }}</span>
          </div>
          <div ref="chartEl" class="equity-chart"></div>
          <div class="cfoot">
            <div class="m">
              <div class="ml m-mono">{{ t('marketing.features.attribution.cfootRoi') }}</div>
              <div class="mv m-mono pos">{{ leadRoi }}</div>
            </div>
            <div class="m">
              <div class="ml m-mono">{{ t('marketing.features.attribution.cfootWin') }}</div>
              <div class="mv m-mono">{{ leadWin }}</div>
            </div>
            <div class="m">
              <div class="ml m-mono">{{ t('marketing.features.attribution.cfootDd') }}</div>
              <div class="mv m-mono">{{ leadDd }}</div>
            </div>
            <div class="m">
              <div class="ml m-mono">{{ t('marketing.features.attribution.cfootLatency') }}</div>
              <div class="mv m-mono accent">1.8 ms</div>
            </div>
          </div>
        </div>

        <!-- attribution side: risk metrics + honest negative sample -->
        <div class="attr-side">
          <div class="metrics">
            <div v-for="mtr in attributionMetrics" :key="mtr.k" class="metric">
              <div class="mk m-mono">{{ mtr.k }}</div>
              <div class="mvv m-mono">{{ mtr.v }}</div>
            </div>
          </div>

          <div v-if="negSample" class="neg-card">
            <div class="neg-head m-mono">
              <span>{{ t('marketing.features.attribution.negHead') }}</span>
              <span class="neg-flag">{{ t('marketing.features.attribution.negFlag') }}</span>
            </div>
            <div class="neg-row">
              <span class="neg-nm">{{ negSample.nickname }}</span>
              <span class="neg-pnl m-mono neg">{{ fmtPct(negSample.roi) }}</span>
            </div>
            <p class="neg-note">
              {{ t('marketing.features.attribution.negNoteA') }} {{ negSample.nickname }}
              {{ t('marketing.features.attribution.negNoteB') }}
              <span class="m-mono">{{ fmtPct(negSample.roi) }}</span>
              {{ t('marketing.features.attribution.negNoteC') }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- ░░ 05 · FIRST PRINCIPLES / DIFFERENTIATION ░░ -->
    <section class="m-wrap section">
      <div class="rv idx-row">
        <div class="sec-idx">{{ t('marketing.features.principles.idx') }}</div>
      </div>
      <div class="principles">
        <div class="quote rv">
          <p class="pull">
            <span class="mark">{{ t('marketing.features.principles.quoteOpen') }}</span>{{ t('marketing.features.principles.quoteA') }}
            <span class="it">{{ t('marketing.features.principles.quoteItalic') }}</span>{{ t('marketing.features.principles.quoteB') }}<span class="mark">{{ t('marketing.features.principles.quoteClose') }}</span>
          </p>
          <div class="pull-cite">{{ t('marketing.features.principles.cite') }}</div>
        </div>
        <div class="prin-list rv">
          <div v-for="p in principles" :key="p.no" class="prin">
            <div class="pno m-mono">{{ p.no }}</div>
            <div>
              <h4>{{ t('marketing.features.principles.' + p.pKey + '.title') }}</h4>
              <p>{{ t('marketing.features.principles.' + p.pKey + '.body') }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ░░ FINAL CTA ░░ -->
    <section class="m-wrap">
      <div class="finalcta rv">
        <div class="fc-watermark" aria-hidden="true">
          <span class="fw-fig m-mono"><span class="lt">&lt;</span>2</span>
          <span class="fw-unit m-mono">{{ t('marketing.features.cta.watermarkUnit') }}</span>
        </div>
        <div class="fc-grid">
          <div>
            <h2>{{ t('marketing.features.cta.titleA') }}<br /><span class="it">{{ t('marketing.features.cta.titleItalic') }}</span> <span class="mark">{{ t('marketing.features.cta.titleMark') }}</span> {{ t('marketing.features.cta.titleB') }}</h2>
          </div>
          <div>
            <p class="fc-sub">
              {{ t('marketing.features.cta.sub') }}
            </p>
            <router-link class="m-btn m-btn-accent" to="/register">{{ t('marketing.features.cta.button') }} <span class="arw">→</span></router-link>
            <div class="fc-fine m-mono">{{ t('marketing.features.cta.fine') }}</div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* All selectors nested under .marketing-site so this never reaches the dark
   D1 console. The .marketing-site element is provided by MarketingLayout; this
   page renders into its router-view and inherits the light Swiss scope + --m-* tokens. */

.marketing-site .m-features {
  padding-bottom: clamp(40px, 5vw, 72px);
}

/* shared editorial primitives ───────────────────────────────── */
.marketing-site .m-features .eyebrow {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--m-ink-3);
  font-family: var(--m-font-mono);
}
.marketing-site .m-features .eyebrow .dot { color: var(--m-accent); }

.marketing-site .m-features .it {
  font-family: var(--m-font-serif);
  font-style: italic;
  font-weight: 400;
  letter-spacing: -0.01em;
}
.marketing-site .m-features .mark { color: var(--m-accent); }
.marketing-site .m-features .pos { color: var(--m-pos); }
.marketing-site .m-features .neg { color: var(--m-neg); }
.marketing-site .m-features .accent { color: var(--m-accent); }
.marketing-site .m-features .muted { color: var(--m-ink-4); }

/* ── hero ── */
.marketing-site .m-features .fx-hero {
  padding-top: clamp(48px, 6vw, 88px);
}
.marketing-site .m-features .fx-tag {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 34px;
}
.marketing-site .m-features .fx-tag .meta {
  font-size: 11px;
  color: var(--m-ink-3);
  letter-spacing: 0.04em;
}
.marketing-site .m-features .fx-hero-grid {
  display: grid;
  grid-template-columns: 7fr 5fr;
  gap: 56px;
  align-items: end;
}
.marketing-site .m-features h1.display {
  font-size: clamp(38px, 5.4vw, 76px);
  line-height: 0.98;
  font-weight: 600;
  letter-spacing: -0.035em;
  text-wrap: balance;
}
.marketing-site .m-features .fx-hero-sub {
  font-size: 17px;
  line-height: 1.58;
  color: var(--m-ink-2);
  letter-spacing: -0.01em;
  max-width: 46ch;
  padding-bottom: 6px;
}

/* ── section scaffold ── */
.marketing-site .m-features .section {
  padding-top: clamp(60px, 8vw, 112px);
}
.marketing-site .m-features .sec-head {
  display: grid;
  grid-template-columns: 7fr 5fr;
  gap: 40px;
  align-items: end;
  margin-bottom: 46px;
}
.marketing-site .m-features .sec-idx {
  font-family: var(--m-font-mono);
  font-size: 11px;
  color: var(--m-accent);
  letter-spacing: 0.1em;
  margin-bottom: 18px;
}
.marketing-site .m-features .sec-head h2 {
  font-size: clamp(28px, 3.6vw, 46px);
  line-height: 1.02;
  font-weight: 600;
  letter-spacing: -0.03em;
  text-wrap: balance;
}
.marketing-site .m-features .sec-head .right {
  font-size: 15px;
  color: var(--m-ink-2);
  line-height: 1.55;
  letter-spacing: -0.01em;
  padding-bottom: 4px;
}

/* ── 01 signal sources ── */
.marketing-site .m-features .src-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border-top: 1px solid var(--m-ink);
  border-left: 1px solid var(--m-line);
}
.marketing-site .m-features .src {
  padding: 30px 28px 32px;
  border-right: 1px solid var(--m-line);
  border-bottom: 1px solid var(--m-line);
  background: var(--m-paper);
  transition: background 0.2s;
  display: flex;
  flex-direction: column;
}
.marketing-site .m-features .src:hover { background: var(--m-paper-2); }
.marketing-site .m-features .src.hl { background: var(--m-accent-soft); }
.marketing-site .m-features .src-no {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: var(--m-ink-4);
  letter-spacing: 0.08em;
  margin-bottom: 22px;
}
.marketing-site .m-features .src-no .badge {
  font-size: 9px;
  letter-spacing: 0.07em;
  color: var(--m-ink-3);
  border: 1px solid var(--m-line);
  border-radius: 999px;
  padding: 2px 8px;
}
.marketing-site .m-features .src-no .badge.on {
  color: var(--m-accent);
  border-color: var(--m-accent);
}
.marketing-site .m-features .src h3 {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin-bottom: 11px;
  line-height: 1.2;
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.marketing-site .m-features .src h3 .lat {
  font-size: 10px;
  letter-spacing: 0.04em;
  color: var(--m-accent);
  border: 1px solid var(--m-accent);
  border-radius: 999px;
  padding: 2px 7px;
  font-weight: 500;
}
.marketing-site .m-features .src p {
  font-size: 14px;
  color: var(--m-ink-2);
  line-height: 1.6;
  letter-spacing: -0.005em;
  flex: 1;
}
.marketing-site .m-features .src-stat {
  margin-top: 18px;
  font-size: 11px;
  color: var(--m-ink-3);
  letter-spacing: 0.03em;
}

/* ── 02 copy engine ── */
.marketing-site .m-features .eng-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border-top: 1px solid var(--m-ink);
  border-left: 1px solid var(--m-line);
}
.marketing-site .m-features .eng {
  padding: 26px 26px 18px;
  border-right: 1px solid var(--m-line);
  border-bottom: 1px solid var(--m-line);
  background: var(--m-paper);
}
.marketing-site .m-features .eng-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 16px;
}
.marketing-site .m-features .eng-no {
  font-size: 11px;
  color: var(--m-ink-4);
  letter-spacing: 0.08em;
}
.marketing-site .m-features .eng-head h4 {
  font-size: 17px;
  font-weight: 600;
  letter-spacing: -0.02em;
  flex: 1;
}
.marketing-site .m-features .eng-count {
  font-size: 10px;
  color: var(--m-accent);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.marketing-site .m-features .eng-fields {
  border-top: 1px solid var(--m-line);
}
.marketing-site .m-features .ef {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 14px;
  padding: 9px 0;
  border-bottom: 1px solid var(--m-line);
}
.marketing-site .m-features .ef:last-child { border-bottom: 0; }
.marketing-site .m-features .ef dt {
  font-size: 13px;
  color: var(--m-ink);
  letter-spacing: -0.005em;
}
.marketing-site .m-features .ef dd {
  font-size: 11px;
  color: var(--m-ink-3);
  letter-spacing: 0.02em;
  text-align: right;
  white-space: nowrap;
}

/* ── 03 isolation + risk ── */
.marketing-site .m-features .split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--m-grid-gap);
}
.marketing-site .m-features .panel {
  border: 1px solid var(--m-line);
  border-radius: var(--m-radius);
  background: var(--m-paper);
  display: flex;
  flex-direction: column;
}
.marketing-site .m-features .panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 13px 16px;
  border-bottom: 1px solid var(--m-line);
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--m-ink-3);
}
.marketing-site .m-features .panel-head .phl { color: var(--m-accent); }
.marketing-site .m-features .ip-rows { padding: 4px 16px; }
.marketing-site .m-features .ip-row {
  display: grid;
  grid-template-columns: 110px 1fr auto;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--m-line);
}
.marketing-site .m-features .ip-row:last-child { border-bottom: 0; }
.marketing-site .m-features .ip-acct {
  font-size: 11px;
  color: var(--m-ink-3);
  letter-spacing: 0.04em;
}
.marketing-site .m-features .ip-val {
  font-size: 13.5px;
  color: var(--m-ink);
  letter-spacing: -0.01em;
}
.marketing-site .m-features .ip-state {
  font-size: 9.5px;
  letter-spacing: 0.06em;
}
.marketing-site .m-features .risk-rows { padding: 4px 16px; }
.marketing-site .m-features .risk-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  padding: 13px 0;
  border-bottom: 1px solid var(--m-line);
}
.marketing-site .m-features .risk-row:last-child { border-bottom: 0; }
.marketing-site .m-features .rk {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.marketing-site .m-features .rk-name {
  font-size: 14px;
  font-weight: 500;
  letter-spacing: -0.01em;
}
.marketing-site .m-features .rk-mode {
  font-size: 9.5px;
  color: var(--m-accent);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.marketing-site .m-features .rk-v {
  font-size: 13px;
  color: var(--m-ink-2);
  text-align: right;
  max-width: 22ch;
  letter-spacing: -0.005em;
}
.marketing-site .m-features .panel-foot {
  margin-top: auto;
  padding: 12px 16px;
  border-top: 1px solid var(--m-line);
  font-size: 10px;
  color: var(--m-ink-3);
  letter-spacing: 0.02em;
  line-height: 1.5;
}

/* ── 04 attribution ── */
.marketing-site .m-features .attr {
  display: grid;
  grid-template-columns: 7fr 5fr;
  gap: var(--m-grid-gap);
  align-items: start;
}
.marketing-site .m-features .chartcard {
  border: 1px solid var(--m-line);
  border-radius: var(--m-radius);
  background: var(--m-paper);
  overflow: hidden;
}
.marketing-site .m-features .chead {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 16px 18px 6px;
}
.marketing-site .m-features .chead .who {
  display: flex;
  align-items: baseline;
  gap: 9px;
}
.marketing-site .m-features .chead .who .nm {
  font-weight: 600;
  font-size: 15px;
  letter-spacing: -0.01em;
}
.marketing-site .m-features .chead .who .ex {
  font-size: 10px;
  color: var(--m-ink-3);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.marketing-site .m-features .chead .pnl {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.01em;
}
.marketing-site .m-features .csub {
  padding: 0 18px 8px;
  font-size: 10px;
  color: var(--m-ink-3);
  letter-spacing: 0.03em;
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.marketing-site .m-features .equity-chart {
  width: 100%;
  height: 220px;
}
.marketing-site .m-features .cfoot {
  display: flex;
  border-top: 1px solid var(--m-line);
}
.marketing-site .m-features .cfoot .m {
  flex: 1;
  padding: 11px 16px;
  border-right: 1px solid var(--m-line);
}
.marketing-site .m-features .cfoot .m:last-child { border-right: 0; }
.marketing-site .m-features .cfoot .ml {
  font-size: 9px;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--m-ink-3);
}
.marketing-site .m-features .cfoot .mv {
  font-size: 13.5px;
  font-weight: 500;
  margin-top: 3px;
}

.marketing-site .m-features .attr-side {
  display: flex;
  flex-direction: column;
  gap: var(--m-grid-gap);
}
.marketing-site .m-features .metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  border-top: 1px solid var(--m-ink);
  border-left: 1px solid var(--m-line);
}
.marketing-site .m-features .metric {
  padding: 18px 18px 20px;
  border-right: 1px solid var(--m-line);
  border-bottom: 1px solid var(--m-line);
  background: var(--m-paper);
}
.marketing-site .m-features .metric .mk {
  font-size: 10px;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--m-ink-3);
  margin-bottom: 8px;
}
.marketing-site .m-features .metric .mvv {
  font-size: clamp(24px, 2.6vw, 32px);
  font-weight: 600;
  letter-spacing: -0.03em;
  line-height: 1;
}
.marketing-site .m-features .neg-card {
  border: 1px solid var(--m-line);
  border-radius: var(--m-radius);
  background: var(--m-paper);
  padding: 18px;
}
.marketing-site .m-features .neg-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: 9.5px;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--m-ink-3);
  margin-bottom: 14px;
}
.marketing-site .m-features .neg-head .neg-flag { color: var(--m-neg); }
.marketing-site .m-features .neg-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--m-line);
  margin-bottom: 12px;
}
.marketing-site .m-features .neg-row .neg-nm {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.02em;
}
.marketing-site .m-features .neg-row .neg-pnl {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.01em;
}
.marketing-site .m-features .neg-note {
  font-size: 12.5px;
  color: var(--m-ink-2);
  line-height: 1.55;
  letter-spacing: -0.005em;
}

/* ── 05 principles ── */
.marketing-site .m-features .idx-row { margin-bottom: 46px; }
.marketing-site .m-features .principles {
  display: grid;
  grid-template-columns: 5fr 7fr;
  gap: 64px;
  align-items: start;
}
.marketing-site .m-features .quote { position: sticky; top: 96px; }
.marketing-site .m-features .pull {
  font-family: var(--m-font-serif);
  font-style: italic;
  font-size: clamp(24px, 2.8vw, 36px);
  line-height: 1.3;
  letter-spacing: -0.01em;
  color: var(--m-ink);
  text-wrap: pretty;
}
.marketing-site .m-features .pull .mark {
  color: var(--m-accent);
  font-style: normal;
  font-family: var(--m-font-mono);
  font-size: 0.62em;
  vertical-align: 0.18em;
}
.marketing-site .m-features .pull .it { color: var(--m-accent); }
.marketing-site .m-features .pull-cite {
  margin-top: 26px;
  font-family: var(--m-font-mono);
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--m-ink-3);
  display: flex;
  align-items: center;
  gap: 10px;
}
.marketing-site .m-features .pull-cite::before {
  content: "";
  width: 28px;
  height: 1px;
  background: var(--m-accent);
}
.marketing-site .m-features .prin-list {
  display: flex;
  flex-direction: column;
  border-top: 1px solid var(--m-ink);
}
.marketing-site .m-features .prin {
  display: grid;
  grid-template-columns: 48px 1fr;
  gap: 20px;
  padding: 26px 0;
  border-bottom: 1px solid var(--m-line);
}
.marketing-site .m-features .prin .pno {
  font-size: 12px;
  color: var(--m-accent);
  letter-spacing: 0.04em;
  padding-top: 3px;
}
.marketing-site .m-features .prin h4 {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin-bottom: 7px;
}
.marketing-site .m-features .prin p {
  font-size: 14px;
  color: var(--m-ink-2);
  line-height: 1.6;
  letter-spacing: -0.005em;
  max-width: 56ch;
}

/* ── final cta ── */
.marketing-site .m-features .finalcta {
  background: var(--m-ink);
  color: var(--m-paper);
  border-radius: 4px;
  padding: clamp(44px, 6vw, 80px) clamp(28px, 5vw, 64px);
  margin-top: clamp(60px, 8vw, 112px);
  position: relative;
  overflow: hidden;
}
.marketing-site .m-features .finalcta .fc-grid {
  display: grid;
  grid-template-columns: 7fr 5fr;
  gap: 48px;
  align-items: end;
  position: relative;
  z-index: 2;
}
.marketing-site .m-features .finalcta h2 {
  font-size: clamp(32px, 4.4vw, 58px);
  line-height: 0.98;
  font-weight: 600;
  letter-spacing: -0.035em;
  text-wrap: balance;
}
.marketing-site .m-features .finalcta h2 .it { color: var(--m-paper); }
.marketing-site .m-features .finalcta .fc-sub {
  font-size: 16px;
  color: rgba(252, 252, 250, 0.62);
  line-height: 1.55;
  margin-bottom: 26px;
  letter-spacing: -0.01em;
}
.marketing-site .m-features .finalcta .m-btn-accent {
  font-size: 15px;
  padding: 13px 22px;
}
.marketing-site .m-features .finalcta .fc-fine {
  font-size: 11px;
  color: rgba(252, 252, 250, 0.45);
  letter-spacing: 0.03em;
  margin-top: 18px;
}
.marketing-site .m-features .fc-watermark {
  position: absolute;
  right: clamp(-12px, -1vw, 0px);
  bottom: clamp(-28px, -3vw, -12px);
  z-index: 1;
  pointer-events: none;
  user-select: none;
  line-height: 0.82;
  text-align: right;
}
.marketing-site .m-features .fc-watermark .fw-fig {
  font-weight: 500;
  font-size: clamp(110px, 20vw, 280px);
  letter-spacing: -0.04em;
  color: rgba(255, 77, 0, 0.085);
  display: block;
}
.marketing-site .m-features .fc-watermark .fw-fig .lt {
  font-family: var(--m-font-serif);
  font-style: italic;
  font-weight: 400;
}
.marketing-site .m-features .fc-watermark .fw-unit {
  font-weight: 500;
  font-size: clamp(20px, 3.2vw, 44px);
  letter-spacing: 0.04em;
  color: rgba(255, 77, 0, 0.1);
  display: block;
  margin-top: clamp(-18px, -1.4vw, -8px);
  padding-right: clamp(8px, 1vw, 18px);
}

/* ── reveal (progressive enhancement; visible by default) ── */
.marketing-site .m-features .rv { opacity: 1; }
@media (prefers-reduced-motion: no-preference) {
  .marketing-site .m-features .rv {
    opacity: 0;
    transform: translateY(14px);
    transition: opacity 0.7s cubic-bezier(0.2, 0.7, 0.2, 1),
      transform 0.7s cubic-bezier(0.2, 0.7, 0.2, 1);
  }
  .marketing-site .m-features .rv.in {
    opacity: 1;
    transform: none;
  }
}

/* ── responsive (breakpoint contract: ≤960 tablet · ≤640 mobile · ≤420 fine)
   All collapses stay nested under .marketing-site so the dark D1 console is
   never touched. Two-axis editorial grids fold to single column; 3-col data
   grids step 3 → 2 → 1; the 20+ param dt/dd rows stack on the finest tier so
   long mono values never force a horizontal scrollbar in either zh or en. ── */

/* ── ≤960 · tablet: two-axis editorial layouts fold; 3-col data → 2-col ── */
@media (max-width: 960px) {
  .marketing-site .m-features .fx-hero-grid,
  .marketing-site .m-features .sec-head,
  .marketing-site .m-features .attr,
  .marketing-site .m-features .principles,
  .marketing-site .m-features .finalcta .fc-grid {
    grid-template-columns: 1fr;
    gap: 32px;
  }
  /* sticky quote would float over its now-stacked list → pin it back in flow */
  .marketing-site .m-features .quote { position: static; }
  .marketing-site .m-features .src-grid,
  .marketing-site .m-features .eng-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  /* attribution card + side metrics share the now-single column, full width */
  .marketing-site .m-features .attr-side { gap: 24px; }
}

/* ── ≤640 · mobile: every multi-col grid collapses to a single column ── */
@media (max-width: 640px) {
  .marketing-site .m-features .src-grid,
  .marketing-site .m-features .eng-grid,
  .marketing-site .m-features .split,
  .marketing-site .m-features .metrics {
    grid-template-columns: 1fr;
  }
  /* equity-card footer: 4 mono metrics wrap to a 2×2 so they never clip */
  .marketing-site .m-features .cfoot { flex-wrap: wrap; }
  .marketing-site .m-features .cfoot .m {
    flex: 1 1 50%;
    border-bottom: 1px solid var(--m-line);
  }
  .marketing-site .m-features .cfoot .m:nth-child(2n) { border-right: 0; }
  /* egress-IP rows: account label drops to its own line above value/state */
  .marketing-site .m-features .ip-row {
    grid-template-columns: 1fr auto;
    row-gap: 4px;
  }
  .marketing-site .m-features .ip-acct { grid-column: 1 / -1; }
  /* hero / section copy a touch tighter so the giant clamp() titles breathe */
  .marketing-site .m-features .fx-hero-grid,
  .marketing-site .m-features .sec-head { gap: 26px; }
  .marketing-site .m-features .fx-hero-sub { max-width: none; }
}

/* ── ≤420 · fine: stack the dt/dd parameter rows + risk rows; trim the dark CTA
   block so the giant watermark figure can't push a horizontal scrollbar. ── */
@media (max-width: 420px) {
  /* 20+ copy-engine params: dt over dd, left-aligned, mono value wraps freely */
  .marketing-site .m-features .ef {
    flex-direction: column;
    align-items: flex-start;
    gap: 3px;
  }
  .marketing-site .m-features .ef dd {
    text-align: left;
    white-space: normal;
  }
  /* risk rows: control name over its value so 22ch cap never overflows */
  .marketing-site .m-features .risk-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }
  .marketing-site .m-features .rk-v {
    text-align: left;
    max-width: none;
  }
  /* equity-card footer steps from 2×2 to a single column on the narrowest tier */
  .marketing-site .m-features .cfoot .m {
    flex: 1 1 100%;
    border-right: 0;
  }
  /* tame the oversized final-CTA watermark so it stays inside the viewport */
  .marketing-site .m-features .fc-watermark .fw-fig { font-size: clamp(88px, 34vw, 130px); }
  .marketing-site .m-features .finalcta { padding-left: 22px; padding-right: 22px; }
}
</style>
