import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

export const useMock = (): boolean => import.meta.env.VITE_USE_MOCK === 'true'

const http: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' }
})

http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`)
  }
  return config
})

http.interceptors.response.use(
  (resp) => resp.data,
  (err) => {
    const status = err?.response?.status
    const msg = err?.response?.data?.detail || err?.message || '请求失败'
    if (status === 401) {
      localStorage.removeItem('token')
      // soft redirect
      if (location.pathname.startsWith('/console')) location.href = '/login'
    } else {
      ElMessage.error(typeof msg === 'string' ? msg : '请求失败')
    }
    return Promise.reject(err)
  }
)

export default http

/** Helper to short-circuit to mock data without hitting backend. */
export function mockOr<T>(real: () => Promise<T>, mockFn: () => T | Promise<T>): Promise<T> {
  if (useMock()) return Promise.resolve(mockFn())
  return real()
}
