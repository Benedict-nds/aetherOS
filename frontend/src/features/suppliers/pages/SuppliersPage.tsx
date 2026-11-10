import { useEffect, useState } from 'react'
import { Plus, Search } from 'lucide-react'
import { useAuth } from '@/app/useAuth'
import {
  Alert, Button, Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader,
  DialogTitle, Input, Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
  StatusBadge, Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui'
import { getErrorMessage } from '@/lib/api/client'
import { deactivateSupplierRequest, listSuppliersRequest } from '@/lib/api/suppliers'
import type { Supplier, SupplierListData } from '@/lib/api/types'
import { SupplierFormDialog } from '../components/SupplierFormDialog'

const PAGE_SIZE = 50
type StatusFilter = 'active' | 'inactive' | 'all'

function DeactivateDialog({ supplier, onClose, onSaved }: {
  supplier: Supplier
  onClose: () => void
  onSaved: () => void
}) {
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleDeactivate() {
    if (isSaving) return
    setIsSaving(true)
    setError(null)
    try {
      await deactivateSupplierRequest(supplier.id)
      onSaved()
    } catch (err) {
      setError(getErrorMessage(err, 'Could not deactivate supplier'))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={(open) => { if (!open && !isSaving) onClose() }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Deactivate supplier?</DialogTitle>
          <DialogDescription>{supplier.name} will be marked inactive. Their existing records will be kept.</DialogDescription>
        </DialogHeader>
        {error && <Alert variant="destructive">{error}</Alert>}
        <DialogFooter>
          <Button variant="secondary" disabled={isSaving} onClick={onClose}>Cancel</Button>
          <Button disabled={isSaving} onClick={handleDeactivate}>{isSaving ? 'Deactivating…' : 'Deactivate'}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function SupplierList({ query, status, offset, canManage, onEdit, onDeactivate, onPageChange, onRetry }: {
  query: string
  status: StatusFilter
  offset: number
  canManage: boolean
  onEdit: (supplier: Supplier) => void
  onDeactivate: (supplier: Supplier) => void
  onPageChange: (offset: number) => void
  onRetry: () => void
}) {
  const [data, setData] = useState<SupplierListData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let ignore = false
    listSuppliersRequest({
      q: query,
      is_active: status === 'all' ? undefined : status === 'active',
      limit: PAGE_SIZE,
      offset,
    })
      .then((res) => { if (!ignore) setData(res.data) })
      .catch((err: unknown) => { if (!ignore) setError(getErrorMessage(err, 'Could not load suppliers')) })
      .finally(() => { if (!ignore) setIsLoading(false) })
    return () => { ignore = true }
  }, [query, status, offset])

  const rows = data?.items ?? []
  return (
    <div className="flex flex-col gap-4">
      <Table aria-busy={isLoading}>
        <TableCaption>Suppliers</TableCaption>
        <TableHeader>
          <TableRow>
            {['Name', 'Contact', 'Phone', 'Email', 'Status', ...(canManage ? ['Actions'] : [])].map((column) => (
              <TableHead key={column} scope="col">{column}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading || error || rows.length === 0 ? (
            <TableRow>
              <TableCell colSpan={canManage ? 6 : 5} className="text-muted">
                <span role={error ? 'alert' : 'status'}>{isLoading ? 'Loading…' : error ?? (query ? 'No suppliers match your search' : 'No suppliers found')}</span>
                {error && <Button variant="ghost" onClick={onRetry}>Try again</Button>}
              </TableCell>
            </TableRow>
          ) : rows.map((supplier) => (
            <TableRow key={supplier.id}>
              <TableCell>{supplier.name}</TableCell>
              <TableCell className="text-muted">{supplier.contact_person ?? '—'}</TableCell>
              <TableCell className="text-muted">{supplier.phone ?? '—'}</TableCell>
              <TableCell className="text-muted">{supplier.email ?? '—'}</TableCell>
              <TableCell><StatusBadge status={supplier.is_active ? 'healthy' : 'low'}>{supplier.is_active ? 'Active' : 'Inactive'}</StatusBadge></TableCell>
              {canManage && (
                <TableCell>
                  <div className="flex gap-2">
                    <Button variant="ghost" className="px-2 py-1" aria-label={`Edit ${supplier.name}`} onClick={() => onEdit(supplier)}>Edit</Button>
                    {supplier.is_active && <Button variant="ghost" className="px-2 py-1" aria-label={`Deactivate ${supplier.name}`} onClick={() => onDeactivate(supplier)}>Deactivate</Button>}
                  </div>
                </TableCell>
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {!isLoading && !error && data && (
        <div className="flex flex-wrap items-center justify-between gap-3 text-body text-muted">
          <span>{data.total === 0 ? '0 suppliers' : `${offset + 1}–${Math.min(offset + rows.length, data.total)} of ${data.total} suppliers`}</span>
          <div className="flex gap-2">
            <Button variant="secondary" disabled={offset === 0} onClick={() => onPageChange(Math.max(0, offset - PAGE_SIZE))}>Previous</Button>
            <Button variant="secondary" disabled={offset + PAGE_SIZE >= data.total} onClick={() => onPageChange(offset + PAGE_SIZE)}>Next</Button>
          </div>
        </div>
      )}
    </div>
  )
}

export function SuppliersPage() {
  const { user } = useAuth()
  const canManage = user != null && user.role !== 'staff'
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<StatusFilter>('active')
  const [offset, setOffset] = useState(0)
  const [revision, setRevision] = useState(0)
  const [editing, setEditing] = useState<Supplier | 'new' | null>(null)
  const [deactivating, setDeactivating] = useState<Supplier | null>(null)

  useEffect(() => {
    const timeout = setTimeout(() => { setSearch(query.trim()); setOffset(0) }, 300)
    return () => clearTimeout(timeout)
  }, [query])

  function refresh() {
    setEditing(null)
    setDeactivating(null)
    setOffset(0)
    setRevision((value) => value + 1)
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="m-0 text-display font-bold text-fg">Suppliers</h1>
        {canManage && <Button onClick={() => setEditing('new')}><Plus className="size-4" aria-hidden="true" />Add supplier</Button>}
      </div>
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search aria-hidden="true" className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted" />
          <Input type="search" aria-label="Search suppliers" placeholder="Search suppliers…" value={query} onChange={(event) => setQuery(event.target.value)} className="pl-10" />
        </div>
        <Select value={status} onValueChange={(value) => {
          if (value === 'active' || value === 'inactive' || value === 'all') { setStatus(value); setOffset(0) }
        }}>
          <SelectTrigger aria-label="Supplier status" className="w-auto min-w-40"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="active">Active suppliers</SelectItem>
            <SelectItem value="inactive">Inactive suppliers</SelectItem>
            <SelectItem value="all">All suppliers</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <SupplierList
        key={JSON.stringify([search, status, offset, revision])}
        query={search} status={status} offset={offset} canManage={canManage}
        onEdit={setEditing} onDeactivate={setDeactivating} onPageChange={setOffset}
        onRetry={() => setRevision((value) => value + 1)}
      />
      {canManage && editing !== null && <SupplierFormDialog supplier={editing === 'new' ? null : editing} onClose={() => setEditing(null)} onSaved={refresh} />}
      {canManage && deactivating && <DeactivateDialog supplier={deactivating} onClose={() => setDeactivating(null)} onSaved={refresh} />}
    </div>
  )
}
