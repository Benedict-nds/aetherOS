import { useEffect, useState } from 'react'
import type { ChangeEvent } from 'react'
import { ChevronDown, Plus, Search } from 'lucide-react'
import { Button, StatCard, StatusBadge } from '@/components/ui'
import { getErrorMessage } from '@/lib/api/client'
import { listCategoriesRequest, listMedicinesRequest } from '@/lib/api/medicines'
import type { Medicine, MedicineCategory, StockStatus } from '@/lib/api/types'
import { AddMedicineModal } from '../components/AddMedicineModal'

const TABLE_COLUMNS = ['Medicine', 'Category', 'Batch', 'Expiry', 'Qty', 'Status'] as const

const STOCK_STATUS_LABELS: Record<StockStatus, string> = {
  healthy: 'Healthy',
  low: 'Low Stock',
  critical: 'Critical',
}

const STATUS_FILTER_OPTIONS: FilterOption[] = [
  { label: 'All Statuses', value: '' },
  { label: STOCK_STATUS_LABELS.healthy, value: 'healthy' },
  { label: STOCK_STATUS_LABELS.low, value: 'low' },
  { label: STOCK_STATUS_LABELS.critical, value: 'critical' },
]

// "2026-06-30" -> "Jun 2026". Parsed as a local date so the month can't shift across timezones.
function formatExpiry(isoDate: string) {
  const date = new Date(`${isoDate}T00:00:00`)
  if (Number.isNaN(date.getTime())) return isoDate
  return new Intl.DateTimeFormat('en-GB', { month: 'short', year: 'numeric' }).format(date)
}

function isPastDate(isoDate: string) {
  const date = new Date(`${isoDate}T00:00:00`)
  return !Number.isNaN(date.getTime()) && date < new Date()
}

type FilterOption = { label: string; value: string }

type FilterSelectProps = {
  options: FilterOption[]
  value: string
  onChange: (value: string) => void
}

function FilterSelect({ options, value, onChange }: FilterSelectProps) {
  return (
    <div className="relative">
      <select
        className="h-full min-w-40 appearance-none rounded-lg border border-subtle bg-elevated py-2.5 pl-4 pr-9 text-body text-fg outline-none focus:border-accent"
        value={value}
        onChange={(e: ChangeEvent<HTMLSelectElement>) => onChange(e.target.value)}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <ChevronDown
        className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-muted"
        strokeWidth={1.75}
      />
    </div>
  )
}

