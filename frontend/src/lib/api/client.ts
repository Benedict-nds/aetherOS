import axios from 'axios'
import type { ApiResponse } from './types'
import { clearToken, getToken } from './auth/token'
import { endpoints } from './endpoints'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

let onUnauthorized: (() => void) | null = null

export function setOnUnauthorized(handler: (() => void) | null) {
  onUnauthorized = handler
}

api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const isLogin = error.config?.url === endpoints.auth.login
    if (status === 401 && !isLogin) {
      clearToken()
      onUnauthorized?.()
    }
    return Promise.reject(error)
  },
)

export class ApiError extends Error {
  status: number
  body: ApiResponse<unknown> | null

  constructor(status: number, body: ApiResponse<unknown> | null) {
    super(body?.message || 'Request failed')
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

type ApiRequestOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  params?: Record<string, string | number | undefined>
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<ApiResponse<T>> {
  try {
    const { data } = await api.request<ApiResponse<T>>({
      url: path,
      method: options.method ?? 'GET',
      data: options.body,
      params: options.params,
    })
    return data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const body = (error.response?.data ?? null) as ApiResponse<unknown> | null
      throw new ApiError(error.response?.status ?? 0, body)
    }
    throw error
  }
}

export function getErrorMessage(error: unknown, fallback = 'Request failed'): string {
  if (error instanceof ApiError) {
    if (error.body?.message) return error.body.message
    if (error.body?.errors.length) return error.body.errors.join(', ')
    return fallback
  }
  if (error instanceof Error && error.message) return error.message
  return fallback
}