import { beforeEach, expect, it, vi } from 'vitest'
import { apiRequest } from '@/lib/api/client'
import { createSupplierRequest, deactivateSupplierRequest, listSuppliersRequest, updateSupplierRequest } from '@/lib/api/suppliers'

vi.mock('@/lib/api/client', () => ({ apiRequest: vi.fn() }))
beforeEach(() => { vi.clearAllMocks() })

it('sends false explicitly for inactive suppliers and preserves pagination', () => {
  listSuppliersRequest({ q: 'Nova', is_active: false, limit: 50, offset: 50 })
  expect(apiRequest).toHaveBeenCalledWith('/api/suppliers', {
    params: { q: 'Nova', is_active: 'false', limit: 50, offset: 50 },
  })
})

it('omits the active filter when showing all suppliers', () => {
  listSuppliersRequest()
  expect(apiRequest).toHaveBeenCalledWith('/api/suppliers', {
    params: { q: undefined, is_active: undefined, limit: undefined, offset: undefined },
  })
})

it('uses POST, PATCH and DELETE for supplier mutations', () => {
  createSupplierRequest({ name: 'Nova' })
  updateSupplierRequest(7, { phone: null })
  deactivateSupplierRequest(7)
  expect(apiRequest).toHaveBeenNthCalledWith(1, '/api/suppliers', { method: 'POST', body: { name: 'Nova' } })
  expect(apiRequest).toHaveBeenNthCalledWith(2, '/api/suppliers/7', { method: 'PATCH', body: { phone: null } })
  expect(apiRequest).toHaveBeenNthCalledWith(3, '/api/suppliers/7', { method: 'DELETE' })
})
