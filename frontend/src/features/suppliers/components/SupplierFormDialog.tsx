import { useState } from 'react'
import type { FormEvent } from 'react'
import {
  Alert, Button, Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle, Field, FieldLabel, Input,
} from '@/components/ui'
import { getErrorMessage } from '@/lib/api/client'
import { createSupplierRequest, updateSupplierRequest } from '@/lib/api/suppliers'
import type { Supplier } from '@/lib/api/types'

type Props = {
  supplier: Supplier | null
  onClose: () => void
  onSaved: () => void
}

export function SupplierFormDialog({ supplier, onClose, onSaved }: Props) {
  const [form, setForm] = useState({
    name: supplier?.name ?? '',
    contact_person: supplier?.contact_person ?? '',
    phone: supplier?.phone ?? '',
    email: supplier?.email ?? '',
    address: supplier?.address ?? '',
  })
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (isSaving) return
    if (!form.name.trim()) {
      setError('Supplier name is required.')
      return
    }
    setError(null)
    setIsSaving(true)
    const body = {
      name: form.name.trim(),
      contact_person: form.contact_person.trim() || null,
      phone: form.phone.trim() || null,
      email: form.email.trim() || null,
      address: form.address.trim() || null,
    }
    try {
      if (supplier) await updateSupplierRequest(supplier.id, body)
      else await createSupplierRequest(body)
      onSaved()
    } catch (err) {
      setError(getErrorMessage(err, 'Could not save supplier'))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={(open) => { if (!open && !isSaving) onClose() }}>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{supplier ? 'Edit supplier' : 'Add supplier'}</DialogTitle>
          <DialogDescription>Keep supplier contact details up to date.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <fieldset disabled={isSaving} className="flex flex-col gap-4">
            {([
              { name: 'name', label: 'Name', maxLength: 200, required: true },
              { name: 'contact_person', label: 'Contact person', maxLength: 200 },
              { name: 'phone', label: 'Phone', maxLength: 50, type: 'tel' },
              { name: 'email', label: 'Email', type: 'email' },
              { name: 'address', label: 'Address', maxLength: 500 },
            ] as const).map(({ name, label, ...inputProps }) => (
              <Field key={name}>
                <FieldLabel htmlFor={`supplier-${name}`}>{label}</FieldLabel>
                <Input
                  {...inputProps}
                  id={`supplier-${name}`}
                  name={name}
                  value={form[name]}
                  onChange={(event) => setForm((previous) => ({ ...previous, [name]: event.target.value }))}
                />
              </Field>
            ))}
          </fieldset>
          {error && <Alert variant="destructive" className="mt-4">{error}</Alert>}
          <DialogFooter>
            <Button variant="secondary" disabled={isSaving} onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={isSaving}>{isSaving ? 'Saving…' : 'Save supplier'}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
