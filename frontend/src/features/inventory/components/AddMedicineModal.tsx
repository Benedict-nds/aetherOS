import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ChevronDown, X } from 'lucide-react'
import { Button, InputField } from '@/components/ui'
import { createMedicineRequest, getErrorMessage } from '../../../lib/api/client'
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
  label: string
  value: string
  onChange: (value: string) => void
  options: { label: string; value: string }[]
}

function SelectField({ label, value, onChange, options }: SelectFieldProps) {
  return (
    <div className="input-field">
      <label>{label}</label>
      <div className="relative w-full">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full appearance-none rounded-lg border border-subtle bg-elevated py-2.5 pl-3.5 pr-9 text-body text-fg outline-none focus:border-accent"
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <ChevronDown
          className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-muted"
          strokeWidth={1.75}
        />
      </div>
    </div>
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

  // reset the form each time the modal is (re)opened
  useEffect(() => {
    if (open) {
      setForm(buildEmptyForm(categories))
      setFormError(null)
      setIsSubmitting(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  // close on Escape (not while submitting, so an in-flight request can't be abandoned silently)
  useEffect(() => {
    if (!open) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isSubmitting) onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [open, isSubmitting, onClose])

  if (!open) return null

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
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={() => !isSubmitting && onClose()}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="add-medicine-title"
        className="w-full max-w-lg rounded-[14px] border border-subtle bg-surface p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 id="add-medicine-title" className="m-0 text-h1 font-semibold text-fg">
              Add Medicine
            </h2>
            <p className="m-0 mt-1 text-body text-muted">Add a new medicine to your catalogue</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            aria-label="Close"
            className="shrink-0 rounded-md p-1 text-muted outline-none hover:bg-elevated hover:text-fg disabled:opacity-50"
          >
            <X className="size-5" strokeWidth={1.75} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
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
              label="Category"
              value={form.categoryId}
              onChange={setField('categoryId')}
              options={categoryOptions}
            />
            <SelectField
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

          {formError ? (
            <p role="alert" className="m-0 text-caption text-critical">
              {formError}
            </p>
          ) : null}

          <div className="mt-2 flex items-center justify-end gap-3">
            <Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={isSubmitting}>
              {isSubmitting ? 'Saving…' : 'Save Medicine'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
