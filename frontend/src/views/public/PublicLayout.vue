<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import StatusBar from '@/components/StatusBar.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const tabs = [
  { name: 'home',     idx: '01', label: 'HERO' },
  { name: 'tutorial', idx: '02', label: 'DOCS' },
  { name: 'shop',     idx: '03', label: 'PRICING' },
  { name: 'wallet',   idx: '04', label: 'WALLET' },
  { name: 'invite',   idx: '05', label: 'REFERRAL' },
  { name: 'profile',  idx: '06', label: 'SECURITY' }
]
const active = computed(() => String(route.name || 'home'))
</script>

<template>
  <div class="public-shell">
    <StatusBar :uid="auth.user?.id ?? 52494073" />

    <nav class="topnav">
      <div class="wordmark" @click="router.push('/')">
        COPY<span class="slash">//</span>TRADER<span class="ver">v2.6.1 · BUILD 8941</span>
      </div>
      <div class="nav-tabs">
        <router-link
          v-for="t in tabs"
          :key="t.name"
          :to="t.name === 'home' ? '/' : `/${t.name}`"
          class="nav-tab"
          :class="{ active: active === t.name }"
        >
          <span class="idx">{{ t.idx }}</span>{{ t.label }}
        </router-link>
      </div>
      <div class="right">
        <router-link to="/console" class="console-pill">CONSOLE →</router-link>
        <router-link v-if="!auth.isAuthed" to="/login" class="login-pill">LOGIN</router-link>
        <span v-else class="user-pill">{{ auth.user?.nickname || 'MAIETRY' }}</span>
      </div>
    </nav>

    <main class="public-main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.public-shell {
  background: var(--ct-bg);
  min-height: 100vh;
  color: var(--ct-text);
  padding-top: 74px;
}

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
.nav-tabs {
  display: flex;
  gap: 0;
  margin-left: 36px;
  height: 52px;
}
.nav-tab {
  height: 52px;
  display: flex;
  align-items: center;
  padding: 0 18px;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ct-text-2);
  border-bottom: 2px solid transparent;
  transition: color 80ms linear;
}
.nav-tab:hover { color: var(--ct-text); }
.nav-tab.active {
  color: var(--ct-amber);
  border-bottom-color: var(--ct-amber);
}
.nav-tab .idx {
  color: var(--ct-text-dim);
  margin-right: 8px;
  font-size: 10px;
}
.nav-tab.active .idx { color: var(--ct-amber); }

.right {
  margin-left: auto;
  display: flex;
  gap: 12px;
  align-items: center;
}
.console-pill,
.login-pill,
.user-pill {
  padding: 6px 14px;
  border: 1px solid var(--ct-divider-strong);
  color: var(--ct-text);
  font-family: var(--ct-font-mono);
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.console-pill {
  background: var(--ct-amber);
  border-color: var(--ct-amber);
  color: #0A0E14 !important;
  font-weight: 600;
}
.console-pill:hover { filter: brightness(1.08); }
.login-pill:hover { border-color: var(--ct-amber); color: var(--ct-amber); }

.public-main { position: relative; }

@media (max-width: 1024px) {
  .nav-tabs { display: none; }
}
</style>
