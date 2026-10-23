import { useEffect, useState } from 'react'
import { StatusBadge } from '@/components/ui'
import { getErrorMessage } from '@/lib/api/client'
import { getExpiryReportRequest } from '@/lib/api/reports'
import type { ExpiryBucket, ExpiryRow, StockStatus } from '@/lib/api/types'

const COLUMNS = ['Medicine', 'Batch', 'Expiry', 'Qty', 'Risk']
const RISK: Record<ExpiryBucket, { status: StockStatus; label: string }> = {
  expired: { status: 'critical', label: 'Expired' },
  '30': { status: 'critical', label: 'Within 30 days' },
  '60': { status: 'low', label: 'Within 60 days' },
  '90': { status: 'healthy', label: 'Within 90 days' },
}

function formatExpiry(isoDate: string) {
  const date = new Date(`${isoDate}T00:00:00`)
  if (Number.isNaN(date.getTime())) return isoDate
  return new Intl.DateTimeFormat('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric',
  }).format(date)
}

// The page keys this component by withinDays so each filter starts with a loading row.
export const ExpiryTable = ({ withinDays }: { withinDays: number }) => {
  const [rows, setRows] = useState<ExpiryRow[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let ignore = false
    getExpiryReportRequest(withinDays)
      .then((res) => {
        if (!ignore) setRows(res.data ?? [])
      })
      .catch((err: unknown) => {
        if (!ignore) setError(getErrorMessage(err, 'Could not load expiry report'))
      })
      .finally(() => {
        if (!ignore) setIsLoading(false)
      })
    return () => { ignore = true }
  }, [withinDays])

  return (
    <div className="overflow-x-auto rounded-[14px] bg-surface">
      <table className="w-full min-w-180 border-collapse text-left" aria-busy={isLoading}>
        <caption className="sr-only">Expiry report within {withinDays} days, including expired batches</caption>
        <thead>
          <tr className="border-b border-subtle">
            {COLUMNS.map((column) => (
              <th key={column} scope="col" className="px-5 py-3.5 text-caption font-normal uppercase tracking-wider text-muted">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {isLoading || error || rows.length === 0 ? (
            <tr>
              <td colSpan={COLUMNS.length} className="px-5 py-4 text-body text-muted">
                <span role={error ? 'alert' : 'status'}>
                  {isLoading ? 'Loading…' : error ?? `Nothing expiring in ${withinDays} days`}
                </span>
              </td>
            </tr>
          ) : rows.map((row) => (
            <tr key={row.batch_id} className="border-b border-subtle last:border-0">
              <td className="px-5 py-4 text-body text-fg">{row.name}</td>
              <td className="px-5 py-4 text-body text-muted">{row.batch_number}</td>
              <td className="px-5 py-4 text-body text-fg">{formatExpiry(row.expiry_date)}</td>
              <td className="px-5 py-4 text-body text-fg">{row.quantity_on_hand.toLocaleString()}</td>
              <td className="px-5 py-4">
                <StatusBadge status={RISK[row.bucket].status}>{RISK[row.bucket].label}</StatusBadge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
