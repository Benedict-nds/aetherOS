import { useEffect, useState } from 'react'
import type { ChangeEvent } from 'react'
import { ChevronDown, Plus, Search } from 'lucide-react'
import { Button, StatCard, StatusBadge } from '@/components/ui'
import {
  getErrorMessage,
  listCategoriesRequest,
  listMedicinesRequest,
} from '../../../lib/api/client'
import type { Medicine, MedicineCategory } from '../../../lib/api/types'
import { AddMedicineModal } from '../components/AddMedicineModal'

const TABLE_COLUMNS = ['Medicine', 'Category', 'Batch', 'Expiry', 'Qty', 'Status'] as const

type FilterOption = { label: string; value: string }

type FilterSelectProps = {
  label: string
  options: FilterOption[]
  value?: string
  onChange?: (value: string) => void
}

function FilterSelect({ label, options, value, onChange }: FilterSelectProps) {
  const isControlled = value !== undefined

  return (
    <div className="relative">
      {isControlled ? (
        <select
          className="h-full min-w-40 appearance-none rounded-lg border border-subtle bg-elevated py-2.5 pl-4 pr-9 text-body text-fg outline-none focus:border-accent"
          value={value}
          onChange={(e: ChangeEvent<HTMLSelectElement>) => onChange?.(e.target.value)}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      ) : (
        <select
          className="h-full min-w-40 appearance-none rounded-lg border border-subtle bg-elevated py-2.5 pl-4 pr-9 text-body text-fg outline-none focus:border-accent"
          defaultValue={label}
        >
          <option value={label}>{label}</option>
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      )}
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
        <StatCard label="Healthy" value={9} hint="well-stocked" />
        <StatCard label="Low stock" value={4} hint="below reorder point" />
        <StatCard label="Critical" value={2} hint="out of stock or expired" tone="critical" />
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
        <FilterSelect
          label="All Categories"
          options={categoryOptions}
          value={categoryId}
          onChange={setCategoryId}
        />
        {/* Visual only — batch status does not exist in the API yet, so this does not filter. */}
        <FilterSelect
          label="All Statuses"
          options={[
            { label: 'Healthy', value: 'Healthy' },
            { label: 'Low Stock', value: 'Low Stock' },
            { label: 'Critical', value: 'Critical' },
          ]}
        />
      </div>

      <div className="overflow-x-auto rounded-[14px] bg-surface">
        <table className="w-full min-w-[720px] border-collapse text-left">
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
            ) : medicines.length === 0 ? (
              <tr>
                <td className="px-5 py-4 text-body text-muted" colSpan={TABLE_COLUMNS.length}>
                  No medicines yet
                </td>
              </tr>
            ) : (
              medicines.map((medicine) => (
                <tr key={medicine.id} className="border-b border-subtle last:border-0">
                  <td className="px-5 py-4 text-body text-fg">{medicine.name}</td>
                  <td className="px-5 py-4 text-body text-muted">
                    {medicine.category_name ?? '—'}
                  </td>
                  <td className="px-5 py-4 text-body text-muted">—</td>
                  <td className="px-5 py-4 text-body text-fg">—</td>
                  <td className="px-5 py-4 text-body text-fg">—</td>
                  <td className="px-5 py-4">
                    <StatusBadge status="healthy">Active</StatusBadge>
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
