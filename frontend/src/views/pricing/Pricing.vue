<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { usePublicTraders } from '@/composables/usePublicTraders'
import type { Trader } from '@/api/traders'

const { t, locale } = useI18n()
const isZh = computed(() => locale.value === 'zh-CN')

/* ──────────────────────────────────────────────────────────────
   PRICING — INSTITUTIONAL CLARITY (light Swiss)
   Faithful translation of design/marketing/direction_clarity.html
   §04 / PRICING, expanded into a dedicated page. Scoped to
   .marketing-site so the dark D1 console is never touched.
   ────────────────────────────────────────────────────────────── */

/* ── number format: thousands separated by a thin space (brand rule) ── */
function group(n: number): string {
  const sign = n < 0 ? '−' : ''
  const abs = Math.abs(n)
  const [int, dec] = abs.toFixed(2).split('.')
  const spaced = int.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
  return `${sign}${spaced}.${dec}`
}
function groupInt(n: number): string {
  const sign = n < 0 ? '−' : ''
  const abs = Math.round(Math.abs(n))
  return sign + String(abs).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}
/* ROI %: leading +/− (U+2212 for negatives), grouped, trailing %, .00 trimmed */
function fmtRoi(n: number): string {
  const sign = n < 0 ? '−' : '+'
  return `${sign}${group(Math.abs(n)).replace(/\.00$/, '')}%`
}

/* ── comparison matrix (rows × 3 tiers) ─────────────────────────
   tiers: TRIAL (free 7d) · PRO ($80/MO, recommended inverted column)
   · INSTITUTIONAL (custom). Honest capability-by-capability rows. */
type Cell = { v: string; on?: boolean; off?: boolean; accent?: boolean }
interface MatrixRow {
  label: string
  trial: Cell
  pro: Cell
  inst: Cell
}

/* row keys map 1:1 to marketing.pricing.matrix.* ; presentation flags
   (on / off / accent) are visual state, not text — kept here, copy via t(). */
interface MatrixDef {
  key: string
  trial?: { on?: boolean; off?: boolean; accent?: boolean }
  pro?: { on?: boolean; off?: boolean; accent?: boolean }
  inst?: { on?: boolean; off?: boolean; accent?: boolean }
}
const matrixDefs: MatrixDef[] = [
  { key: 'accounts' },
  { key: 'slots' },
  { key: 'speed' },
  { key: 'egress', trial: { off: true }, pro: { on: true }, inst: { on: true } },
  { key: 'sources', pro: { on: true }, inst: { on: true } },
  { key: 'leadSeat', trial: { off: true }, pro: { off: true }, inst: { on: true } },
  { key: 'selfHost', trial: { off: true }, pro: { off: true }, inst: { on: true } },
  { key: 'riskEngine', inst: { on: true } },
  { key: 'sla', inst: { on: true } },
  { key: 'fee', trial: { accent: true }, pro: { accent: true }, inst: { accent: true } }
]
const matrix = computed<MatrixRow[]>(() =>
  matrixDefs.map((d) => ({
    label: t(`marketing.pricing.matrix.${d.key}.label`),
    trial: { v: t(`marketing.pricing.matrix.${d.key}.trial`), ...d.trial },
    pro: { v: t(`marketing.pricing.matrix.${d.key}.pro`), ...d.pro },
    inst: { v: t(`marketing.pricing.matrix.${d.key}.inst`), ...d.inst }
  }))
)

/* ── per-tier card model (mobile ≤640): same matrix data, re-projected
   column-wise into three stacked cards so the 3-tier comparison never
   needs a horizontal table on narrow screens. Text still via t() — these
   are the identical labels/values, just laid out per tier. ── */
type TierKey = 'trial' | 'pro' | 'inst'
interface TierFeature { label: string; cell: Cell }
interface TierCard {
  key: TierKey
  name: string
  price: string
  per?: string
  note: string
  recommend: boolean
  cta: string
  ctaAccent: boolean
  features: TierFeature[]
}
const tierCards = computed<TierCard[]>(() => {
  const cols: { key: TierKey; recommend: boolean; ctaAccent: boolean }[] = [
    { key: 'trial', recommend: false, ctaAccent: false },
    { key: 'pro', recommend: true, ctaAccent: true },
    { key: 'inst', recommend: false, ctaAccent: false }
  ]
  return cols.map((c) => ({
    key: c.key,
    name: t(`marketing.pricing.plans.${c.key}.name`),
    price:
      c.key === 'trial' ? '$0' : c.key === 'pro' ? '$80' : t('marketing.pricing.plans.inst.price'),
    per: c.key === 'pro' ? t('marketing.pricing.plans.pro.per') : undefined,
    note: t(`marketing.pricing.plans.${c.key}.note`),
    recommend: c.recommend,
    cta: t(`marketing.pricing.cta.${c.key}`),
    ctaAccent: c.ctaAccent,
    features: matrix.value.map((row): TierFeature => ({ label: row.label, cell: row[c.key] }))
  }))
})

