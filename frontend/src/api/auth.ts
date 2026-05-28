import http, { mockOr } from './axios'
import { mockLoginResp, mockUser } from '@/mock/data'

export interface LoginPayload {
  username: string
  password: string
  captcha?: string
}

export interface RegisterPayload {
  username: string
  password: string
  email?: string
  invite_code?: string
}

export const authApi = {
  login: (p: LoginPayload) => mockOr(
    () => http.post('/auth/login', p),
    () => mockLoginResp()
  ),
  register: (p: RegisterPayload) => mockOr(
    () => http.post('/auth/register', p),
    () => mockLoginResp()
  ),
  forgot: (email: string) => mockOr(
    () => http.post('/auth/forgot', { email }),
    () => ({ ok: true })
  ),
  me: () => mockOr(
    () => http.get('/auth/me'),
    () => mockUser()
  ),
  logout: () => mockOr(
    () => http.post('/auth/logout'),
    () => ({ ok: true })
  )
}
