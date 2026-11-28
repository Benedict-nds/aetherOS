import { expect, it, vi } from 'vitest'
import { apiRequest } from '@/lib/api/client'
import { createSaleRequest } from '@/lib/api/sales'

vi.mock('@/lib/api/client', () => ({ apiRequest: vi.fn() }))

it('posts payment and tendered amount unchanged through the shared client', () => {
  const body = { payment_method: 'cash' as const, amount_paid: 50, lines: [{ medicine_id: 7, quantity: 2 }] }
  createSaleRequest(body)
  expect(apiRequest).toHaveBeenCalledWith('/api/sales', { method: 'POST', body })
})
