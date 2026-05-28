import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'

export interface UserInfo {
  id: number
  username: string
  nickname: string
  email: string
  avatar: string
  svip: boolean
  points: number
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const user = ref<UserInfo | null>(null)

  const isAuthed = computed(() => !!token.value)

  function persist(newToken: string, u: UserInfo) {
    token.value = newToken
    user.value = u
    localStorage.setItem('token', newToken)
  }

  async function login(username: string, password: string, captcha?: string) {
    const data = await authApi.login({ username, password, captcha }) as { token: string; user: UserInfo }
    persist(data.token, data.user)
  }

  async function register(username: string, password: string, email?: string, invite_code?: string) {
    const data = await authApi.register({ username, password, email, invite_code }) as { token: string; user: UserInfo }
    persist(data.token, data.user)
  }

  function mockLogin() {
    persist('mock-jwt-' + Math.random().toString(36).slice(2), {
      id: 1401,
      username: 'demo_trader',
      nickname: 'Demo',
      email: 'demo@example.com',
      avatar: '',
      svip: true,
      points: 0
    })
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return { token, user, isAuthed, login, register, mockLogin, logout }
})
