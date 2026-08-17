import axios from 'axios'
import type { ApiResponse } from './types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

export async function apiGet<T>(path: string): Promise<ApiResponse<T>> {
  const { data } = await api.get<ApiResponse<T>>(path)
  return data
}

export async function apiPost<T>(path: string, body: unknown): Promise<ApiResponse<T>> {
  const { data } = await api.post<ApiResponse<T>>(path, body)
  return data
}
