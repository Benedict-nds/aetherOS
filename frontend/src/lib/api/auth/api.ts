import { apiRequest } from '../client'
import { endpoints } from '../endpoints'
import type { AuthUser, LoginData } from '../types'

export function loginRequest(email: string, password: string) {
  return apiRequest<LoginData>(endpoints.auth.login, {
    method: 'POST',
    body: { email, password },
  })
}

export function getMeRequest() {
  return apiRequest<AuthUser>(endpoints.auth.me)
}

export function logoutRequest() {
  return apiRequest<null>(endpoints.auth.logout, { method: 'POST' })
}