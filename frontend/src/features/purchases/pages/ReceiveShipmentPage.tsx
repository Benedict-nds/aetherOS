import { Download, Sparkles } from "lucide-react"
import { Button } from "@/components/ui"

const STEPS = [
  {n:"1", label:"Upload invoice", active:true},
  {n:"2", label:"AI extraction", active:false},
  {n:"3", label:"Review & approve", active:false},
  {n:"4", label:"Imported", active:false},
] as const

export function ReceiveShipmentPage() {
  return (
    <div className="flex flex-col gap-8">
      <h1 className="m-0 text-h1 font-semibold text-fg">Receive Shipment</h1>
      <div className="flex w-full items-center">
        {STEPS.map((step, index) => (
          <div
            key={step.n}
            className={index < STEPS.length - 1 ? 'flex min-w-0 flex-1 items-center' : 'flex items-center'}
          >
            <div className="flex items-center gap-2">
              <span
                className={
                  step.active
                    ? 'flex size-7 shrink-0 items-center justify-center rounded-full bg-accent text-body text-base'
                    : 'flex size-7 shrink-0 items-center justify-center rounded-full bg-elevated text-body text-muted'
                }
              >
                {step.n}
              </span>
              <span className={step.active ? 'text-body whitespace-nowrap text-fg' : 'text-body whitespace-nowrap text-muted'}>
                {step.label}
              </span>
            </div>
            {index < STEPS.length - 1 && <span className="mx-3 h-0.5 min-w-4 flex-1 bg-subtle" />}
          </div>
        ))}
      </div>
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start">
        <section className="flex min-w-0 flex-1 flex-col gap-4">
          <div className="flex h-55 flex-col items-center justify-center gap-3 rounded-[14px] border-[1.5px] border-subtle px-6 py-6 text-center">
            <Download className="size-9 text-muted" strokeWidth={1.75} aria-hidden="true" />
            <p className="m-0 text-h2 font-semibold text-fg">Drop invoice here</p>
            <p className="m-0 max-w-85 text-caption text-muted">
              PDF, JPG or PNG up to 20MB. AI reads printed and handwritten invoices.
            </p>
            <div className="flex items-center gap-2.5 pt-1">
              <Button variant="secondary" onClick={() => console.log('browse files')}>
                Browse files
              </Button>
              <Button variant="secondary" onClick={() => console.log('use camera')}>
                Use camera
              </Button>
            </div>
          </div>
          <p className="m-0 text-caption text-muted">Uploaded document</p>
          <div className="flex items-center gap-3 rounded-[10px] bg-surface p-3.5">
            <span className="size-9 shrink-0 rounded-lg bg-accent" aria-hidden="true" />
            <div className="min-w-0 flex-1">
              <p className="m-0 text-body text-fg">invoice-medisource-4821.pdf</p>
              <p className="m-0 text-caption text-muted">1.2 MB · MediSource Global</p>
            </div>
            <button
              type="button"
              className="shrink-0 cursor-pointer border-0 bg-transparent p-0 text-h1 font-semibold text-muted"
              aria-label="Remove uploaded document"
              onClick={() => console.log('remove file')}
            >
              ×
            </button>
          </div>
        </section>
        <section className="flex min-h-85 min-w-0 flex-1 flex-col items-center justify-center gap-3 rounded-[14px] bg-surface px-10 py-10 text-center">
          <Sparkles className="size-10 text-accent" strokeWidth={1.75} aria-hidden="true" />
          <p className="m-0 text-h2 font-semibold text-fg">Upload an invoice to begin</p>
          <p className="m-0 max-w-100 text-body text-muted">
            AetherQore will read the document, extract every line item, match it to your inventory, and
            prepare it for a one-click import.
          </p>
        </section>
      </div>
    </div>
  )
}
