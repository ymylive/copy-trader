<script setup lang="ts">
import { ref } from 'vue'
import { formatUTC } from '@/utils/format'

const active = ref('binance')
const renderTs = ref(formatUTC())

const exchanges = [
  {
    key: 'binance',
    name: 'BINANCE',
    steps: [
      'LOGIN binance.com → USER CENTER · API MANAGEMENT',
      'CREATE API · COMPLETE 2FA CHALLENGE',
      'PERMISSIONS · READ ✓ · USDS-M / COIN-M FUTURES ✓',
      'FUTURES SETTINGS · SWITCH TO HEDGE MODE',
      'COPY API_KEY / SECRET_KEY INTO CONSOLE',
      'OPTIONAL: ADD 4 EGRESS IPS TO API IP WHITELIST'
    ]
  },
  {
    key: 'okx',
    name: 'OKX',
    steps: [
      'LOGIN okx.com → PROFILE · API',
      'CREATE API · USE-CASE = API TRADING',
      'PERMISSIONS · TRADE ✓ · READ ✓',
      'SET PASSPHRASE · STORE SECURELY',
      'POSITION MODE · HEDGE',
      'PROVIDE KEY / SECRET / PASSPHRASE TO CONSOLE'
    ]
  },
  {
    key: 'gate',
    name: 'GATE.IO',
    steps: [
      'LOGIN gate.io → API MANAGEMENT',
      'CREATE SEPARATE KEY FOR COPY//TRADER',
      'PERMS · PERPETUAL = R/W · OTHERS = R/O',
      'CONTRACT SETTINGS · ENABLE HEDGE MODE',
      'PASTE KEY / SECRET INTO CONSOLE'
    ]
  },
  {
    key: 'bitget',
    name: 'BITGET',
    steps: [
      'LOGIN bitget.com → API MANAGEMENT',
      'CREATE TWO KEYS · CONTRACT-TRADE + LEAD-TRADE',
      'PERMS · CONTRACT TRADE ✓ · READ ✓',
      'POSITION MODE · HEDGE',
      'PROVIDE KEY / SECRET / PASSPHRASE TO CONSOLE'
    ]
  }
]

const copyModes = [
  {
    name: 'TRADER SQUARE',
    desc: 'Direct selection of platform-curated traders. No delay. Recommended for newcomers.',
    pros: ['ONE-TAP COPY', 'ZERO CONFIG', 'CURATED FEED']
  },
  {
    name: 'CUSTOM WATCHLIST',
    desc: 'Search arbitrary trader by link / id / nickname. Supports hidden positions and cookie sessions (SVIP).',
    pros: ['BROADER COVERAGE', 'NON-CURATED TRADERS', 'SVIP COOKIE REAL-TIME']
  }
]
</script>

<template>
  <div class="tut-page">
    <div class="sec-head">
      <div class="sec-title"><span class="amber">02 //</span> DOCUMENTATION · 5-MIN ONBOARDING</div>
      <div class="sec-coord">{{ renderTs }}</div>
    </div>

    <div class="ex-tabs">
      <button
        v-for="ex in exchanges"
        :key="ex.key"
        class="ex-tab"
        :class="{ active: active === ex.key }"
        @click="active = ex.key"
      >
        {{ ex.name }}
      </button>
    </div>

    <div v-for="ex in exchanges" v-show="active === ex.key" :key="ex.key" class="steps">
      <div v-for="(s, idx) in ex.steps" :key="idx" class="step">
        <span class="idx">{{ String(idx + 1).padStart(2, '0') }}</span>
        <span class="body">{{ s }}</span>
      </div>
    </div>

    <div class="sec-head">
      <div class="sec-title"><span class="amber">02-B //</span> COPY MODES</div>
    </div>
    <div class="modes">
      <div v-for="m in copyModes" :key="m.name" class="mode">
        <div class="mode-h">{{ m.name }}</div>
        <p class="mode-d">{{ m.desc }}</p>
        <div class="mode-pros">
          <span v-for="p in m.pros" :key="p" class="pro-chip">{{ p }}</span>
        </div>
      </div>
    </div>

    <div class="hedge-warn">
      ⚠ ALL VENUES MUST RUN HEDGE MODE · OTHERWISE OPEN ORDERS WILL BE NETTED AGAINST OPPOSING POSITIONS · VERIFY BEFORE COPY-JOB START.
    </div>
  </div>
</template>

<style scoped>
.tut-page {
  padding: 18px 18px 60px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 1080px;
  margin: 0 auto;
}

.ex-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--ct-divider);
}
.ex-tab {
  background: transparent;
  border: 0;
  border-bottom: 2px solid transparent;
  padding: 10px 18px;
  font-family: var(--ct-font-mono);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ct-text-2);
  cursor: pointer;
}
.ex-tab.active { color: var(--ct-amber); border-bottom-color: var(--ct-amber); }
.ex-tab:hover:not(.active) { color: var(--ct-text); }

.steps {
  display: flex;
  flex-direction: column;
  border-top: 1px solid var(--ct-divider);
}
.step {
  display: flex;
  gap: 16px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--ct-divider);
  font-family: var(--ct-font-mono);
}
.step .idx {
  color: var(--ct-amber);
  font-size: 12px;
  letter-spacing: 0.1em;
  font-weight: 600;
  min-width: 30px;
}
.step .body {
  color: var(--ct-text);
  font-size: 13px;
  letter-spacing: 0.02em;
  line-height: 1.5;
}

.modes {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  border: 1px solid var(--ct-divider);
}
.mode {
  padding: 16px 18px;
  border-right: 1px solid var(--ct-divider);
}
.mode:last-child { border-right: 0; }
.mode-h {
  color: var(--ct-amber);
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-weight: 600;
  margin-bottom: 10px;
  font-family: var(--ct-font-mono);
}
.mode-d {
  color: var(--ct-text);
  font-size: 12px;
  line-height: 1.6;
  margin: 0 0 14px;
  font-family: var(--ct-font-mono);
}
.mode-pros { display: flex; flex-wrap: wrap; gap: 6px; }
.pro-chip {
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border: 1px solid var(--ct-divider-strong);
  color: var(--ct-text-2);
  padding: 2px 8px;
  font-family: var(--ct-font-mono);
}

.hedge-warn {
  border: 1px solid rgba(255, 180, 0, 0.35);
  background: rgba(255, 180, 0, 0.04);
  color: var(--ct-amber);
  padding: 12px 14px;
  font-size: 11px;
  letter-spacing: 0.08em;
  line-height: 1.6;
  text-transform: uppercase;
  font-family: var(--ct-font-mono);
}

@media (max-width: 768px) {
  .modes { grid-template-columns: 1fr; }
  .mode { border-right: 0; border-bottom: 1px solid var(--ct-divider); }
  .mode:last-child { border-bottom: 0; }
}
</style>
