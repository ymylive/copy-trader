<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import StatusBar from '@/components/StatusBar.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const drawer = ref(false)

interface MenuItem { name: string; label: string; idx?: string }
interface MenuGroup { group: string; items: MenuItem[] }

const menu: MenuGroup[] = [
  {
    group: 'OPERATIONS',
    items: [
      { name: 'console.dashboard',  label: 'DASHBOARD',   idx: '01' },
      { name: 'console.accounts',   label: 'ACCOUNTS',    idx: '02' },
      { name: 'console.positions',  label: 'POSITIONS',   idx: '03' }
    ]
  },
  {
    group: 'COPY-TRADING',
    items: [
      { name: 'console.traderSquare',      label: 'TRADER SQUARE',    idx: '04' },
      { name: 'console.exchangeWatchlist', label: 'EXCHANGE WATCHLIST', idx: '05' },
      { name: 'console.bicoinWatchlist',   label: 'BICOIN WATCHLIST',  idx: '06' }
    ]
  },
  {
    group: 'SYSTEM',
    items: [
      { name: 'console.system', label: 'CONTROL', idx: '07' }
    ]
  }
]

const active = computed(() => String(route.name))

function goto(name: string) {
  router.push({ name })
  drawer.value = false
}

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="console-shell">
    <!-- Top status bar (22px) -->
    <StatusBar :uid="auth.user?.id ?? 52494073" />

    <!-- Top nav (52px) -->
    <nav class="topnav">
      <div class="wordmark" @click="router.push('/')">
        COPY<span class="slash">//</span>TRADER<span class="ver">v2.6.1 · BUILD 8941</span>
      </div>
      <div class="spacer-mobile" />
      <div class="right">
        <span class="pill"><span class="dot"></span>NET BTC-MAINNET</span>
        <span class="hide-sm">43.153.149.108</span>
        <span class="sep hide-sm">|</span>
        <el-dropdown trigger="click" @command="(c: string) => c === 'logout' && logout()">
          <span class="user-pill">
            {{ auth.user?.nickname || 'Maietry' }}
            <span class="caret">▾</span>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="router.push('/profile')">PROFILE</el-dropdown-item>
              <el-dropdown-item @click="router.push('/wallet')">WALLET</el-dropdown-item>
              <el-dropdown-item divided command="logout">LOGOUT</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <button class="hamburger" @click="drawer = true" aria-label="menu">≡</button>
      </div>
    </nav>

    <div class="shell-grid">
      <!-- Sidebar -->
      <aside class="sidebar">
        <div v-for="g in menu" :key="g.group" class="menu-group">
          <div class="menu-section">{{ g.group }}</div>
          <button
            v-for="item in g.items"
            :key="item.name"
            class="menu-item"
            :class="{ active: active === item.name }"
            @click="goto(item.name)"
          >
            <span class="idx">{{ item.idx }}</span>
            <span class="lbl">{{ item.label }}</span>
            <span class="cursor-mark" v-if="active === item.name">▌</span>
          </button>
        </div>

        <div class="sidebar-foot">
          <div class="foot-line"><span>SVC</span><span class="amber">220D 13H</span></div>
          <div class="foot-line"><span>SVIP</span><span class="amber" v-if="auth.user?.svip">✓ ACTIVE</span><span v-else>—</span></div>
        </div>
      </aside>

      <!-- Mobile drawer -->
      <el-drawer v-model="drawer" direction="ltr" size="260px" :with-header="false">
        <aside class="sidebar mobile">
          <div v-for="g in menu" :key="g.group" class="menu-group">
            <div class="menu-section">{{ g.group }}</div>
            <button
              v-for="item in g.items"
              :key="item.name"
              class="menu-item"
              :class="{ active: active === item.name }"
              @click="goto(item.name)"
            >
              <span class="idx">{{ item.idx }}</span>
              <span class="lbl">{{ item.label }}</span>
            </button>
          </div>
        </aside>
      </el-drawer>

      <!-- Main page -->
      <main class="main">
        <div class="page">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.console-shell {
  background: var(--ct-bg);
  min-height: 100vh;
  color: var(--ct-text);
  padding-top: 74px;
}

