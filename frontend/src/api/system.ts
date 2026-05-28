import http, { mockOr } from './axios'

export const systemApi = {
  channels: () => mockOr(
    () => http.get('/system/notification-channels'),
    () => ({
      wechat: { bound: false, code: '' },
      telegram: { bound: false, session_id: '' },
      email: { bound: true, email: 'demo@example.com' },
      sms: { bound: false, phone: '' }
    })
  ),
  bindChannel: (channel: string, body: Record<string, unknown>) => mockOr(
    () => http.post(`/system/notification-channels/${channel}`, body),
    () => ({ ok: true })
  ),
  sendTest: (channel: string) => mockOr(
    () => http.post(`/system/notification-channels/${channel}/test`),
    () => ({ ok: true })
  ),
  versions: () => mockOr(
    () => http.get('/system/versions'),
    () => ({ current: 'v3.2.1', latest: 'v3.2.1', preview_opt_in: false })
  ),
  upgrade: (account_id: number) => mockOr(
    () => http.post(`/system/upgrade`, { account_id }),
    () => ({ ok: true })
  )
}