/* ── invite / rebate strip (markers are data, text via t()) ── */
const strip = computed(() => [
  { marker: '0% FEE', text: t('marketing.pricing.strip.zeroFee') },
  { marker: '+10%', text: t('marketing.pricing.strip.rebate') },
  { marker: '½', text: t('marketing.pricing.strip.half') }
])

/* ── FAQ ── */
interface Faq { q: string; a: string }
const faqs = computed<Faq[]>(() =>
  ['q1', 'q2', 'q3', 'q4'].map((k) => ({
    q: t(`marketing.pricing.faq.${k}.q`),
    a: t(`marketing.pricing.faq.${k}.a`)
  }))
)
const openFaq = ref<number>(0)
function toggleFaq(i: number) {
  openFaq.value = openFaq.value === i ? -1 : i
}

/* ── illustrative "keep 100%" equity curve ──────────────────────
   Reuse the deterministic leader curve from mock data (茂茂大魔王),
   normalised to ROI %. Labelled ILLUSTRATIVE — honest, not a promise. */
const { traders } = usePublicTraders()
const lead = computed<Trader | undefined>(() => traders.value[0])
const headlineRoi = computed<number>(() => lead.value?.roi ?? 0)
const headlinePnl = computed<number>(() => lead.value?.total_pnl ?? 0)

/* honest negative-sample disclosure — derived from live data, not hardcoded.
   Prefer the brand-spec loss leader (MaximizeSR); fall back to the worst-ROI
   listed trader so the disclosure stays truthful even if live data shifts. */
const negSample = computed<Trader | undefined>(() => {
  const list = traders.value
  const named = list.find((tr) => tr.nickname === 'MaximizeSR')
  if (named) return named
  const losers = list.filter((tr) => tr.roi < 0)
  if (losers.length === 0) return undefined
  return losers.reduce((worst, tr) => (tr.roi < worst.roi ? tr : worst))
})

const chartEl = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

