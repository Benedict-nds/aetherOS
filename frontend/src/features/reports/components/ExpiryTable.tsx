import { useEffect, useState } from 'react'
import {
  Alert,
  StatusBadge,
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TableSkeleton,
} from '@/components/ui'
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
    <div className="flex flex-col gap-3">
      {error ? <Alert variant="destructive">{error}</Alert> : null}
      <Table aria-busy={isLoading}>
        <TableCaption>Expiry report within {withinDays} days, including expired batches</TableCaption>
        <TableHeader>
          <TableRow>
            {COLUMNS.map((column) => (
              <TableHead key={column} scope="col">{column}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableSkeleton columns={COLUMNS.length} />
          ) : rows.length === 0 ? (
            <TableRow>
              <TableCell colSpan={COLUMNS.length} className="text-muted">
                <span role="status">Nothing expiring in {withinDays} days</span>
              </TableCell>
            </TableRow>
          ) : (
            rows.map((row) => (
              <TableRow key={row.batch_id}>
                <TableCell>{row.name}</TableCell>
                <TableCell className="text-muted">{row.batch_number}</TableCell>
                <TableCell>{formatExpiry(row.expiry_date)}</TableCell>
                <TableCell>{row.quantity_on_hand.toLocaleString()}</TableCell>
                <TableCell>
                  <StatusBadge status={RISK[row.bucket].status}>{RISK[row.bucket].label}</StatusBadge>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  )
}
