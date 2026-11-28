import { act } from 'react'
import { createRoot } from 'react-dom/client'
import type { Root } from 'react-dom/client'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { PosPage } from '@/features/pos/pages/PosPage'
import { ApiError } from '@/lib/api/client'
import { listMedicineBatchesRequest, listMedicinesRequest } from '@/lib/api/medicines'
import { createSaleRequest } from '@/lib/api/sales'
import type { Medicine, Sale } from '@/lib/api/types'

vi.mock('@/lib/api/medicines')
vi.mock('@/lib/api/sales')

const medicine: Medicine = {
  id: 1, name: 'Paracetamol', generic_name: null, brand_name: null,
  category_id: null, category_name: null, barcode: null, dosage_form: null,
  strength: null, unit: null, reorder_level: 2, is_active: true,
  quantity_on_hand: 10, nearest_batch_number: 'B1', nearest_expiry_date: '2099-01-01',
  stock_status: 'healthy', created_at: '', updated_at: '',
}
const sale: Sale = {
  id: 42, payment_method: 'cash', total: '12.50', amount_paid: '50.00', change_due: '37.50',
  user_id: 7, cashier: { id: 7, full_name: 'Ada Cashier' }, created_at: '2026-11-10T12:30:00Z',
  lines: [
    { id: 1, medicine_id: 1, medicine_name: 'Paracetamol', batch_id: 1, batch_number: 'B1', quantity: 1, unit_price: '5.00', line_total: '5.00' },
    { id: 2, medicine_id: 1, medicine_name: 'Paracetamol', batch_id: 2, batch_number: 'B2', quantity: 1, unit_price: '7.50', line_total: '7.50' },
  ],
}
const envelope = <T,>(data: T) => ({ success: true, data, message: 'OK', errors: [] })
let root: Root
let host: HTMLDivElement

function button(name: string) {
  const match = [...host.querySelectorAll('button')].find((element) =>
    (element.getAttribute('aria-label') ?? element.textContent)?.trim() === name)
  if (!match) throw new Error(`Button not found: ${name}`)
  return match
}
async function click(name: string) { await act(async () => { button(name).click() }) }
async function tender(value: string) {
  await act(async () => {
    const element = host.querySelector<HTMLInputElement>('#tendered')!
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(element, value)
    element.dispatchEvent(new Event('input', { bubbles: true }))
  })
}
async function payment(name: string) {
  await act(async () => { button(name).dispatchEvent(new MouseEvent('mousedown', { bubbles: true, button: 0 })) })
}
async function addMedicine() {
  await act(async () => {
    const product = [...host.querySelectorAll('button')].find((element) => element.textContent?.startsWith('Paracetamol'))!
    product.click()
  })
}
async function renderCart() {
  await act(async () => { root.render(<PosPage />) })
  await addMedicine()
}

beforeEach(() => {
  vi.clearAllMocks()
  host = document.createElement('div')
  document.body.append(host)
  root = createRoot(host)
  vi.mocked(listMedicinesRequest).mockResolvedValue(envelope([medicine]))
  vi.mocked(listMedicineBatchesRequest).mockResolvedValue(envelope([
    { id: 1, status: 'active', quantity_on_hand: 10, expiry_date: '2099-01-01', selling_price: '10.00' },
  ]))
  vi.mocked(createSaleRequest).mockResolvedValue(envelope(sale))
})
afterEach(async () => { await act(async () => root.unmount()); host.remove() })

