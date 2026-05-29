<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { setLocale } from '@/i18n'

/* ── i18n: global scope (no local messages) ── */
const { t, locale } = useI18n()

/* ── scroll state: nav gains hairline + faint backing once scrolled ── */
const scrolled = ref(false)
function onScroll() {
  scrolled.value = window.scrollY > 8
}

/* ── live UTC clock (footer meta) ── */
const utc = ref('UTC 0000-00-00 00:00:00')
let clockTimer: ReturnType<typeof setInterval> | undefined
function tick() {
  const d = new Date()
  const p = (n: number, w = 2) => String(n).padStart(w, '0')
  utc.value =
    `UTC ${d.getUTCFullYear()}-${p(d.getUTCMonth() + 1)}-${p(d.getUTCDate())} ` +
    `${p(d.getUTCHours())}:${p(d.getUTCMinutes())}:${p(d.getUTCSeconds())}`
}

onMounted(() => {
  onScroll()
  window.addEventListener('scroll', onScroll, { passive: true })
  tick()
  clockTimer = setInterval(tick, 1000)
})
onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
  if (clockTimer) clearInterval(clockTimer)
})
</script>

<template>
  <div class="marketing-site">
    <!-- ░░ NAV ░░ -->
    <nav class="m-nav" :class="{ scrolled }">
      <div class="m-wrap m-nav-inner">
        <router-link class="m-wordmark" to="/">
          <span class="glyph"></span>
          <span>Copy&nbsp;Trader</span>
          <span class="sub">/ exec layer</span>
        </router-link>

        <div class="m-nav-links">
          <router-link to="/features">{{ t('marketing.layout.nav.features') }}</router-link>
          <router-link to="/#traders">{{ t('marketing.layout.nav.traders') }}</router-link>
          <router-link to="/pricing">{{ t('marketing.layout.nav.pricing') }}</router-link>
          <router-link to="/tutorial">{{ t('marketing.layout.nav.docs') }}</router-link>
        </div>

        <div class="m-nav-cta">
          <!-- ░ language switcher ░ -->
          <div class="m-lang" role="group" :aria-label="t('marketing.layout.lang.label')">
            <button
              type="button"
              class="m-lang-opt"
              :class="{ active: locale === 'zh-CN' }"
              :aria-pressed="locale === 'zh-CN'"
              @click="setLocale('zh-CN')"
            >{{ t('marketing.layout.lang.zh') }}</button>
            <span class="m-lang-sep">/</span>
            <button
              type="button"
              class="m-lang-opt"
              :class="{ active: locale === 'en' }"
              :aria-pressed="locale === 'en'"
              @click="setLocale('en')"
            >{{ t('marketing.layout.lang.en') }}</button>
          </div>

          <router-link class="console" to="/console">{{ t('marketing.layout.nav.console') }}</router-link>
          <router-link class="login" to="/login">{{ t('marketing.layout.nav.login') }}</router-link>
          <router-link class="m-btn m-btn-accent" to="/register">
            {{ t('marketing.layout.nav.cta') }} <span class="arw">→</span>
          </router-link>
        </div>
      </div>
    </nav>

    <main class="m-main">
      <router-view />
    </main>

    <!-- ░░ FOOTER ░░ -->
    <footer class="m-wrap m-footer">
      <div class="foot-top">
        <div class="foot-brand">
          <router-link class="m-wordmark" to="/">
            <span class="glyph"></span><span>Copy Trader</span>
          </router-link>
          <div class="foot-status">
            <div class="st"><span class="dot"></span><b>{{ t('marketing.layout.footer.status.operational') }}</b> · {{ t('marketing.layout.footer.status.operationalSuffix') }}</div>
            <div class="st"><span class="dot"></span>{{ t('marketing.layout.footer.status.latency') }} · <b>1.8 ms</b> {{ t('marketing.layout.footer.status.latencyUnit') }}</div>
            <div class="st"><span class="dot amber"></span>{{ t('marketing.layout.footer.status.subscribers') }} · <b>1 247</b> {{ t('marketing.layout.footer.status.subscribersUnit') }}</div>
          </div>
        </div>

        <div class="foot-col">
          <h5>{{ t('marketing.layout.footer.product.title') }}</h5>
          <router-link to="/features">{{ t('marketing.layout.footer.product.features') }}</router-link>
          <router-link to="/#traders">{{ t('marketing.layout.footer.product.leaderboard') }}</router-link>
          <router-link to="/pricing">{{ t('marketing.layout.footer.product.pricing') }}</router-link>
          <router-link to="/console">{{ t('marketing.layout.footer.product.console') }}</router-link>
        </div>

        <div class="foot-col">
          <h5>{{ t('marketing.layout.footer.resources.title') }}</h5>
          <router-link to="/tutorial">{{ t('marketing.layout.footer.resources.documentation') }}</router-link>
          <router-link to="/tutorial">{{ t('marketing.layout.footer.resources.api') }}</router-link>
          <router-link to="/console/system">{{ t('marketing.layout.footer.resources.status') }}</router-link>
          <router-link to="/tutorial">{{ t('marketing.layout.footer.resources.changelog') }}</router-link>
        </div>

        <div class="foot-col">
          <h5>{{ t('marketing.layout.footer.exchanges.title') }}</h5>
          <span class="foot-static">Binance</span>
          <span class="foot-static">OKX</span>
          <span class="foot-static">Gate.io</span>
          <span class="foot-static">Bitget</span>
          <span class="foot-static">Hyperliquid</span>
        </div>
      </div>

      <div class="foot-bottom">
        <p class="risk">
          <b>{{ t('marketing.layout.footer.risk.label') }}</b> {{ t('marketing.layout.footer.risk.body') }}
        </p>
        <div class="foot-meta">
          <span class="clk">{{ utc }}</span>
          <span>{{ t('marketing.layout.footer.copyright') }}</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* All selectors are nested under .marketing-site so light Swiss styling
   never reaches the dark D1 console. */

