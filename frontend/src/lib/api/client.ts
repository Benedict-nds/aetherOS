import axios from 'axios'
import type { ApiResponse, AuthUser, LoginData } from './types'
import { clearToken, getToken } from './auth/token'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

let onUnauthorized: (() => void) | null = null

export function setOnUnauthorized(handler: (() => void) | null) {
  onUnauthorized = handler
}

api.interceptors.request.use((config)=>{
  const token = getToken()

  if (token) config.headers.Authorization =  `Bearer ${token}`

  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) =>{
    const status = error.response?.status
    const url = `${error.config?.baseURL ?? ''}${error.config?.url ?? ''}`
    const isLogin = url.includes('/api/auth/login')
    if (status === 401 && !isLogin){
      clearToken()
      onUnauthorized?.()
    }
    return Promise.reject(error)
  },
)

export async function apiGet<T>(path: string): Promise<ApiResponse<T>> {
  const { data } = await api.get<ApiResponse<T>>(path)
  return data
}

export async function apiPost<T>(path: string, body?: unknown): Promise<ApiResponse<T>> {
  const { data } = await api.post<ApiResponse<T>>(path, body)
  return data
}


/**
 *  Auth Service API (Move to dedecated folders later)
 */

export function loginRequest(email: string, password: string){
  return apiPost<LoginData>('/api/auth/login', {email, password})
}

export function getMeRequest(){
  return apiGet<AuthUser>('/api/auth/me')
}

export function logoutRequest() {
  return apiPost<null>('/api/auth/logout')
}

export function getErrorMessage(error: unknown, fallback = 'Invalid credentials'): string {
  if (axios.isAxiosError(error)){
    const message = (error.response?.data as ApiResponse<unknown> | undefined)?.message
    if (message) return message
  }

  if (error instanceof Error && error.message) return error.message
  return fallback
}