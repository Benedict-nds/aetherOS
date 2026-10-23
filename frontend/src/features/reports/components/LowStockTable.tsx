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
    <div className="flex flex-col gap-3">
      {error ? <Alert variant="destructive">{error}</Alert> : null}
      <Table aria-busy={isLoading}>
        <TableCaption>Low stock report</TableCaption>
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
                <span role="status">Nothing below reorder level</span>
              </TableCell>
            </TableRow>
          ) : (
            rows.map((row) => (
              <TableRow key={row.medicine_id}>
                <TableCell>{row.name}</TableCell>
                <TableCell className="text-muted">{row.category_name ?? '—'}</TableCell>
                <TableCell>{row.quantity_on_hand.toLocaleString()}</TableCell>
                <TableCell>{row.reorder_level.toLocaleString()}</TableCell>
                <TableCell>
                  {Math.max(0, row.reorder_level - row.quantity_on_hand).toLocaleString()}
                </TableCell>
                <TableCell>
                  <StatusBadge status={row.quantity_on_hand === 0 ? 'critical' : 'low'}>
                    {row.quantity_on_hand === 0 ? 'Critical' : 'Low Stock'}
                  </StatusBadge>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  )
}