/* Top nav 52px (status bar is 22px fixed) */
.topnav {
  position: fixed;
  top: 22px;
  left: 0;
  right: 0;
  z-index: 99;
  background: var(--ct-bg);
  border-bottom: 1px solid var(--ct-divider);
  height: 52px;
  display: flex;
  align-items: center;
  padding: 0 18px;
  font-family: var(--ct-font-mono);
}
.wordmark {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--ct-text);
  cursor: pointer;
}
.wordmark .slash { color: var(--ct-amber); }
.wordmark .ver {
  font-size: 10px;
  color: var(--ct-text-3);
  margin-left: 8px;
  letter-spacing: 0.08em;
}
.spacer-mobile { flex: 1; }
.topnav .right {
  margin-left: auto;
  display: flex;
  gap: 14px;
  align-items: center;
  font-size: 11px;
  color: var(--ct-text-3);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 8px;
  border: 1px solid var(--ct-divider-strong);
  color: var(--ct-text-2);
  font-size: 10px;
  letter-spacing: 0.08em;
}
.pill .dot {
  width: 5px;
  height: 5px;
  background: var(--ct-pos);
}
.sep { color: var(--ct-text-dim); }
.user-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border: 1px solid var(--ct-divider-strong);
  color: var(--ct-text);
  font-family: var(--ct-font-mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  cursor: pointer;
}
.user-pill:hover { border-color: var(--ct-amber); color: var(--ct-amber); }
.caret { font-size: 9px; color: var(--ct-text-3); }
.hamburger {
  display: none;
  background: transparent;
  border: 1px solid var(--ct-divider-strong);
  color: var(--ct-text);
  font-size: 16px;
  width: 30px;
  height: 30px;
  cursor: pointer;
  align-items: center;
  justify-content: center;
}

.shell-grid {
  display: grid;
  grid-template-columns: 200px 1fr;
  min-height: calc(100vh - 74px);
}

/* Sidebar */
.sidebar {
  background: var(--ct-bg);
  border-right: 1px solid var(--ct-divider);
  padding: 18px 0 24px;
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 74px;
  height: calc(100vh - 74px);
  overflow-y: auto;
}
.menu-group {
  margin-bottom: 18px;
  border-bottom: 1px solid var(--ct-divider);
  padding-bottom: 12px;
}
.menu-group:last-of-type { border-bottom: 0; }
.menu-section {
  font-size: 10px;
  color: var(--ct-text-dim);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  padding: 0 18px 8px;
  font-family: var(--ct-font-mono);
}
.menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 18px;
  background: transparent;
  border: 0;
  border-left: 2px solid transparent;
  font-family: var(--ct-font-mono);
  font-size: 12px;
  color: var(--ct-text-2);
  cursor: pointer;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  text-align: left;
  transition: color 100ms linear, background 100ms linear, border-color 100ms linear;
}
.menu-item:hover {
  color: var(--ct-text);
  background: var(--ct-bg-2);
}
.menu-item.active {
  color: var(--ct-amber);
  background: var(--ct-bg-2);
  border-left-color: var(--ct-amber);
}
.menu-item .idx {
  color: var(--ct-text-dim);
  font-size: 10px;
  letter-spacing: 0.1em;
}
.menu-item.active .idx { color: var(--ct-amber); }
.menu-item .lbl { flex: 1; }
.cursor-mark {
  color: var(--ct-amber);
  animation: blink 1s steps(2, start) infinite;
}
@keyframes blink { to { visibility: hidden; } }

.sidebar-foot {
  margin-top: auto;
  padding: 12px 18px 0;
  border-top: 1px solid var(--ct-divider);
  font-family: var(--ct-font-mono);
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ct-text-3);
}
.foot-line {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
}
.foot-line .amber { color: var(--ct-amber); }

/* Main */
.main {
  background: var(--ct-bg);
  min-width: 0;
}
.page { padding: 18px 18px 36px; }

/* Mobile */
@media (max-width: 1024px) {
  .shell-grid { grid-template-columns: 1fr; }
  .sidebar:not(.mobile) { display: none; }
  .hamburger { display: inline-flex; }
}
.sidebar.mobile {
  position: static;
  height: auto;
  border-right: 0;
}
</style>
