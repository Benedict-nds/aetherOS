import { useState } from 'react'
import { ChevronDown, Plus, Search } from 'lucide-react'
import { Button, StatCard, StatusBadge } from '@/components/ui'
import { AddMedicineModal } from '../components/AddMedicineModal'

type InventoryStatus = 'healthy' | 'low' | 'critical'

type InventoryRow = {
  name: string
  category: string
  batch: string
  expiry: string
  expiryCritical?: boolean
  qty: string
  status: InventoryStatus
  statusLabel: string
}

const ROWS: InventoryRow[] = [
  {
    name: 'Amlodipine 5mg',
    category: 'Cardiovascular',
    batch: 'AML-7788',
    expiry: 'Jun 2026',
    qty: '175',
    status: 'healthy',
    statusLabel: 'Healthy',
  },
  {
    name: 'Amoxicillin 500mg',
    category: 'Antibiotics',
    batch: 'AMX-2231',
    expiry: 'Mar 2026',
    qty: '1,240',
    status: 'healthy',
    statusLabel: 'Healthy',
  },
  {
    name: 'Atorvastatin 20mg',
    category: 'Cardiovascular',
    batch: 'ATV-4420',
    expiry: 'Aug 2026',
    qty: '210',
    status: 'low',
    statusLabel: 'Low Stock',
  },
  {
    name: 'Azithromycin 250mg',
    category: 'Antibiotics',
    batch: 'AZM-6640',
    expiry: 'Dec 2025',
    expiryCritical: true,
    qty: '38',
    status: 'critical',
    statusLabel: 'Critical',
  },
  {
    name: 'Metformin 850mg',
    category: 'Antidiabetic',
    batch: 'MET-1180',
    expiry: 'May 2026',
    qty: '90',
    status: 'critical',
    statusLabel: 'Critical',
  },
  {
    name: 'Insulin Glargine',
    category: 'Antidiabetic',
    batch: 'INS-3320',
    expiry: 'Jan 2026',
    qty: '52',
    status: 'low',
    statusLabel: 'Low Stock',
  },
]

const TABLE_COLUMNS = ['Medicine', 'Category', 'Batch', 'Expiry', 'Qty', 'Status'] as const

function FilterSelect({ label, options }: { label: string; options: string[] }) {
  return (
    <div className="relative">
      <select
        className="h-full min-w-40 appearance-none rounded-lg border border-subtle bg-elevated py-2.5 pl-4 pr-9 text-body text-fg outline-none focus:border-accent"
        defaultValue={label}
      >
        <option value={label}>{label}</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
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
        <StatCard label="Total SKUs" value={15} hint="across all categories" />
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
            className="w-full rounded-lg border border-subtle bg-elevated py-2.5 pl-10 pr-4 text-body text-fg outline-none placeholder:text-muted focus:border-accent"
          />
        </div>
        <FilterSelect
          label="All Categories"
          options={['Cardiovascular', 'Antibiotics', 'Antidiabetic']}
        />
        <FilterSelect label="All Statuses" options={['Healthy', 'Low Stock', 'Critical']} />
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
            {ROWS.map((row) => (
              <tr key={row.batch} className="border-b border-subtle last:border-0">
                <td className="px-5 py-4 text-body text-fg">{row.name}</td>
                <td className="px-5 py-4 text-body text-muted">{row.category}</td>
                <td className="px-5 py-4 text-body text-muted">{row.batch}</td>
                <td
                  className={`px-5 py-4 text-body ${row.expiryCritical ? 'text-critical' : 'text-fg'}`}
                >
                  {row.expiry}
                </td>
                <td className="px-5 py-4 text-body text-fg">{row.qty}</td>
                <td className="px-5 py-4">
                  <StatusBadge status={row.status}>{row.statusLabel}</StatusBadge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <AddMedicineModal
        open={isAddMedicineOpen}
        onClose={() => setIsAddMedicineOpen(false)}
        onSave={(medicine) => {
          // TODO: wire up to your actual create-medicine API/mutation
          console.log('New medicine:', medicine)
        }}
      />
    </div>
  )
}