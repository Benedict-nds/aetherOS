import { useEffect, useState } from 'react'
import { StatusBadge } from '@/components/ui'
import { getErrorMessage } from '@/lib/api/client'
import { getLowStockReportRequest } from '@/lib/api/reports'
import type { LowStockRow } from '@/lib/api/types'

const COLUMNS = ['Medicine', 'Category', 'On hand', 'Reorder level', 'Short by', 'Status']

export const LowStockTable = () => {
  const [rows, setRows] = useState<LowStockRow[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let ignore = false
    getLowStockReportRequest()
      .then((res) => {
        if (!ignore) setRows(res.data ?? [])
      })
      .catch((err: unknown) => {
        if (!ignore) setError(getErrorMessage(err, 'Could not load low stock report'))
      })
      .finally(() => {
        if (!ignore) setIsLoading(false)
      })
    return () => { ignore = true }
  }, [])

  return (
    <div className="overflow-x-auto rounded-[14px] bg-surface">
      <table className="w-full min-w-180 border-collapse text-left" aria-busy={isLoading}>
        <caption className="sr-only">Low stock report</caption>
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
                  {isLoading ? 'Loading…' : error ?? 'Nothing below reorder level'}
                </span>
              </td>
            </tr>
          ) : rows.map((row) => (
            <tr key={row.medicine_id} className="border-b border-subtle last:border-0">
              <td className="px-5 py-4 text-body text-fg">{row.name}</td>
              <td className="px-5 py-4 text-body text-muted">{row.category_name ?? '—'}</td>
              <td className="px-5 py-4 text-body text-fg">{row.quantity_on_hand.toLocaleString()}</td>
              <td className="px-5 py-4 text-body text-fg">{row.reorder_level.toLocaleString()}</td>
              <td className="px-5 py-4 text-body text-fg">{Math.max(0, row.reorder_level - row.quantity_on_hand).toLocaleString()}</td>
              <td className="px-5 py-4">
                <StatusBadge status={row.quantity_on_hand === 0 ? 'critical' : 'low'}>
                  {row.quantity_on_hand === 0 ? 'Critical' : 'Low Stock'}
                </StatusBadge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
