import { act } from 'react'
import { createRoot } from 'react-dom/client'
import type { Root } from 'react-dom/client'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { SuppliersPage } from '@/features/suppliers/pages/SuppliersPage'
import * as api from '@/lib/api/suppliers'
import type { Supplier } from '@/lib/api/types'

vi.mock('@/lib/api/suppliers')
const auth = vi.hoisted(() => ({ user: { role: 'owner' } }))
vi.mock('@/app/useAuth', () => ({ useAuth: () => auth }))

const supplier: Supplier = {
  id: 1, name: 'Nova Health', contact_person: 'Ada', phone: '0300000000',
  email: 'ada@example.com', address: 'Accra', is_active: true,
  created_at: '2026-11-10T12:00:00Z', updated_at: '2026-11-10T12:00:00Z',
}
const envelope = <T,>(data: T) => ({ success: true, data, message: 'OK', errors: [] })
let root: Root
let host: HTMLDivElement

function button(name: string) {
  const match = [...document.querySelectorAll('button')].find((element) =>
    (element.getAttribute('aria-label') ?? element.textContent)?.trim() === name)
  if (!match) throw new Error(`Button not found: ${name}`)
  return match
}
async function click(name: string) { await act(async () => { button(name).click() }) }
async function input(id: string, value: string) {
  await act(async () => {
    const element = document.querySelector<HTMLInputElement>(id)!
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(element, value)
    element.dispatchEvent(new Event('input', { bubbles: true }))
  })
}
async function submit() {
  await act(async () => { document.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })) })
}
async function render() { await act(async () => { root.render(<SuppliersPage />) }) }

beforeEach(() => {
  vi.clearAllMocks()
  auth.user.role = 'owner'
  host = document.createElement('div')
  document.body.append(host)
  root = createRoot(host)
  vi.mocked(api.listSuppliersRequest).mockResolvedValue(envelope({ items: [supplier], total: 1, limit: 50, offset: 0 }))
  vi.mocked(api.createSupplierRequest).mockResolvedValue(envelope(supplier))
  vi.mocked(api.updateSupplierRequest).mockResolvedValue(envelope(supplier))
  vi.mocked(api.deactivateSupplierRequest).mockResolvedValue(envelope(null))
})
afterEach(async () => { await act(async () => root.unmount()); host.remove(); vi.useRealTimers() })

describe('Suppliers', () => {
  it('loads active suppliers and hides management actions from staff', async () => {
    auth.user.role = 'staff'
    await render()
    expect(api.listSuppliersRequest).toHaveBeenCalledWith({ q: '', is_active: true, limit: 50, offset: 0 })
    expect(host.textContent).toContain('Nova Health')
    expect(host.textContent).not.toContain('Add supplier')
    expect(host.textContent).not.toContain('Deactivate')
    expect(host.textContent).not.toContain('Edit')
  })

  it('creates a supplier with trimmed fields and refreshes the list', async () => {
    await render()
    vi.mocked(api.listSuppliersRequest).mockResolvedValue(envelope({ items: [{ ...supplier, name: 'New Supplier' }], total: 1, limit: 50, offset: 0 }))
    await click('Add supplier')
    await input('#supplier-name', '  New Supplier  ')
    await input('#supplier-email', 'new@example.com')
    await submit()
    expect(api.createSupplierRequest).toHaveBeenCalledWith({ name: 'New Supplier', contact_person: null, phone: null, email: 'new@example.com', address: null })
    expect(api.listSuppliersRequest).toHaveBeenCalledTimes(2)
    expect(document.querySelector('[role="dialog"]')).toBeNull()
    expect(host.textContent).toContain('New Supplier')
  })

  it('edits a supplier and sends null when optional contact details are cleared', async () => {
    await render()
    await click('Edit Nova Health')
    expect(document.querySelector<HTMLInputElement>('#supplier-name')?.value).toBe('Nova Health')
    await input('#supplier-contact_person', '')
    await submit()
    expect(api.updateSupplierRequest).toHaveBeenCalledWith(1, expect.objectContaining({ contact_person: null }))
    expect(api.listSuppliersRequest).toHaveBeenCalledTimes(2)
  })

  it('requires confirmation before deactivating and refreshes after success', async () => {
    await render()
    await click('Deactivate Nova Health')
    expect(api.deactivateSupplierRequest).not.toHaveBeenCalled()
    vi.mocked(api.listSuppliersRequest).mockResolvedValue(envelope({ items: [], total: 0, limit: 50, offset: 0 }))
    await click('Deactivate')
    expect(api.deactivateSupplierRequest).toHaveBeenCalledWith(1)
    expect(api.listSuppliersRequest).toHaveBeenCalledTimes(2)
    expect(host.textContent).not.toContain('Nova Health')
  })

  it('keeps an edit dialog and entered values after an API failure', async () => {
    vi.mocked(api.updateSupplierRequest).mockRejectedValue(new Error('Supplier name already exists'))
    await render()
    await click('Edit Nova Health')
    await input('#supplier-name', 'Duplicate')
    await submit()
    expect(document.querySelector('[role="dialog"]')?.textContent).toContain('Supplier name already exists')
    expect(document.querySelector<HTMLInputElement>('#supplier-name')?.value).toBe('Duplicate')
    expect(api.listSuppliersRequest).toHaveBeenCalledTimes(1)
  })

  it('debounces searches and ignores a late response from a previous search', async () => {
    let resolveOld: (value: Awaited<ReturnType<typeof api.listSuppliersRequest>>) => void = () => {}
    vi.mocked(api.listSuppliersRequest).mockReturnValueOnce(new Promise((resolve) => { resolveOld = resolve }))
    vi.mocked(api.listSuppliersRequest).mockResolvedValue(envelope({ items: [], total: 0, limit: 50, offset: 0 }))
    vi.useFakeTimers()
    await render()
    await input('[aria-label="Search suppliers"]', 'missing')
    expect(api.listSuppliersRequest).toHaveBeenCalledTimes(1)
    await act(async () => { await vi.advanceTimersByTimeAsync(300) })
    expect(api.listSuppliersRequest).toHaveBeenLastCalledWith(expect.objectContaining({ q: 'missing', offset: 0 }))
    await act(async () => { resolveOld(envelope({ items: [supplier], total: 1, limit: 50, offset: 0 })) })
    expect(host.textContent).toContain('No suppliers match your search')
    expect(host.textContent).not.toContain('Nova Health')
  })

  it('shows list errors and lets the user retry', async () => {
    vi.mocked(api.listSuppliersRequest).mockRejectedValueOnce(new Error('Could not connect'))
    await render()
    expect(host.querySelector('[role="alert"]')?.textContent).toBe('Could not connect')
    await click('Try again')
    expect(host.textContent).toContain('Nova Health')
  })
})