.marketing-site .m-wrap {
  max-width: var(--m-maxw);
  margin: 0 auto;
  padding-left: var(--m-pad);
  padding-right: var(--m-pad);
}

/* ── nav ── */
.marketing-site .m-nav {
  position: sticky;
  top: 0;
  z-index: 50;
  background: transparent;
  border-bottom: 1px solid transparent;
  transition: background 0.2s, border-color 0.2s, backdrop-filter 0.2s;
}
.marketing-site .m-nav.scrolled {
  background: rgba(252, 252, 250, 0.86);
  backdrop-filter: saturate(140%) blur(12px);
  border-bottom: 1px solid var(--m-line);
}
.marketing-site .m-nav-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
}

.marketing-site .m-wordmark {
  display: flex;
  align-items: baseline;
  gap: 9px;
  font-weight: 600;
  font-size: 17px;
  letter-spacing: -0.02em;
  color: var(--m-ink);
}
.marketing-site .m-wordmark .glyph {
  width: 14px;
  height: 14px;
  border: 1.5px solid var(--m-ink);
  position: relative;
  flex: none;
  align-self: center;
  transform: translateY(1px);
}
.marketing-site .m-wordmark .glyph::after {
  content: "";
  position: absolute;
  inset: 3px;
  background: var(--m-accent);
}
.marketing-site .m-wordmark .sub {
  font-family: var(--m-font-mono);
  font-size: 10px;
  color: var(--m-ink-3);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-weight: 500;
}

.marketing-site .m-nav-links {
  display: flex;
  gap: 30px;
  align-items: center;
}
.marketing-site .m-nav-links a {
  font-size: 14px;
  color: var(--m-ink-2);
  letter-spacing: -0.01em;
  transition: color 0.15s;
}
.marketing-site .m-nav-links a:hover { color: var(--m-ink); }

.marketing-site .m-nav-cta {
  display: flex;
  align-items: center;
  gap: 18px;
}
.marketing-site .m-nav-cta .console {
  font-family: var(--m-font-mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--m-ink-3);
  transition: color 0.15s;
}
.marketing-site .m-nav-cta .console:hover { color: var(--m-ink); }
.marketing-site .m-nav-cta .login {
  font-size: 14px;
  color: var(--m-ink-2);
  transition: color 0.15s;
}
.marketing-site .m-nav-cta .login:hover { color: var(--m-ink); }

/* ── language switcher (Swiss restraint: hairline + mono small caps) ── */
.marketing-site .m-lang {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 9px;
  border: 1px solid var(--m-line);
  border-radius: var(--m-radius);
  font-family: var(--m-font-mono);
}
.marketing-site .m-lang-opt {
  font-family: var(--m-font-mono) !important;
  font-size: 11px;
  letter-spacing: 0.06em;
  line-height: 1;
  color: var(--m-ink-4);
  background: transparent;
  border: 0;
  padding: 1px 1px;
  cursor: pointer;
  transition: color 0.15s;
}
.marketing-site .m-lang-opt:hover { color: var(--m-ink-2); }
.marketing-site .m-lang-opt.active {
  color: var(--m-ink);
  font-weight: 600;
}
.marketing-site .m-lang-sep {
  font-size: 11px;
  color: var(--m-ink-4);
  line-height: 1;
  user-select: none;
}

