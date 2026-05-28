import http, { mockOr } from './axios'

export const inviteApi = {
  summary: () => mockOr(
    () => http.get('/invite/summary'),
    () => ({
      uid: 1401,
      level: 1,
      rebate_pct: 10,
      total_rebate: 0,
      invite_link: `${location.origin}/register?code=1401`
    })
  ),
  records: () => mockOr(
    () => http.get('/invite/records'),
    () => [] as Array<{ id: number; invitee_uid: number; created_at: string; reward: number }>
  ),
  withdraw: () => mockOr(
    () => http.post('/invite/withdraw'),
    () => ({ ok: true })
  )
}
