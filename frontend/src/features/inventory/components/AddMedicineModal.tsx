import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ChevronDown, X } from 'lucide-react'
import { Button, InputField } from '@/components/ui'

/**
 * TODO: LOOK INTO WHICH FIELDS WHOULD BE REQUIRED FOR THE MEDICINE
 */



type AddMedicineForm = {
  name: string
  genericName: string
  category: string
  dosageForm: string
  strength: string
  barcode: string
  reorderLevel: string
}

const EMPTY_FORM: AddMedicineForm = {
  name: '',
  genericName: '',
  category: 'Antibiotics',
  dosageForm: 'Tablet',
  strength: '',
  barcode: '',
  reorderLevel: '',
}

const CATEGORY_OPTIONS = ['Antibiotics', 'Cardiovascular', 'Antidiabetic', 'Analgesics', 'Vitamins']
const DOSAGE_FORM_OPTIONS = ['Tablet', 'Capsule', 'Syrup', 'Injection', 'Cream']

type SelectFieldProps = {
  label: string
  value: string
  onChange: (value: string) => void
  options: string[]
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
    </div>
  )
}

type AddMedicineModalProps = {
  open: boolean
  onClose: () => void
  onSave?: (medicine: AddMedicineForm) => void
}

export const AddMedicineModal = ({ open, onClose, onSave }: AddMedicineModalProps) => {
  const [form, setForm] = useState<AddMedicineForm>(EMPTY_FORM)
  const [error, setError] = useState<string | null>(null)

  const handleClose = useCallback(() => {
    setForm(EMPTY_FORM)
    setError(null)
    onClose()
  }, [onClose])

  useEffect(() => {
    if (!open) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [open, handleClose])

  if (!open) return null

  const setField = (key: keyof AddMedicineForm) => (value: string) => {
    if (key === 'name' && error) setError(null)
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!form.name.trim()) {
      setError('Medicine name is required.')
      return
    }
    onSave?.(form)
    handleClose()
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={handleClose}
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
            onClick={handleClose}
            aria-label="Close"
            className="shrink-0 rounded-md p-1 text-muted outline-none hover:bg-elevated hover:text-fg"
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
          {error ? (
            <p className="-mt-2 m-0 text-caption text-critical" role="alert">
              {error}
            </p>
          ) : null}

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
              value={form.category}
              onChange={setField('category')}
              options={CATEGORY_OPTIONS}
            />
            <SelectField
              label="Dosage Form"
              value={form.dosageForm}
              onChange={setField('dosageForm')}
              options={DOSAGE_FORM_OPTIONS}
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

          <div className="mt-2 flex items-center justify-end gap-3">
            <Button type="button" variant="secondary" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Save Medicine
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
