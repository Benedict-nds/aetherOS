import { useEffect, useState } from 'react'
import { Plus, Search } from 'lucide-react'
import {
  Alert,
  Button,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  StatCard,
  StatusBadge,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TableSkeleton,
} from '@/components/ui'
import { getErrorMessage } from '@/lib/api/client'
import { listCategoriesRequest, listMedicinesRequest } from '@/lib/api/medicines'
import type { Medicine, MedicineCategory, StockStatus } from '@/lib/api/types'
import { AddMedicineModal } from '../components/AddMedicineModal'

const TABLE_COLUMNS = ['Medicine', 'Category', 'Batch', 'Expiry', 'Qty', 'Status'] as const
const ALL_FILTER = 'all'

const STOCK_STATUS_LABELS: Record<StockStatus, string> = {
  healthy: 'Healthy',
  low: 'Low Stock',
  critical: 'Critical',
}

const STATUS_FILTER_OPTIONS: FilterOption[] = [
  { label: 'All Statuses', value: ALL_FILTER },
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
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-auto min-w-40">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {options.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

export const InventoryPage = () => {
  const [isAddMedicineOpen, setIsAddMedicineOpen] = useState(false)

  const [medicines, setMedicines] = useState<Medicine[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  const [categories, setCategories] = useState<MedicineCategory[]>([])

  const [searchQuery, setSearchQuery] = useState('')
  const [categoryId, setCategoryId] = useState(ALL_FILTER)
  const [statusFilter, setStatusFilter] = useState(ALL_FILTER)

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
        category_id: categoryId === ALL_FILTER ? undefined : Number(categoryId),
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
      category_id: categoryId === ALL_FILTER ? undefined : Number(categoryId),
    })
      .then((res) => setMedicines(res.data ?? []))
      .catch((err) => setLoadError(getErrorMessage(err, 'Could not load medicines')))
      .finally(() => setIsLoading(false))
  }

  const categoryOptions: FilterOption[] = [
    { label: 'All Categories', value: ALL_FILTER },
    ...categories.map((c) => ({ label: c.name, value: String(c.id) })),
  ]

  // status filter runs on the already-loaded rows; the API has no status query param
  const visibleMedicines =
    statusFilter === ALL_FILTER
      ? medicines
      : medicines.filter((m) => m.stock_status === statusFilter)

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
            className="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-muted"
            strokeWidth={1.75}
          />
          <Input
            type="search"
            placeholder="Search by name, brand, or barcode..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="py-2.5 pr-4 pl-10"
          />
        </div>
        <FilterSelect options={categoryOptions} value={categoryId} onChange={setCategoryId} />
        <FilterSelect
          options={STATUS_FILTER_OPTIONS}
          value={statusFilter}
          onChange={setStatusFilter}
        />
      </div>

      {loadError ? <Alert variant="destructive">{loadError}</Alert> : null}

      <Table>
        <TableHeader>
          <TableRow>
            {TABLE_COLUMNS.map((column) => (
              <TableHead key={column}>{column}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableSkeleton columns={TABLE_COLUMNS.length} />
          ) : visibleMedicines.length === 0 ? (
            <TableRow>
              <TableCell colSpan={TABLE_COLUMNS.length} className="text-muted">
                {medicines.length === 0 ? 'No medicines yet' : 'No medicines match this status'}
              </TableCell>
            </TableRow>
          ) : (
            visibleMedicines.map((medicine) => (
              <TableRow key={medicine.id}>
                <TableCell>{medicine.name}</TableCell>
                <TableCell className="text-muted">{medicine.category_name ?? '—'}</TableCell>
                <TableCell className="text-muted">{medicine.nearest_batch_number ?? '—'}</TableCell>
                <TableCell
                  className={
                    medicine.nearest_expiry_date && isPastDate(medicine.nearest_expiry_date)
                      ? 'text-critical'
                      : undefined
                  }
                >
                  {medicine.nearest_expiry_date
                    ? formatExpiry(medicine.nearest_expiry_date)
                    : '—'}
                </TableCell>
                <TableCell>{medicine.quantity_on_hand.toLocaleString()}</TableCell>
                <TableCell>
                  <StatusBadge status={medicine.stock_status}>
                    {STOCK_STATUS_LABELS[medicine.stock_status]}
                  </StatusBadge>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>

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
