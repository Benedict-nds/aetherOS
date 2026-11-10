import { apiRequest } from './client'
import { endpoints } from './endpoints'
import type { CreateSaleBody, Sale } from './types'

export function createSaleRequest(body: CreateSaleBody) {
  return apiRequest<Sale>(endpoints.sales.create, { method: 'POST', body })
}
