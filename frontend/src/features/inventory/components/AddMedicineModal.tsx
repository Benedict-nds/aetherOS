import { useState } from 'react'
import type { FormEvent } from 'react'
import {
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Field,
  FieldError,
  FieldGroup,
  FieldLabel,
  InputField,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui'
import { getErrorMessage } from '@/lib/api/client'
import { createMedicineRequest } from '@/lib/api/medicines'
import type { MedicineCategory } from '../../../lib/api/types'

const DOSAGE_FORM_OPTIONS = ['Tablet', 'Capsule', 'Syrup', 'Injection', 'Cream']
const DEFAULT_CATEGORY_NAME = 'Antibiotics'

type FormState = {
  name: string
  genericName: string
  categoryId: string
  dosageForm: string
  strength: string
  barcode: string
  reorderLevel: string
}

function buildEmptyForm(categories: MedicineCategory[]): FormState {
  const defaultCategory =
    categories.find((c) => c.name === DEFAULT_CATEGORY_NAME) ?? categories[0]

  return {
    name: '',
    genericName: '',
    categoryId: defaultCategory ? String(defaultCategory.id) : '',
    dosageForm: 'Tablet',
    strength: '',
    barcode: '',
    reorderLevel: '',
  }
}

type SelectFieldProps = {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  options: { label: string; value: string }[]
}

function SelectField({ id, label, value, onChange, options }: SelectFieldProps) {
  return (
    <Field>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger id={id}>
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
    </Field>
  )
}

type AddMedicineModalProps = {
  open: boolean
  onClose: () => void
  categories: MedicineCategory[]
  /** Called after a successful save so the parent can refetch the list. */
  onSaved?: () => void
}

export const AddMedicineModal = ({ open, onClose, categories, onSaved }: AddMedicineModalProps) => {
  const [form, setForm] = useState<FormState>(() => buildEmptyForm(categories))
  const [formError, setFormError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [wasOpen, setWasOpen] = useState(open)

  if (open !== wasOpen) {
    setWasOpen(open)
    if (open) {
      setForm(buildEmptyForm(categories))
      setFormError(null)
      setIsSubmitting(false)
    }
  }

  const setField = (key: keyof FormState) => (value: string) =>
    setForm((prev) => ({ ...prev, [key]: value }))

  const categoryOptions = categories.map((c) => ({ label: c.name, value: String(c.id) }))

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setFormError(null)

    const trimmedName = form.name.trim()
    if (!trimmedName) {
      setFormError('Medicine name is required.')
      return
    }

    let reorderLevel = 0
    if (form.reorderLevel.trim() !== '') {
      const parsed = Number(form.reorderLevel)
      if (!Number.isFinite(parsed)) {
        setFormError('Reorder level must be a number.')
        return
      }
      reorderLevel = parsed
    }

    if (!form.categoryId) {
      setFormError('Select a category.')
      return
    }

    setIsSubmitting(true)
    try {
      await createMedicineRequest({
        name: trimmedName,
        generic_name: form.genericName.trim() || undefined,
        category_id: Number(form.categoryId),
        dosage_form: form.dosageForm || undefined,
        strength: form.strength.trim() || undefined,
        barcode: form.barcode.trim() || undefined,
        reorder_level: reorderLevel,
      })
      onSaved?.()
      onClose()
    } catch (err) {
      setFormError(getErrorMessage(err, 'Could not save medicine'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next && !isSubmitting) onClose()
      }}
    >
      <DialogContent
        className="max-w-lg"
        onPointerDownOutside={(event) => {
          if (isSubmitting) event.preventDefault()
        }}
        onEscapeKeyDown={(event) => {
          if (isSubmitting) event.preventDefault()
        }}
      >
        <DialogHeader>
          <DialogTitle className="text-h1">Add Medicine</DialogTitle>
          <DialogDescription>Add a new medicine to your catalogue</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <FieldGroup>
            <InputField
              label="Medicine name"
              name="name"
              placeholder="e.g. Paracetamol 500mg"
              value={form.name}
              onChange={(e) => setField('name')(e.target.value)}
            />

            <InputField
              label="Generic name"
              name="genericName"
              placeholder="e.g. Acetaminophen"
              value={form.genericName}
              onChange={(e) => setField('genericName')(e.target.value)}
            />

            <div className="grid grid-cols-2 gap-4">
              <SelectField
                id="category"
                label="Category"
                value={form.categoryId}
                onChange={setField('categoryId')}
                options={categoryOptions}
              />
              <SelectField
                id="dosageForm"
                label="Dosage Form"
                value={form.dosageForm}
                onChange={setField('dosageForm')}
                options={DOSAGE_FORM_OPTIONS.map((o) => ({ label: o, value: o }))}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <InputField
                label="Strength"
                name="strength"
                placeholder="e.g. 500mg"
                value={form.strength}
                onChange={(e) => setField('strength')(e.target.value)}
              />
              <InputField
                label="Barcode"
                name="barcode"
                placeholder="8901234500xxx"
                value={form.barcode}
                onChange={(e) => setField('barcode')(e.target.value)}
              />
            </div>

            <InputField
              label="Reorder level"
              name="reorderLevel"
              placeholder="e.g. 50"
              value={form.reorderLevel}
              onChange={(e) => setField('reorderLevel')(e.target.value)}
            />

            <FieldError>{formError}</FieldError>
          </FieldGroup>

          <DialogFooter>
            <Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={isSubmitting}>
              {isSubmitting ? 'Saving…' : 'Save Medicine'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
