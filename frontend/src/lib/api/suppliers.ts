import { apiRequest } from './client'
import { endpoints } from './endpoints'
import type { CreateSupplierBody, Supplier, SupplierListData, UpdateSupplierBody } from './types'

export function listSuppliersRequest(params: {
  q?: string
  is_active?: boolean
  limit?: number
  offset?: number
} = {}) {
  return apiRequest<SupplierListData>(endpoints.suppliers.list, {
    params: {
      q: params.q || undefined,
      is_active: params.is_active === undefined ? undefined : String(params.is_active),
      limit: params.limit,
      offset: params.offset,
    },
  })
}

export function createSupplierRequest(body: CreateSupplierBody) {
  return apiRequest<Supplier>(endpoints.suppliers.list, { method: 'POST', body })
}

export function updateSupplierRequest(id: number, body: UpdateSupplierBody) {
  return apiRequest<Supplier>(endpoints.suppliers.detail(id), { method: 'PATCH', body })
}

export function deactivateSupplierRequest(id: number) {
  return apiRequest<null>(endpoints.suppliers.detail(id), { method: 'DELETE' })
}
