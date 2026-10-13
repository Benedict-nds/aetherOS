import { Download, Sparkles } from "lucide-react"
import { Button } from "@/components/ui"

const STEP: 1 | 2 = 2

const STEPS = [
  { n: 1, label: "Upload invoice" },
  { n: 2, label: "AI extraction" },
  { n: 3, label: "Review & approve" },
  { n: 4, label: "Imported" },
] as const

const CHECKLIST = [
  { mark: "✓", label: "Detecting document structure", markClass: "text-healthy", labelClass: "text-muted" },
  { mark: "✓", label: "Reading line items", markClass: "text-healthy", labelClass: "text-muted" },
  { mark: "◐", label: "Matching products to inventory", markClass: "text-accent", labelClass: "text-fg" },
  { mark: "○", label: "Validating quantities and prices", markClass: "text-muted", labelClass: "text-muted" },
] as const

function stepState(n: number) {
  if (n < STEP) return "complete" as const
  if (n === STEP) return "active" as const
  return "inactive" as const
}

export function ReceiveShipmentPage() {
  return (
    <div className="flex flex-col gap-8">
      <h1 className="m-0 text-h1 font-semibold text-fg">Receive Shipment</h1>
      <div className="flex w-full items-center">
        {STEPS.map((step, index) => {
          const state = stepState(step.n)
          return (
            <div
              key={step.n}
              className={index < STEPS.length - 1 ? "flex min-w-0 flex-1 items-center" : "flex items-center"}
            >
              <div className="flex items-center gap-2">
                <span
                  className={
                    state === "inactive"
                      ? "flex size-7 shrink-0 items-center justify-center rounded-full bg-elevated text-body text-muted"
                      : "flex size-7 shrink-0 items-center justify-center rounded-full bg-accent text-body text-base"
                  }
                >
                  {state === "complete" ? "✓" : step.n}
                </span>
                <span
                  className={
                    state === "inactive"
                      ? "text-body whitespace-nowrap text-muted"
                      : "text-body whitespace-nowrap text-fg"
                  }
                >
                  {step.label}
                </span>
              </div>
              {index < STEPS.length - 1 && <span className="mx-3 h-0.5 min-w-4 flex-1 bg-subtle" />}
            </div>
          )
        })}
      </div>
      {STEP === 1 && (
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start">
          <section className="flex min-w-0 flex-1 flex-col gap-4">
            <div className="flex h-55 flex-col items-center justify-center gap-3 rounded-[14px] border-[1.5px] border-subtle px-6 py-6 text-center">
              <Download className="size-9 text-muted" strokeWidth={1.75} aria-hidden="true" />
              <p className="m-0 text-h2 font-semibold text-fg">Drop invoice here</p>
              <p className="m-0 max-w-85 text-caption text-muted">
                PDF, JPG or PNG up to 20MB. AI reads printed and handwritten invoices.
              </p>
              <div className="flex items-center gap-2.5 pt-1">
                <Button variant="secondary" onClick={() => console.log("browse files")}>
                  Browse files
                </Button>
                <Button variant="secondary" onClick={() => console.log("use camera")}>
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
                onClick={() => console.log("remove file")}
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
      )}
      {STEP === 2 && (
        <div className="flex justify-center">
          <section className="flex h-85 w-full max-w-140 flex-col items-center gap-5 rounded-[14px] bg-surface px-10 py-10 text-center">
            <Sparkles className="size-12 text-accent" strokeWidth={1.75} aria-hidden="true" />
            <p className="m-0 text-h2 font-semibold text-fg">Extracting invoice data...</p>
            <p className="m-0 text-caption text-muted">Reading invoice-medisource-4821.pdf</p>
            <ul className="m-0 flex w-full max-w-100 list-none flex-col gap-2.5 p-0 pt-2 text-left text-body">
              {CHECKLIST.map((item) => (
                <li key={item.label}>
                  <span className={item.markClass}>{item.mark}</span>
                  <span className={item.labelClass}> {item.label}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
    </div>
  )
}