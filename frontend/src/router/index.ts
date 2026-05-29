import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  // Marketing site (light INSTITUTIONAL CLARITY layout)
  {
    path: '/',
    component: () => import('@/views/public/MarketingLayout.vue'),
    meta: { marketing: true },
    children: [
      { path: '', name: 'home', component: () => import('@/views/home/Home.vue') },
      { path: 'features', name: 'features', component: () => import('@/views/features/Features.vue') },
      { path: 'pricing', name: 'pricing', component: () => import('@/views/pricing/Pricing.vue') }
    ]
  },
  // Public site (shared dark space layout)
  {
    path: '/',
    component: () => import('@/views/public/PublicLayout.vue'),
    children: [
      { path: 'invite', name: 'invite', component: () => import('@/views/invite/Invite.vue') },
      { path: 'shop', name: 'shop', component: () => import('@/views/shop/Shop.vue') },
      { path: 'wallet', name: 'wallet', component: () => import('@/views/wallet/Wallet.vue') },
      { path: 'profile', name: 'profile', component: () => import('@/views/profile/Security.vue') },
      { path: 'tutorial', name: 'tutorial', component: () => import('@/views/tutorial/Tutorial.vue') }
    ]
  },
  // Auth pages (no chrome)
  { path: '/login', name: 'login', component: () => import('@/views/auth/Login.vue') },
  { path: '/register', name: 'register', component: () => import('@/views/auth/Register.vue') },
  { path: '/forgot', name: 'forgot', component: () => import('@/views/auth/ForgotPassword.vue') },

  // Console
  {
    path: '/console',
    component: () => import('@/views/console/Layout.vue'),
    meta: { requiresAuth: true },
    redirect: { name: 'console.dashboard' },
    children: [
      { path: 'dashboard', name: 'console.dashboard', component: () => import('@/views/console/Dashboard.vue') },
      { path: 'accounts', name: 'console.accounts', component: () => import('@/views/console/Accounts.vue') },
      { path: 'trader-square', name: 'console.traderSquare', component: () => import('@/views/console/TraderSquare.vue') },
      { path: 'exchange-watchlist', name: 'console.exchangeWatchlist', component: () => import('@/views/console/ExchangeWatchlist.vue') },
      { path: 'bicoin-watchlist', name: 'console.bicoinWatchlist', component: () => import('@/views/console/BicoinWatchlist.vue') },
      { path: 'positions', name: 'console.positions', component: () => import('@/views/console/Positions.vue') },
      { path: 'system', name: 'console.system', component: () => import('@/views/console/System.vue') }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthed) {
    // In dev/mock mode auto-login a demo user so UX flows are testable.
    if (import.meta.env.VITE_USE_MOCK === 'true') {
      auth.mockLogin()
      return true
    }
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
