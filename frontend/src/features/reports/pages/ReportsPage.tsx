import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { LowStockTable } from '../components/LowStockTable'
import { ExpiryTable } from '../components/ExpiryTable'

export const ReportsPage = () => {
  const [tab, setTab] = useState<'low-stock' | 'expiry'>('low-stock')
  const [withinDays, setWithinDays] = useState(90)

  return (
    <div className="flex flex-col gap-6">
      <h1 className="m-0 text-display font-bold text-fg">Reports</h1>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div role="group" aria-label="Report type" className="inline-flex gap-1 rounded-lg border border-subtle bg-surface p-1">
          {([
            { value: 'low-stock', label: 'Low stock' },
            { value: 'expiry', label: 'Expiry' },
          ] as const).map((item) => (
            <button
              key={item.value}
              type="button"
              aria-pressed={tab === item.value}
              aria-controls="report-results"
              onClick={() => setTab(item.value)}
              className={`cursor-pointer rounded-md px-4 py-2 text-body focus-visible:outline-2 focus-visible:outline-accent ${tab === item.value ? 'bg-elevated text-fg' : 'text-muted hover:text-fg'}`}
            >
              {item.label}
            </button>
          ))}
        </div>
        {tab === 'expiry' && (
          <label className="flex items-center gap-3 text-body text-muted">
            Expiry window
            <span className="relative">
              <select
                value={withinDays}
                onChange={(event) => setWithinDays(Number(event.target.value))}
                className="min-w-40 appearance-none rounded-lg border border-subtle bg-elevated py-2.5 pl-4 pr-9 text-body text-fg outline-none focus:border-accent"
              >
                {[30, 60, 90].map((days) => <option key={days} value={days}>{days} days</option>)}
              </select>
              <ChevronDown aria-hidden="true" className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-muted" strokeWidth={1.75} />
            </span>
          </label>
        )}
      </div>
      <div id="report-results">
        {tab === 'low-stock' ? <LowStockTable /> : <ExpiryTable key={withinDays} withinDays={withinDays} />}
      </div>
    </div>
  )
}
