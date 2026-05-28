<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const tabs = [
  { name: 'home', label: '首页' },
  { name: 'invite', label: '推广返佣' },
  { name: 'shop', label: '商城' },
  { name: 'wallet', label: '钱包' },
  { name: 'profile', label: '个人中心' },
  { name: 'tutorial', label: '使用教程' }
]
const active = computed(() => String(route.name || 'home'))
</script>

<template>
  <div class="public-shell ct-space ct-space-stars">
    <header class="topbar">
      <div class="brand" @click="router.push('/')">
        <img src="/logo.svg" alt="logo" />
        <span class="brand-text">Copy Trader</span>
      </div>
      <nav class="nav">
        <router-link
          v-for="t in tabs"
          :key="t.name"
          :to="t.name === 'home' ? '/' : `/${t.name}`"
          class="tab-li"
          :class="{ active: active === t.name }"
        >
          {{ t.label }}
        </router-link>
        <router-link to="/console" class="tab-li tab-cta">控制台</router-link>
      </nav>
      <div class="actions">
        <router-link v-if="!auth.isAuthed" to="/login" class="login-btn">Login</router-link>
        <span v-else class="user-pill">{{ auth.user?.nickname || auth.user?.username || 'cornna' }}</span>
      </div>
    </header>

    <main class="public-main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.public-shell {
  position: relative;
  min-height: 100vh;
  overflow-x: hidden;
}
.topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 32px;
  backdrop-filter: blur(10px);
  background: rgba(6, 8, 12, 0.7);
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}
.brand img { width: 32px; height: 32px; }
.brand-text {
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5px;
  font-size: 17px;
}
.nav {
  display: flex;
  gap: 28px;
  align-items: center;
}
.tab-li {
  color: #d1d5db;
  font-size: 14px;
  padding: 6px 4px;
  border-bottom: 2px solid transparent;
  transition: color 0.15s, border-color 0.15s;
}
.tab-li:hover { color: #fff; }
.tab-li.active {
  color: var(--ct-space-accent);
  border-bottom-color: var(--ct-space-accent);
  font-weight: 600;
}
.tab-cta {
  background: var(--ct-space-accent);
  color: #06140a !important;
  padding: 8px 18px;
  border-radius: 999px;
  font-weight: 700;
  border: 0 !important;
}
.tab-cta:hover { filter: brightness(1.05); }
.actions { display: flex; align-items: center; }
.login-btn,
.user-pill {
  padding: 8px 22px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  color: #e5e7eb;
  font-size: 13px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}
.login-btn:hover { background: rgba(255, 255, 255, 0.1); }
.public-main { position: relative; z-index: 1; }

@media (max-width: 768px) {
  .topbar { padding: 12px 16px; }
  .nav { gap: 14px; }
  .tab-li { font-size: 12px; }
  .brand-text { display: none; }
}
</style>
