import axios from 'axios'
import { ElMessage } from 'element-plus'

export const useMock = (): boolean => import.meta.env.VITE_USE_MOCK === 'true'

const raw = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' }
})

raw.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`)
  }
  return config
})

raw.interceptors.response.use(
  (resp) => resp.data,
  (err) => {
    const status = err?.response?.status
    const msg = err?.response?.data?.detail || err?.message || '请求失败'
    if (status === 401) {
      localStorage.removeItem('token')
      if (location.pathname.startsWith('/console')) location.href = '/login'
    } else {
      ElMessage.error(typeof msg === 'string' ? msg : '请求失败')
    }
    return Promise.reject(err)
  }
)

/**
 * Typed HTTP facade. Since our response interceptor unwraps `resp.data`,
 * we re-type the verbs to return the plain payload `T`.
 */
const http = {
  get: <T = any>(url: string, config?: Parameters<typeof raw.get>[1]) =>
    raw.get(url, config) as unknown as Promise<T>,
  post: <T = any>(url: string, data?: unknown, config?: Parameters<typeof raw.post>[2]) =>
    raw.post(url, data, config) as unknown as Promise<T>,
  patch: <T = any>(url: string, data?: unknown, config?: Parameters<typeof raw.patch>[2]) =>
    raw.patch(url, data, config) as unknown as Promise<T>,
  put: <T = any>(url: string, data?: unknown, config?: Parameters<typeof raw.put>[2]) =>
    raw.put(url, data, config) as unknown as Promise<T>,
  delete: <T = any>(url: string, config?: Parameters<typeof raw.delete>[1]) =>
    raw.delete(url, config) as unknown as Promise<T>
}

export default http

/** Helper to short-circuit to mock data without hitting backend. */
export function mockOr<T>(real: () => Promise<T>, mockFn: () => T | Promise<T>): Promise<T> {
  if (useMock()) return Promise.resolve(mockFn())
  return real()
}