/* shared button */
.marketing-site .m-btn {
  font-family: var(--m-font-display);
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
  gap: 8px;
  white-space: nowrap;
}
.marketing-site .m-btn:hover {
  background: var(--m-accent);
  border-color: var(--m-accent);
}
.marketing-site .m-btn .arw {
  font-family: var(--m-font-mono);
  font-weight: 400;
}
.marketing-site .m-btn-accent {
  background: var(--m-accent);
  border-color: var(--m-accent);
  color: var(--m-paper);
}
.marketing-site .m-btn-accent:hover {
  background: var(--m-ink);
  border-color: var(--m-ink);
}

.marketing-site .m-main { position: relative; }

/* ── footer ── */
.marketing-site .m-footer {
  padding-top: clamp(56px, 6vw, 84px);
  padding-bottom: 48px;
}
.marketing-site .foot-top {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 32px;
  padding-bottom: 42px;
  border-bottom: 1px solid var(--m-line);
}
.marketing-site .foot-brand .m-wordmark { margin-bottom: 18px; }
.marketing-site .foot-status {
  display: flex;
  flex-direction: column;
  gap: 9px;
  font-family: var(--m-font-mono);
  font-size: 11px;
  color: var(--m-ink-3);
  letter-spacing: 0.03em;
}
.marketing-site .foot-status .st {
  display: flex;
  align-items: center;
  gap: 9px;
}
.marketing-site .foot-status .st .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--m-pos);
  box-shadow: 0 0 0 3px rgba(22, 122, 60, 0.12);
  flex: none;
}
.marketing-site .foot-status .st .dot.amber {
  background: var(--m-accent);
  box-shadow: 0 0 0 3px rgba(255, 77, 0, 0.12);
}
.marketing-site .foot-status .st b { color: var(--m-ink); font-weight: 500; }

.marketing-site .foot-col h5 {
  font-family: var(--m-font-mono);
  font-size: 10px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--m-ink-3);
  margin-bottom: 16px;
}
.marketing-site .foot-col a,
.marketing-site .foot-col .foot-static {
  display: block;
  font-size: 14px;
  color: var(--m-ink-2);
  margin-bottom: 11px;
  letter-spacing: -0.01em;
  transition: color 0.15s;
}
.marketing-site .foot-col a:hover { color: var(--m-accent); }

.marketing-site .foot-bottom {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 32px;
  padding-top: 26px;
  flex-wrap: wrap;
}
.marketing-site .risk {
  font-size: 12px;
  color: var(--m-ink-3);
  line-height: 1.6;
  max-width: 64ch;
  letter-spacing: -0.005em;
}
.marketing-site .risk b { color: var(--m-ink-2); font-weight: 500; }
.marketing-site .foot-meta {
  font-family: var(--m-font-mono);
  font-size: 11px;
  color: var(--m-ink-3);
  letter-spacing: 0.04em;
  text-align: right;
  white-space: nowrap;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.marketing-site .foot-meta .clk {
  color: var(--m-ink);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

/* ── responsive ──
   Breakpoint contract: desktop 1440 base · tablet ≤960 · mobile ≤640 · fine ≤420.
   Mobile invariant: the language switcher + the primary accent CTA must ALWAYS
   stay visible and usable. Only secondary chrome (nav links, console, login)
   collapses on narrow viewports — Swiss restraint, no overflow. */

/* tablet — tighten the rhythm, footer 4 → 2 columns */
@media (max-width: 960px) {
  .marketing-site .m-nav-links { gap: 22px; }
  .marketing-site .m-nav-cta { gap: 14px; }
  .marketing-site .foot-top { grid-template-columns: 1fr 1fr; row-gap: 36px; }
}

/* small tablet / large phone — drop the secondary nav links so the
   wordmark · language switcher · CTA row never wraps or overflows.
   The console + login text links also fold here (reachable via footer). */
@media (max-width: 768px) {
  .marketing-site .m-nav-links { display: none; }
  .marketing-site .m-nav-cta .console,
  .marketing-site .m-nav-cta .login { display: none; }
}

/* mobile — footer collapses to a single column; nav keeps only the
   always-on language switcher + accent CTA, with trimmed padding. */
@media (max-width: 640px) {
  .marketing-site .m-nav-cta { gap: 10px; }
  .marketing-site .m-btn { padding: 8px 14px; }
  .marketing-site .foot-top { grid-template-columns: 1fr; }
  .marketing-site .foot-bottom { flex-direction: column; }
  .marketing-site .foot-meta { text-align: left; }
}

/* fine — keep the wordmark sub-label from crowding the lang + CTA on
   the narrowest phones; everything stays on one line, no overflow. */
@media (max-width: 420px) {
  .marketing-site .m-wordmark .sub { display: none; }
  .marketing-site .m-nav-inner { height: 58px; }
  .marketing-site .m-lang { padding: 4px 7px; }
}
</style>