function buildChart() {
  const el = chartEl.value
  if (!el) return
  const raw = lead.value?.curve
  if (!raw || raw.length === 0) return
  // normalise the deterministic curve to a 0-based ROI %, ending at the
  // honest headline ROI so shape and label agree.
  const first = raw[0]
  const last = raw[raw.length - 1]
  const span = last - first || 1
  const data = raw.map((v) => {
    const t = (v - first) / span
    return +(t * headlineRoi.value).toFixed(2)
  })
  chart = echarts.init(el, undefined, { renderer: 'canvas' })
  chart.setOption({
    animation: true,
    animationDuration: 1200,
    animationEasing: 'cubicOut',
    grid: { left: 0, right: 0, top: 6, bottom: 0 },
    xAxis: {
      type: 'category',
      show: false,
      boundaryGap: false,
      data: data.map((_, i) => i)
    },
    yAxis: { type: 'value', show: false, scale: true },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#14161A',
      borderColor: '#14161A',
      borderWidth: 0,
      padding: [7, 11],
      textStyle: { color: '#FCFCFA', fontFamily: 'Geist Mono, monospace', fontSize: 11 },
      formatter: (p: unknown) => {
        const arr = p as Array<{ value: number }>
        return 'ROI  +' + group(arr[0].value).replace(/\.00$/, '') + '%'
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

function onResize() {
  chart?.resize()
}

/* ── reveal on scroll (progressive enhancement; content visible by default) ── */
const reduceMotion = ref(false)
let io: IntersectionObserver | undefined
let failsafe: ReturnType<typeof setTimeout> | undefined

onMounted(async () => {
  await nextTick()
  buildChart()
  window.addEventListener('resize', onResize, { passive: true })

  reduceMotion.value = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if ('IntersectionObserver' in window && !reduceMotion.value) {
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
    document.querySelectorAll('.marketing-site .rv').forEach((el) => io?.observe(el))
    // failsafe: reveal everything after 2.6s no matter what
    failsafe = setTimeout(() => {
      document.querySelectorAll('.marketing-site .rv').forEach((el) => el.classList.add('in'))
    }, 2600)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
  chart = null
  io?.disconnect()
  if (failsafe) clearTimeout(failsafe)
})
</script>

<template>
  <!-- root carries .marketing-site so the light Swiss theme + --m-* tokens
       cascade into this page even though MarketingLayout already wraps it. -->
  <div class="marketing-site pricing-page" :class="{ 'lang-zh': isZh }">
    <!-- ░░ HEADER ░░ -->
    <section class="m-wrap sec-head rv">
      <div>
        <div class="sec-idx">{{ t('marketing.pricing.head.idx') }}</div>
        <h2>{{ t('marketing.pricing.head.titleLine1') }}<br /><span class="it">{{ t('marketing.pricing.head.titleLine2') }}</span></h2>
      </div>
      <p class="right">
        {{ t('marketing.pricing.head.rightLead') }}<span class="ink">{{ t('marketing.pricing.head.rightInk') }}</span>{{ t('marketing.pricing.head.rightTail') }}
      </p>
    </section>

    <!-- ░░ COMPARISON MATRIX ░░ -->
    <section class="m-wrap matrix-wrap rv">
      <div class="pricing-table">
        <!-- column heads -->
        <div class="pricing-row head-row">
          <div class="pcell rowlabel blank"></div>
          <div class="pcol-head">
            <div class="pname">{{ t('marketing.pricing.plans.trial.name') }}</div>
            <div class="pprice m-num">$0</div>
            <div class="pnote">{{ t('marketing.pricing.plans.trial.note') }}</div>
          </div>
          <div class="pcol-head recommend">
            <div class="pname">{{ t('marketing.pricing.plans.pro.name') }}</div>
            <div class="pprice m-num">$80<span class="per">{{ t('marketing.pricing.plans.pro.per') }}</span></div>
            <div class="pnote">{{ t('marketing.pricing.plans.pro.note') }}</div>
          </div>
          <div class="pcol-head">
            <div class="pname">{{ t('marketing.pricing.plans.inst.name') }}</div>
            <div class="pprice">{{ t('marketing.pricing.plans.inst.price') }}</div>
            <div class="pnote">{{ t('marketing.pricing.plans.inst.note') }}</div>
          </div>
        </div>

        <!-- capability rows -->
        <div v-for="row in matrix" :key="row.label" class="pricing-row">
          <div class="pcell rowlabel">{{ row.label }}</div>
          <div
            class="pcell"
            :class="{ 'feat-on': row.trial.on, 'feat-off': row.trial.off, accent: row.trial.accent }"
          >
            {{ row.trial.v }}
          </div>
          <div
            class="pcell"
            :class="{ 'feat-on': row.pro.on, 'feat-off': row.pro.off, accent: row.pro.accent }"
          >
            {{ row.pro.v }}
          </div>
          <div
            class="pcell"
            :class="{ 'feat-on': row.inst.on, 'feat-off': row.inst.off, accent: row.inst.accent }"
          >
            {{ row.inst.v }}
          </div>
        </div>

        <!-- CTA foot -->
        <div class="pricing-row foot-row">
          <div class="pcell rowlabel blank"></div>
          <div class="pcell cta">
            <router-link class="m-btn-2 ghost" to="/register">{{ t('marketing.pricing.cta.trial') }}</router-link>
          </div>
          <div class="pcell cta">
            <router-link class="m-btn-2 accent" to="/register"
              >{{ t('marketing.pricing.cta.pro') }} <span class="arw">→</span></router-link
            >
          </div>
          <div class="pcell cta">
            <router-link class="m-btn-2 ghost" to="/register">{{ t('marketing.pricing.cta.inst') }}</router-link>
          </div>
        </div>
      </div>

      <!-- mobile-only: same data re-projected into per-tier stacked cards
           (no horizontal table / scroll on narrow screens) -->
      <div class="pricing-cards" aria-hidden="false">
        <div
          v-for="card in tierCards"
          :key="card.key"
          class="ptier"
          :class="{ recommend: card.recommend }"
        >
          <div class="ptier-head">
            <div class="ptier-name">{{ card.name }}</div>
            <div class="ptier-price m-num">
              {{ card.price }}<span v-if="card.per" class="per">{{ card.per }}</span>
            </div>
            <div class="ptier-note">{{ card.note }}</div>
          </div>
          <dl class="ptier-feats">
            <div v-for="f in card.features" :key="f.label" class="ptier-feat">
              <dt>{{ f.label }}</dt>
              <dd
                :class="{ 'feat-on': f.cell.on, 'feat-off': f.cell.off, accent: f.cell.accent }"
              >
                {{ f.cell.v }}
              </dd>
            </div>
          </dl>
          <router-link
            class="m-btn-2"
            :class="card.ctaAccent ? 'accent' : 'ghost'"
            to="/register"
          >
            {{ card.cta }}<span v-if="card.ctaAccent" class="arw"> →</span>
          </router-link>
        </div>
      </div>

      <!-- invite / rebate strip -->
      <div class="pricing-strip">
        <div v-for="item in strip" :key="item.marker" class="pi">
          <span class="marker m-num">{{ item.marker }}</span> {{ item.text }}
        </div>
      </div>
    </section>

    <!-- ░░ ZERO-FEE VALUE PANEL ░░ -->
    <section class="m-wrap section value-wrap rv">
      <div class="value-grid">
        <div class="value-quote">
          <p class="pull">
            <span class="mark">“</span>{{ t('marketing.pricing.value.quoteLead') }}<span class="it accent">{{ t('marketing.pricing.value.quoteAccent') }}</span>{{ t('marketing.pricing.value.quoteTail') }}<span class="mark">”</span>
          </p>
          <div class="pull-cite">{{ t('marketing.pricing.value.cite') }}</div>
        </div>

        <div class="value-card" v-if="lead">
          <div class="vc-head">
            <div class="who">
              <span class="nm" lang="zh">{{ lead.nickname }}</span>
              <span class="ex">OKX · 币Coin</span>
            </div>
            <span class="pnl m-num m-pos">+{{ group(headlinePnl) }}</span>
          </div>
          <div class="vc-sub">
            <span>{{ t('marketing.pricing.value.cardRoiUsdt') }}</span>
            <span>{{ groupInt(lead.enrolled_days) }} {{ t('marketing.pricing.value.cardDaysLive') }}</span>
            <span class="illu">{{ t('marketing.pricing.value.cardIllustrative') }}</span>
          </div>
          <div ref="chartEl" class="vc-chart"></div>
          <div class="vc-foot">
            <div class="m">
              <div class="ml">{{ t('marketing.pricing.value.footHeadlineRoi') }}</div>
              <div class="mv m-num m-pos">+{{ group(headlineRoi).replace(/\.00$/, '') }}%</div>
            </div>
            <div class="m">
              <div class="ml">{{ t('marketing.pricing.value.footFee') }}</div>
              <div class="mv m-num accent">0%</div>
            </div>
            <div class="m">
              <div class="ml">{{ t('marketing.pricing.value.footKeep') }}</div>
              <div class="mv m-num">100%</div>
            </div>
          </div>
        </div>
      </div>

      <!-- honest negative-sample disclosure line (derived from live data) -->
      <p class="honest-note" v-if="negSample">
        {{ t('marketing.pricing.value.honestLead') }}
        <span class="m-num m-neg">{{ negSample.nickname }} {{ fmtRoi(negSample.roi) }}</span> {{ t('marketing.pricing.value.honestSample') }}<span class="ink">{{ t('marketing.pricing.value.honestInk') }}</span>{{ t('marketing.pricing.value.honestTail') }}
      </p>
    </section>

    <!-- ░░ FAQ ░░ -->
    <section class="m-wrap section faq-wrap rv">
      <div class="sec-head">
        <div>
          <div class="sec-idx">{{ t('marketing.pricing.faq.idx') }}</div>
          <h2>{{ t('marketing.pricing.faq.titleLine1') }}<br /><span class="it">{{ t('marketing.pricing.faq.titleLine2') }}</span></h2>
        </div>
        <p class="right">
          {{ t('marketing.pricing.faq.right') }}
        </p>
      </div>

      <div class="faq-list">
        <div
          v-for="(f, i) in faqs"
          :key="f.q"
          class="faq"
          :class="{ open: openFaq === i }"
        >
          <button class="faq-q m-mono-ctrl" type="button" @click="toggleFaq(i)">
            <span class="qno m-num">{{ String(i + 1).padStart(2, '0') }}</span>
            <span class="qt">{{ f.q }}</span>
            <span class="qx" aria-hidden="true">{{ openFaq === i ? '−' : '+' }}</span>
          </button>
          <div v-show="openFaq === i" class="faq-a">
            <p>{{ f.a }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ░░ FINAL CTA ░░ -->
    <section class="m-wrap">
      <div class="finalcta rv">
        <div class="fc-watermark" aria-hidden="true">
          <span class="fw-fig">0<span class="lt">%</span></span>
          <span class="fw-unit">PERFORMANCE FEE</span>
        </div>
        <div class="fc-grid">
          <div>
            <h2>{{ t('marketing.pricing.final.titleLine1') }}<br /><span class="it">{{ t('marketing.pricing.final.titleLine2') }}</span> <span class="mark">{{ t('marketing.pricing.final.titleMark') }}</span></h2>
          </div>
          <div>
            <p class="fc-sub">
              {{ t('marketing.pricing.final.sub') }}
            </p>
            <router-link class="m-btn-2 accent big" to="/register"
              >{{ t('marketing.pricing.final.cta') }} <span class="arw">→</span></router-link
            >
            <div class="fc-fine">{{ t('marketing.pricing.final.fine') }}</div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* All selectors nested under .marketing-site so light Swiss styling
   never reaches the dark D1 console, and wins over global.css. */

.marketing-site.pricing-page {
  padding-top: clamp(40px, 5vw, 72px);
  padding-bottom: clamp(48px, 6vw, 80px);
}

/* local re-declaration of layout helpers (scoped CSS doesn't pierce SFC boundary) */
.marketing-site .m-wrap {
  max-width: var(--m-maxw);
  margin: 0 auto;
  padding-left: var(--m-pad);
  padding-right: var(--m-pad);
}
.marketing-site .ink { color: var(--m-ink); }
.marketing-site .accent { color: var(--m-accent); }

/* ── section header ── */
.marketing-site .sec-head {
  display: grid;
  grid-template-columns: 7fr 5fr;
  gap: 40px;
  align-items: end;
  margin-bottom: 46px;
}
.marketing-site .sec-idx {
  font-family: var(--m-font-mono);
  font-size: 11px;
  color: var(--m-accent);
  letter-spacing: 0.1em;
  margin-bottom: 18px;
}
.marketing-site .sec-head h2 {
  font-size: clamp(30px, 3.6vw, 46px);
  line-height: 1.02;
  font-weight: 600;
  letter-spacing: -0.03em;
  text-wrap: balance;
}
.marketing-site .sec-head h2 .it {
  font-family: var(--m-font-serif);
  font-style: italic;
  font-weight: 400;
}
.marketing-site .sec-head .right {
  font-size: 15px;
  color: var(--m-ink-2);
  line-height: 1.55;
  letter-spacing: -0.01em;
  padding-bottom: 4px;
}
.marketing-site .section { padding-top: clamp(64px, 8vw, 118px); }

/* ── shared button (local; layout's .m-btn is scoped to the layout) ── */
.marketing-site .m-btn-2 {
  font-family: var(--m-font-display) !important;
  font-size: 13.5px;
  font-weight: 500;
  letter-spacing: -0.01em;
  padding: 9px 17px;
  border: 1px solid var(--m-ink);
  background: var(--m-ink);
  color: var(--m-paper);
  cursor: pointer;
  border-radius: var(--m-radius);
  transition: background 0.15s, color 0.15s, border-color 0.15s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  white-space: nowrap;
}
.marketing-site .m-btn-2 .arw { font-family: var(--m-font-mono); font-weight: 400; }
.marketing-site .m-btn-2.ghost {
  background: transparent;
  color: var(--m-ink);
  border: 1px solid var(--m-line-strong);
}
.marketing-site .m-btn-2.ghost:hover {
  background: var(--m-ink);
  color: var(--m-paper);
  border-color: var(--m-ink);
}
.marketing-site .m-btn-2.accent {
  background: var(--m-accent);
  border-color: var(--m-accent);
  color: var(--m-paper);
}
.marketing-site .m-btn-2.accent:hover {
  background: var(--m-ink);
  border-color: var(--m-ink);
}
.marketing-site .m-btn-2.big { font-size: 15px; padding: 13px 22px; }

/* ── pricing matrix ── */
.marketing-site .pricing-table {
  border-top: 1px solid var(--m-ink);
  border-left: 1px solid var(--m-line);
}
.marketing-site .pricing-row {
  display: grid;
  grid-template-columns: 1.4fr 1fr 1fr 1fr;
  border-bottom: 1px solid var(--m-line);
}
.marketing-site .pcell {
  padding: 18px 22px;
  border-right: 1px solid var(--m-line);
  display: flex;
  flex-direction: column;
  justify-content: center;
  font-size: 14.5px;
  letter-spacing: -0.01em;
  color: var(--m-ink);
}
.marketing-site .pcell.rowlabel {
  font-family: var(--m-font-mono);
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--m-ink-3);
  background: var(--m-paper-2);
}
.marketing-site .pcell.rowlabel.blank { background: var(--m-paper); }
.marketing-site .pcell.feat-on { color: var(--m-ink); font-weight: 500; }
.marketing-site .pcell.feat-off { color: var(--m-ink-4); }
.marketing-site .pcell.accent {
  color: var(--m-accent);
  font-weight: 500;
  font-family: var(--m-font-mono);
  font-variant-numeric: tabular-nums;
}

.marketing-site .head-row .pcol-head { padding: 26px 22px 24px; border-right: 1px solid var(--m-line); }
.marketing-site .head-row .pcol-head.recommend { background: var(--m-ink); color: var(--m-paper); }
.marketing-site .pcol-head .pname {
  font-family: var(--m-font-mono);
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--m-ink-3);
  margin-bottom: 14px;
}
.marketing-site .pcol-head.recommend .pname { color: var(--m-accent); }
.marketing-site .pcol-head .pprice {
  font-family: var(--m-font-mono);
  font-size: 34px;
  font-weight: 600;
  letter-spacing: -0.03em;
  line-height: 1;
  display: flex;
  align-items: baseline;
  gap: 3px;
  font-variant-numeric: tabular-nums;
}
.marketing-site .pcol-head .pprice .per {
  font-size: 12px;
  color: var(--m-ink-3);
  font-weight: 500;
  letter-spacing: 0.04em;
}
.marketing-site .pcol-head.recommend .pprice .per { color: var(--m-ink-4); }
.marketing-site .pcol-head .pnote {
  font-size: 13px;
  color: var(--m-ink-2);
  margin-top: 11px;
  letter-spacing: -0.01em;
  line-height: 1.4;
}
.marketing-site .pcol-head.recommend .pnote { color: var(--m-ink-4); }

.marketing-site .foot-row .pcell.cta { padding: 18px 22px; }
.marketing-site .foot-row .pcell.cta .m-btn-2 { width: 100%; }

/* ── mobile per-tier cards (hidden on desktop, shown ≤640) ── */
.marketing-site .pricing-cards { display: none; }
.marketing-site .ptier {
  border: 1px solid var(--m-line);
  border-radius: var(--m-radius);
  background: var(--m-paper);
  padding: 20px 18px 22px;
  margin-bottom: 16px;
}
.marketing-site .ptier:last-child { margin-bottom: 0; }
.marketing-site .ptier.recommend {
  border-color: var(--m-ink);
  box-shadow: 0 0 0 1px var(--m-ink);
}
.marketing-site .ptier-name {
  font-family: var(--m-font-mono);
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--m-ink-3);
}
.marketing-site .ptier.recommend .ptier-name { color: var(--m-accent); }
.marketing-site .ptier-price {
  font-family: var(--m-font-mono);
  font-size: 32px;
  font-weight: 600;
  letter-spacing: -0.03em;
  line-height: 1;
  margin-top: 10px;
  display: flex;
  align-items: baseline;
  gap: 3px;
  font-variant-numeric: tabular-nums;
  color: var(--m-ink);
}
.marketing-site .ptier-price .per {
  font-size: 12px;
  color: var(--m-ink-3);
  font-weight: 500;
  letter-spacing: 0.04em;
}
.marketing-site .ptier-note {
  font-size: 13px;
  color: var(--m-ink-2);
  margin-top: 9px;
  line-height: 1.4;
  letter-spacing: -0.01em;
}
.marketing-site .ptier-feats {
  margin: 16px 0 18px;
  border-top: 1px solid var(--m-line);
}
.marketing-site .ptier-feat {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: baseline;
  gap: 14px;
  padding: 11px 0;
  border-bottom: 1px solid var(--m-line);
}
.marketing-site .ptier-feat dt {
  font-family: var(--m-font-mono);
  font-size: 10px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--m-ink-3);
  line-height: 1.4;
}
.marketing-site .ptier-feat dd {
  margin: 0;
  font-size: 13.5px;
  letter-spacing: -0.01em;
  color: var(--m-ink);
  text-align: right;
}
.marketing-site .ptier-feat dd.feat-on { font-weight: 500; }
.marketing-site .ptier-feat dd.feat-off { color: var(--m-ink-4); }
.marketing-site .ptier-feat dd.accent {
  color: var(--m-accent);
  font-weight: 500;
  font-family: var(--m-font-mono);
  font-variant-numeric: tabular-nums;
}
.marketing-site .ptier > .m-btn-2 { width: 100%; }

/* ── invite / rebate strip ── */
.marketing-site .pricing-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 24px;
  padding: 18px 22px;
  border: 1px solid var(--m-line);
  border-radius: var(--m-radius);
  background: var(--m-paper-2);
}
.marketing-site .pricing-strip .pi {
  display: flex;
  align-items: center;
  gap: 11px;
  font-size: 13.5px;
  color: var(--m-ink-2);
  letter-spacing: -0.01em;
}
.marketing-site .pricing-strip .pi .marker {
  font-size: 11px;
  color: var(--m-accent);
  border: 1px solid var(--m-accent);
  border-radius: 999px;
  padding: 2px 8px;
  letter-spacing: 0.04em;
  white-space: nowrap;
  flex: none;
}

/* ── zero-fee value panel ── */
.marketing-site .value-grid {
  display: grid;
  grid-template-columns: 5fr 7fr;
  gap: 64px;
  align-items: start;
}
.marketing-site .value-quote { position: sticky; top: 96px; }
.marketing-site .pull {
  font-family: var(--m-font-serif);
  font-style: italic;
  font-size: clamp(24px, 2.7vw, 34px);
  line-height: 1.28;
  letter-spacing: -0.01em;
  color: var(--m-ink);
  text-wrap: pretty;
}
.marketing-site .pull .mark {
  color: var(--m-accent);
  font-style: normal;
  font-family: var(--m-font-mono);
  font-size: 0.62em;
  vertical-align: 0.18em;
}
.marketing-site .pull .it { font-style: italic; }
.marketing-site .pull .it.accent { color: var(--m-accent); }
.marketing-site .pull-cite {
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
.marketing-site .pull-cite::before {
  content: "";
  width: 28px;
  height: 1px;
  background: var(--m-accent);
}

.marketing-site .value-card {
  border: 1px solid var(--m-line);
  border-radius: 3px;
  background: var(--m-paper);
  overflow: hidden;
}
.marketing-site .vc-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 16px 18px 6px;
  gap: 12px;
}
.marketing-site .vc-head .who { display: flex; align-items: baseline; gap: 9px; flex-wrap: wrap; }
.marketing-site .vc-head .who .nm { font-weight: 600; font-size: 15px; letter-spacing: -0.01em; }
.marketing-site .vc-head .who .ex {
  font-family: var(--m-font-mono);
  font-size: 10px;
  color: var(--m-ink-3);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.marketing-site .vc-head .pnl { font-size: 17px; font-weight: 600; letter-spacing: -0.01em; }
.marketing-site .vc-sub {
  padding: 0 18px 8px;
  font-family: var(--m-font-mono);
  font-size: 10px;
  color: var(--m-ink-3);
  letter-spacing: 0.03em;
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.marketing-site .vc-sub .illu { color: var(--m-ink-4); }
.marketing-site .vc-chart { width: 100%; height: 200px; }
.marketing-site .vc-foot { display: flex; border-top: 1px solid var(--m-line); }
.marketing-site .vc-foot .m {
  flex: 1;
  padding: 12px 18px;
  border-right: 1px solid var(--m-line);
}
.marketing-site .vc-foot .m:last-child { border-right: 0; }
.marketing-site .vc-foot .m .ml {
  font-family: var(--m-font-mono);
  font-size: 9px;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--m-ink-3);
}
.marketing-site .vc-foot .m .mv { font-size: 14px; font-weight: 500; margin-top: 4px; }
.marketing-site .vc-foot .m .mv.accent { color: var(--m-accent); }

.marketing-site .honest-note {
  margin-top: 28px;
  font-size: 13px;
  color: var(--m-ink-3);
  line-height: 1.6;
  max-width: 78ch;
  letter-spacing: -0.005em;
}

/* ── FAQ ── */
.marketing-site .faq-list {
  border-top: 1px solid var(--m-ink);
}
.marketing-site .faq { border-bottom: 1px solid var(--m-line); }
.marketing-site .faq-q {
  width: 100%;
  display: grid;
  grid-template-columns: 48px 1fr 24px;
  align-items: center;
  gap: 18px;
  padding: 24px 0;
  background: none;
  border: 0;
  text-align: left;
  cursor: pointer;
  color: var(--m-ink);
  transition: color 0.15s;
}
.marketing-site .faq-q:hover { color: var(--m-accent); }
.marketing-site .faq-q .qno {
  font-size: 12px;
  color: var(--m-accent);
  letter-spacing: 0.04em;
}
.marketing-site .faq-q .qt {
  font-family: var(--m-font-display);
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.02em;
}
.marketing-site .faq-q .qx {
  font-family: var(--m-font-mono);
  font-size: 20px;
  color: var(--m-ink-3);
  text-align: right;
  font-weight: 400;
}
.marketing-site .faq.open .faq-q .qx { color: var(--m-accent); }
.marketing-site .faq-a { padding: 0 0 26px 66px; }
.marketing-site .faq-a p {
  font-size: 14.5px;
  color: var(--m-ink-2);
  line-height: 1.62;
  letter-spacing: -0.005em;
  max-width: 64ch;
  text-wrap: pretty;
}

/* ── final cta ── */
.marketing-site .finalcta {
  background: var(--m-ink);
  color: var(--m-paper);
  border-radius: 4px;
  padding: clamp(48px, 6vw, 84px) clamp(28px, 4vw, 64px);
  margin-top: clamp(64px, 8vw, 118px);
  position: relative;
  overflow: hidden;
}
.marketing-site .finalcta .fc-grid {
  display: grid;
  grid-template-columns: 7fr 5fr;
  gap: 48px;
  align-items: end;
  position: relative;
  z-index: 2;
}
.marketing-site .finalcta h2 {
  font-size: clamp(34px, 4.6vw, 62px);
  line-height: 0.98;
  font-weight: 600;
  letter-spacing: -0.035em;
  text-wrap: balance;
}
.marketing-site .finalcta h2 .it {
  font-family: var(--m-font-serif);
  font-style: italic;
  font-weight: 400;
}
.marketing-site .finalcta h2 .mark { color: var(--m-accent); }
.marketing-site .finalcta .fc-sub {
  font-size: 16px;
  color: rgba(252, 252, 250, 0.62);
  line-height: 1.55;
  margin-bottom: 26px;
  letter-spacing: -0.01em;
  text-wrap: pretty;
}
.marketing-site .finalcta .fc-fine {
  font-family: var(--m-font-mono);
  font-size: 11px;
  color: rgba(252, 252, 250, 0.45);
  letter-spacing: 0.03em;
  margin-top: 18px;
}
.marketing-site .fc-watermark {
  position: absolute;
  right: clamp(-12px, -1vw, 0px);
  bottom: clamp(-28px, -3vw, -12px);
  z-index: 1;
  pointer-events: none;
  user-select: none;
  line-height: 0.82;
  text-align: right;
}
.marketing-site .fc-watermark .fw-fig {
  font-family: var(--m-font-mono);
  font-weight: 500;
  font-size: clamp(120px, 21vw, 300px);
  letter-spacing: -0.04em;
  color: rgba(255, 77, 0, 0.085);
  display: block;
}
.marketing-site .fc-watermark .fw-fig .lt {
  font-family: var(--m-font-serif);
  font-style: italic;
  font-weight: 400;
}
.marketing-site .fc-watermark .fw-unit {
  font-family: var(--m-font-mono);
  font-weight: 500;
  font-size: clamp(20px, 3vw, 42px);
  letter-spacing: 0.04em;
  color: rgba(255, 77, 0, 0.1);
  display: block;
  margin-top: clamp(-18px, -1.4vw, -8px);
  padding-right: clamp(8px, 1vw, 18px);
}

/* ── CJK italic discipline ──────────────────────────────────────
   Newsreader/Songti faux-italic on CJK glyphs looks off. In zh mode
   we drop the slant on serif-italic emphasis spans and lean on the
   accent colour + weight instead — same editorial emphasis, clean
   CJK rendering. Latin terms (e.g. "alpha") are unaffected because
   they sit in their own .it span and the page only flags zh here. */
.marketing-site.lang-zh .sec-head h2 .it {
  font-style: normal;
  color: var(--m-accent);
  font-weight: 600;
}
.marketing-site.lang-zh .pull {
  font-style: normal;
}
.marketing-site.lang-zh .pull .it.accent {
  font-style: normal;
  font-weight: 600;
}

/* ── reveal (progressive enhancement — visible by default) ── */
.marketing-site .rv { opacity: 1; }
@media (prefers-reduced-motion: no-preference) {
  .marketing-site .rv {
    opacity: 0;
    transform: translateY(14px);
    transition: opacity 0.7s cubic-bezier(0.2, 0.7, 0.2, 1), transform 0.7s cubic-bezier(0.2, 0.7, 0.2, 1);
  }
  .marketing-site .rv.in { opacity: 1; transform: none; }
}

/* ── responsive (breakpoint contract: tablet ≤960 · mobile ≤640 · fine ≤420)
   Page-stage giant titles already use clamp() (sec-head h2, pull, finalcta h2,
   fc-watermark) — fluid by default, no re-touch needed. Goal at every step:
   no horizontal scrollbar, no overflow / overlap / truncation, in zh and en. ── */

/* ── tablet ≤960: two-up editorial grids collapse to a single column;
   the matrix table tightens but stays a readable 4-col grid. ── */
@media (max-width: 960px) {
  .marketing-site .sec-head,
  .marketing-site .value-grid,
  .marketing-site .finalcta .fc-grid {
    grid-template-columns: 1fr;
    gap: 36px;
  }
  .marketing-site .value-quote { position: static; }
  .marketing-site .pricing-row { grid-template-columns: 1.3fr 1fr 1fr 1fr; }
  .marketing-site .pcell { padding: 14px 14px; font-size: 13px; }
  .marketing-site .pcell.rowlabel { font-size: 10px; letter-spacing: 0.04em; }
  .marketing-site .head-row .pcol-head { padding: 18px 14px; }
  .marketing-site .pcol-head .pprice { font-size: 26px; }
  .marketing-site .pcol-head .pnote { display: none; }
  .marketing-site .foot-row .pcell.cta { padding: 14px; }
  .marketing-site .foot-row .pcell.cta .m-btn-2 {
    font-size: 11.5px;
    padding: 8px 8px;
    gap: 4px;
  }
}

/* ── mobile ≤640: the 3-tier comparison can no longer fit a horizontal
   table without cramping — swap the table for per-tier stacked cards.
   FAQ / strip / value-card reflow; chart shrinks. ── */
@media (max-width: 640px) {
  .marketing-site .pricing-table { display: none; }
  .marketing-site .pricing-cards { display: block; }

  /* strip reads as a stacked list, not a wrapping row */
  .marketing-site .pricing-strip {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 16px 16px;
  }
  .marketing-site .pricing-strip .pi { font-size: 13px; }

  /* value card: chart shorter, footer metrics stack 3→1 cleanly */
  .marketing-site .vc-chart { height: 160px; }
  .marketing-site .vc-foot .m { padding: 11px 14px; }

  /* FAQ: tighter index column so long questions don't overflow */
  .marketing-site .faq-q {
    grid-template-columns: 30px 1fr 22px;
    gap: 10px;
    padding: 20px 0;
  }
  .marketing-site .faq-q .qt { font-size: 15px; }
  .marketing-site .faq-a { padding-left: 40px; padding-bottom: 22px; }

  .marketing-site .honest-note { font-size: 12.5px; }
}

/* ── fine ≤420: trim card chrome so nothing overflows on the narrowest
   phones; metrics footer may wrap to two rows without breaking. ── */
@media (max-width: 420px) {
  .marketing-site.pricing-page { padding-top: clamp(28px, 8vw, 40px); }
  .marketing-site .ptier { padding: 18px 15px 20px; }
  .marketing-site .ptier-price { font-size: 28px; }
  .marketing-site .ptier-feat { gap: 10px; }
  .marketing-site .ptier-feat dt { font-size: 9.5px; }
  .marketing-site .ptier-feat dd { font-size: 13px; }

  /* footer metrics: allow 3 narrow cells to wrap rather than squeeze */
  .marketing-site .vc-foot { flex-wrap: wrap; }
  .marketing-site .vc-foot .m {
    flex: 1 1 33%;
    min-width: 33%;
    padding: 10px 12px;
  }

  .marketing-site .pull-cite { flex-wrap: wrap; }
  .marketing-site .faq-q { grid-template-columns: 26px 1fr 20px; gap: 8px; }
  .marketing-site .faq-a { padding-left: 34px; }
}
</style>
