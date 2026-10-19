import { apiRequest } from './client'
import { endpoints } from './endpoints'
import type { CreateSaleBody } from './types'

export function createSaleRequest(body: CreateSaleBody) {
  return apiRequest<unknown>(endpoints.sales.create, { method: 'POST', body })
}