describe('POS payment and receipt', () => {
  it('sends cash tendered and shows authoritative receipt totals and batch lines', async () => {
    await renderCart()
    await click('Increase Paracetamol')
    await tender('50')
    await click('Charge sale')
    expect(createSaleRequest).toHaveBeenCalledWith({ payment_method: 'cash', amount_paid: 50, lines: [{ medicine_id: 1, quantity: 2 }] })
    expect(host.textContent).toContain('Sale receipt #42')
    expect(host.textContent).toContain('Ada Cashier')
    expect(host.querySelector('time')?.dateTime).toBe(sale.created_at)
    expect([...host.querySelectorAll('tbody tr')].map((row) => row.textContent)).toEqual([
      'ParacetamolB11GH₵ 5.00GH₵ 5.00', 'ParacetamolB21GH₵ 7.50GH₵ 7.50',
    ])
    expect(host.querySelector('dl')?.textContent).toContain('TotalGH₵ 12.50Amount paidGH₵ 50.00Change dueGH₵ 37.50Payment methodCash')
    expect(listMedicinesRequest).toHaveBeenCalledTimes(2)
  })

  it.each(['', '0'])('omits cash amount_paid when tendered is %j', async (amount) => {
    await renderCart()
    await tender(amount)
    await click('Charge sale')
    expect(createSaleRequest).toHaveBeenCalledWith({ payment_method: 'cash', lines: [{ medicine_id: 1, quantity: 1 }] })
  })

  it.each([['MoMo', 'momo'], ['Card', 'card']])('omits amount_paid for %s even if cash tendered was entered', async (label, method) => {
    await renderCart()
    await tender('50')
    await payment(label)
    expect(host.querySelector('#tendered')).toBeNull()
    await click('Charge sale')
    expect(createSaleRequest).toHaveBeenCalledWith({ payment_method: method, lines: [{ medicine_id: 1, quantity: 1 }] })
  })

  it('keeps the cart and tendered amount after 422 and allows a corrected retry', async () => {
    vi.mocked(createSaleRequest).mockRejectedValueOnce(new ApiError(422, { success: false, data: null, message: 'Amount paid is less than sale total', errors: [] }))
    await renderCart()
    await tender('1')
    await click('Charge sale')
    expect(host.querySelector('[role="alert"]')?.textContent).toBe('Amount paid is less than sale total')
    expect(host.querySelector<HTMLInputElement>('#tendered')?.value).toBe('1')
    expect(button('Remove Paracetamol')).toBeTruthy()
    expect(host.textContent).not.toContain('Sale receipt')
    expect(listMedicinesRequest).toHaveBeenCalledTimes(1)
    await tender('50')
    await click('Charge sale')
    expect(host.textContent).toContain('Sale receipt #42')
  })

  it('clears the completed cart and returns to a fresh sale', async () => {
    await renderCart()
    await click('Charge sale')
    await click('New sale')
    expect(host.textContent).toContain('Cart is empty')
    expect(button('Charge sale').disabled).toBe(true)
    expect(host.querySelector<HTMLInputElement>('#tendered')?.value).toBe('')
    expect(document.querySelector('.sale-receipt-print')).toBeNull()
    expect(createSaleRequest).toHaveBeenCalledTimes(1)
  })

  it('calls browser printing and isolates a complete print copy from the application shell', async () => {
    const print = vi.spyOn(window, 'print').mockImplementation(() => {})
    await renderCart()
    await click('Charge sale')
    const printCopy = document.querySelector('.sale-receipt-print')!
    expect(printCopy.parentElement).toBe(document.body)
    expect(printCopy.textContent).toContain('Sale receipt #42')
    expect(printCopy.textContent).toContain('Change dueGH₵ 37.50')
    expect(printCopy.querySelector('button')).toBeNull()
    await click('Print')
    expect(print).toHaveBeenCalledTimes(1)
  })

  it('prevents duplicate charges and locks the cart while a request is pending', async () => {
    let resolveSale: (value: Awaited<ReturnType<typeof createSaleRequest>>) => void = () => {}
    vi.mocked(createSaleRequest).mockReturnValue(new Promise((resolve) => { resolveSale = resolve }))
    await renderCart()
    await act(async () => {
      const charge = button('Charge sale')
      charge.click()
      charge.click()
    })
    expect(createSaleRequest).toHaveBeenCalledTimes(1)
    expect(host.querySelector('fieldset')?.disabled).toBe(true)
    expect(button('Charging…').disabled).toBe(true)
    await act(async () => { resolveSale(envelope(sale)) })
    expect(host.textContent).toContain('Sale receipt #42')
  })
})