export const InventoryPage = () => {
  const [isAddMedicineOpen, setIsAddMedicineOpen] = useState(false)

  const [medicines, setMedicines] = useState<Medicine[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  const [categories, setCategories] = useState<MedicineCategory[]>([])

  const [searchQuery, setSearchQuery] = useState('')
  const [categoryId, setCategoryId] = useState<string>('') // '' = All Categories
  const [statusFilter, setStatusFilter] = useState<string>('') // '' = All Statuses (client-side only)

  // load categories once
  useEffect(() => {
    listCategoriesRequest()
      .then((res) => setCategories(res.data ?? []))
      .catch(() => setCategories([]))
  }, [])

  // fetch medicines whenever search/category changes (debounced)
  useEffect(() => {
    const timeout = setTimeout(() => {
      setIsLoading(true)
      setLoadError(null)
      listMedicinesRequest({
        q: searchQuery || undefined,
        category_id: categoryId ? Number(categoryId) : undefined,
      })
        .then((res) => setMedicines(res.data ?? []))
        .catch((err) => setLoadError(getErrorMessage(err, 'Could not load medicines')))
        .finally(() => setIsLoading(false))
    }, 300)

    return () => clearTimeout(timeout)
  }, [searchQuery, categoryId])

  const refetchMedicines = () => {
    setIsLoading(true)
    setLoadError(null)
    listMedicinesRequest({
      q: searchQuery || undefined,
      category_id: categoryId ? Number(categoryId) : undefined,
    })
      .then((res) => setMedicines(res.data ?? []))
      .catch((err) => setLoadError(getErrorMessage(err, 'Could not load medicines')))
      .finally(() => setIsLoading(false))
  }

  const categoryOptions: FilterOption[] = [
    { label: 'All Categories', value: '' },
    ...categories.map((c) => ({ label: c.name, value: String(c.id) })),
  ]

  // status filter runs on the already-loaded rows; the API has no status query param
  const visibleMedicines = statusFilter
    ? medicines.filter((m) => m.stock_status === statusFilter)
    : medicines

  const countByStatus = (status: StockStatus) =>
    medicines.filter((m) => m.stock_status === status).length

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between gap-4">
        <h1 className="m-0 text-display font-bold text-fg">Inventory</h1>
        <Button variant="primary" onClick={() => setIsAddMedicineOpen(true)}>
          <Plus className="size-4" strokeWidth={2.5} />
          Add Medicine
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Total SKUs" value={medicines.length} hint="across all categories" />
        <StatCard label="Healthy" value={countByStatus('healthy')} hint="well-stocked" />
        <StatCard label="Low stock" value={countByStatus('low')} hint="below reorder point" />
        <StatCard
          label="Critical"
          value={countByStatus('critical')}
          hint="out of stock or expired"
          tone="critical"
        />
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search
            className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted"
            strokeWidth={1.75}
          />
          <input
            type="text"
            placeholder="Search by name, brand, or barcode..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-subtle bg-elevated py-2.5 pl-10 pr-4 text-body text-fg outline-none placeholder:text-muted focus:border-accent"
          />
        </div>
        <FilterSelect options={categoryOptions} value={categoryId} onChange={setCategoryId} />
        <FilterSelect
          options={STATUS_FILTER_OPTIONS}
          value={statusFilter}
          onChange={setStatusFilter}
        />
      </div>

      <div className="overflow-x-auto rounded-[14px] bg-surface">
        <table className="w-full min-w-180 border-collapse text-left">
          <thead>
            <tr className="border-b border-subtle">
              {TABLE_COLUMNS.map((column) => (
                <th
                  key={column}
                  className="px-5 py-3.5 text-caption font-normal uppercase tracking-wider text-muted"
                >
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td className="px-5 py-4 text-body text-muted" colSpan={TABLE_COLUMNS.length}>
                  Loading…
                </td>
              </tr>
            ) : loadError ? (
              <tr>
                <td className="px-5 py-4 text-body text-muted" colSpan={TABLE_COLUMNS.length}>
                  {loadError}
                </td>
              </tr>
            ) : visibleMedicines.length === 0 ? (
              <tr>
                <td className="px-5 py-4 text-body text-muted" colSpan={TABLE_COLUMNS.length}>
                  {medicines.length === 0 ? 'No medicines yet' : 'No medicines match this status'}
                </td>
              </tr>
            ) : (
              visibleMedicines.map((medicine) => (
                <tr key={medicine.id} className="border-b border-subtle last:border-0">
                  <td className="px-5 py-4 text-body text-fg">{medicine.name}</td>
                  <td className="px-5 py-4 text-body text-muted">
                    {medicine.category_name ?? '—'}
                  </td>
                  <td className="px-5 py-4 text-body text-muted">
                    {medicine.nearest_batch_number ?? '—'}
                  </td>
                  <td
                    className={`px-5 py-4 text-body ${
                      medicine.nearest_expiry_date && isPastDate(medicine.nearest_expiry_date)
                        ? 'text-critical'
                        : 'text-fg'
                    }`}
                  >
                    {medicine.nearest_expiry_date
                      ? formatExpiry(medicine.nearest_expiry_date)
                      : '—'}
                  </td>
                  <td className="px-5 py-4 text-body text-fg">
                    {medicine.quantity_on_hand.toLocaleString()}
                  </td>
                  <td className="px-5 py-4">
                    <StatusBadge status={medicine.stock_status}>
                      {STOCK_STATUS_LABELS[medicine.stock_status]}
                    </StatusBadge>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <AddMedicineModal
        open={isAddMedicineOpen}
        onClose={() => setIsAddMedicineOpen(false)}
        categories={categories}
        onSaved={() => {
          setIsAddMedicineOpen(false)
          refetchMedicines()
        }}
      />
    </div>
  )
}
