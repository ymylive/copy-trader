<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const drawer = ref(false)
const subOpen = ref(true)

const menu = [
  { name: 'console.dashboard', label: '首页', icon: 'home' },
  { name: 'console.accounts', label: '账户管理', icon: 'wallet' },
  {
    label: '智能跟单',
    icon: 'chart',
    children: [
      { name: 'console.traderSquare', label: '交易员广场' },
      { name: 'console.exchangeWatchlist', label: '交易所自选' },
      { name: 'console.bicoinWatchlist', label: '币Coin 自选' },
      { name: 'console.positions', label: '持仓详情' }
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

const icons: Record<string, string> = {
  home: 'M3 11 12 3l9 8v9a2 2 0 0 1-2 2h-4v-6h-6v6H5a2 2 0 0 1-2-2v-9z',
  wallet: 'M3 7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7zm14 5a1 1 0 1 0 0 2 1 1 0 0 0 0-2z',
  chart: 'M3 21V3m18 18H3m4-4 4-6 4 4 6-10',
  settings: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm7-3 2-2-2-2m-2-2-2-2-2 2m-4 12 2 2 2-2m4-4 2 2 2-2'
}
</script>

<template>
  <div class="console-shell">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="logo-block">
        <img src="/logo.svg" />
        <div>
          <div class="brand-zh">Copy Trader</div>
          <div class="brand-en">智能跟单系统</div>
        </div>
      </div>

      <nav class="menu">
        <template v-for="item in menu" :key="item.label">
          <div
            v-if="!item.children"
            class="menu-item"
            :class="{ active: active === item.name }"
            @click="goto(item.name!)"
          >
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path :d="icons[item.icon]" />
            </svg>
            <span>{{ item.label }}</span>
          </div>
          <div v-else>
            <div class="menu-section">{{ item.label }}</div>
            <div class="menu-group" @click="subOpen = !subOpen">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path :d="icons[item.icon]" />
              </svg>
              <span>智能跟单</span>
              <svg class="caret" :class="{ open: subOpen }" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6" /></svg>
            </div>
            <transition name="fade">
              <div v-if="subOpen" class="submenu">
                <div
                  v-for="sub in item.children"
                  :key="sub.name"
                  class="sub-item"
                  :class="{ active: active === sub.name }"
                  @click="goto(sub.name)"
                >
                  {{ sub.label }}
                </div>
              </div>
            </transition>
          </div>
        </template>
      </nav>

      <div class="sidebar-bottom">
        <div
          class="menu-item"
          :class="{ active: active === 'console.system' }"
          @click="goto('console.system')"
        >
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33h0a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51h0a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v0a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
          <span>系统控制</span>
        </div>
      </div>
    </aside>

    <!-- Mobile drawer -->
    <el-drawer v-model="drawer" direction="ltr" size="240px" :with-header="false">
      <aside class="sidebar mobile">
        <!-- duplicate compact menu -->
        <div class="logo-block">
          <img src="/logo.svg" />
          <div class="brand-zh">Copy Trader</div>
        </div>
        <nav class="menu">
          <template v-for="item in menu" :key="item.label">
            <div v-if="!item.children" class="menu-item" :class="{ active: active === item.name }" @click="goto(item.name!)">
              <span>{{ item.label }}</span>
            </div>
            <div v-else>
              <div class="menu-section">{{ item.label }}</div>
              <div v-for="sub in item.children" :key="sub.name" class="sub-item" :class="{ active: active === sub.name }" @click="goto(sub.name)">
                {{ sub.label }}
              </div>
            </div>
          </template>
          <div class="menu-item" :class="{ active: active === 'console.system' }" @click="goto('console.system')">系统控制</div>
        </nav>
      </aside>
    </el-drawer>

    <!-- Main -->
    <main class="main">
      <header class="topbar">
        <div class="left">
          <el-button text class="hamburger" @click="drawer = true">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M3 12h18M3 18h18" /></svg>
          </el-button>
          <div class="hello">Hello {{ auth.user?.nickname || 'Demo' }}</div>
        </div>
        <div class="right">
          <button class="icon-btn" title="系统设置">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="3" />
              <path d="M12 1v6m0 10v6m11-11h-6m-10 0H1m17.66-7.66-4.24 4.24M7.34 16.66 3.1 20.9M20.9 20.9l-4.24-4.24M7.34 7.34 3.1 3.1" />
            </svg>
          </button>
          <button class="icon-btn" title="通知">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 8A6 6 0 1 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            <span class="dot"></span>
          </button>
          <div class="svip" v-if="auth.user?.svip">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="#F59E0B"><path d="M12 2 4 7v6c0 5 3.4 9.4 8 11 4.6-1.6 8-6 8-11V7l-8-5z" /></svg>
            SVIP
          </div>
          <el-dropdown trigger="click" @command="(c: string) => c === 'logout' && logout()">
            <div class="user-avatar">
              {{ (auth.user?.username || 'D').slice(0, 1).toUpperCase() }}
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/profile')">个人中心</el-dropdown-item>
                <el-dropdown-item @click="router.push('/wallet')">钱包</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <div class="points hide-sm">积分: <b>{{ auth.user?.points ?? 0 }}</b></div>
        </div>
      </header>

      <div class="page">
        <router-view />
      </div>
    </main>
  </div>
</template>

<style scoped>
.console-shell {
  display: grid;
  grid-template-columns: 232px 1fr;
  min-height: 100vh;
  background: var(--ct-bg);
}
.sidebar {
  background: linear-gradient(180deg, #0D9488 0%, #047857 100%);
  color: #E5F7F2;
  padding: 24px 14px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  position: sticky;
  top: 0;
  height: 100vh;
}
.logo-block {
  display: flex; align-items: center; gap: 10px;
  padding: 0 8px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
.logo-block img { width: 36px; height: 36px; }
.brand-zh { color: #fff; font-weight: 700; font-size: 16px; }
.brand-en { color: rgba(255, 255, 255, 0.7); font-size: 11px; margin-top: 2px; }
.menu { flex: 1; display: flex; flex-direction: column; gap: 2px; padding-top: 8px; }
.menu-section { color: rgba(255, 255, 255, 0.5); font-size: 11px; padding: 12px 12px 4px; letter-spacing: 0.05em; }
.menu-item,
.menu-group {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.85);
  cursor: pointer;
  transition: background 0.15s;
}
.menu-item:hover,
.menu-group:hover { background: rgba(255, 255, 255, 0.07); }
.menu-item.active {
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
  font-weight: 600;
}
.caret { margin-left: auto; transition: transform 0.2s; }
.caret.open { transform: rotate(180deg); }
.submenu { display: flex; flex-direction: column; gap: 2px; padding: 4px 0 4px 26px; }
.sub-item {
  font-size: 13px;
  padding: 8px 12px;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.78);
  cursor: pointer;
  transition: background 0.15s;
}
.sub-item:hover { background: rgba(255, 255, 255, 0.07); }
.sub-item.active { background: rgba(255, 255, 255, 0.16); color: #fff; font-weight: 600; }
.sidebar-bottom { border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 12px; }
.fade-enter-active,
.fade-leave-active { transition: opacity 0.18s; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }

.main { display: flex; flex-direction: column; min-width: 0; }
.topbar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 28px;
  background: var(--ct-bg-card);
  border-bottom: 1px solid var(--ct-border);
  position: sticky; top: 0; z-index: 10;
}
.left { display: flex; align-items: center; gap: 12px; }
.hamburger { display: none; }
.hello { font-size: 18px; color: var(--ct-text-1); font-weight: 500; }
.right { display: flex; align-items: center; gap: 14px; }
.icon-btn {
  position: relative;
  background: transparent;
  border: 0;
  cursor: pointer;
  color: var(--ct-primary);
  padding: 6px;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
}
.icon-btn:hover { background: var(--ct-primary-50); }
.dot {
  position: absolute; top: 4px; right: 4px;
  width: 8px; height: 8px;
  background: var(--ct-danger);
  border-radius: 50%;
  border: 1.5px solid #fff;
}
.svip {
  display: flex; align-items: center; gap: 4px;
  background: linear-gradient(135deg, #FBBF24, #F59E0B);
  color: #78350F;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}
.user-avatar {
  width: 34px; height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, #34D399, #0D9488);
  color: #fff; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
}
.points { color: var(--ct-text-2); font-size: 13px; }
.page { padding: 24px 28px; flex: 1; }

@media (max-width: 1024px) {
  .console-shell { grid-template-columns: 1fr; }
  .sidebar { display: none; }
  .hamburger { display: inline-flex; }
  .page { padding: 16px; }
  .topbar { padding: 12px 16px; }
}

.sidebar.mobile { position: static; height: auto; }
</style>
