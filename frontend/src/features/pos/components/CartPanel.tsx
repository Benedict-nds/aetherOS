import { Trash2, Minus, Plus } from "lucide-react";
import { Button, InputField } from "@/components/ui";
import { useState } from "react";


export type CartLine = {
    id: string
    name: string
    unitPrice: number
    qty: number
}


type PaymentMethod = "Cash" | "MoMo" | "Card"


const PAYMENT_METHODS: PaymentMethod[] = ['Cash', 'MoMo', 'Card']


type CartPanelProps = {
    lines:CartLine[]
    onIncrement: (id:string) => void
    onDecrement: (id:string) => void
    onRemove: (id:string) => void
}

function formatMoney(value:number){
    return `GH₵ ${value.toFixed(2)}`
}

function parsePct(raw: string) {
    const n = Number.parseFloat(raw)
    if (!Number.isFinite(n) || n < 0) return 0
    return Math.min(n, 100)
}

function sanitizeDecimal(raw: string) {
    const cleaned = raw.replace(/[^\d.]/g, '')
    const [whole = '', ...rest] = cleaned.split('.')
    const frac = rest.join('').slice(0, 2)
    const normalizedWhole = whole.replace(/^0+(?=\d)/, '')
    const next = rest.length > 0 ? `${normalizedWhole}.${frac}` : normalizedWhole
    if (next === '' || next === '.') return next
    const n = Number.parseFloat(next)
    if (!Number.isFinite(n) || n < 0) return ''
    return next
}

function sanitizePct(raw: string) {
    const next = sanitizeDecimal(raw)
    if (next === '' || next === '.') return next
    if (Number.parseFloat(next) >= 100) return '100'
    return next
}

function lineTotal(line:CartLine){
    return  line.qty * line.unitPrice
}

type PctInputProps = {
    name: string
    label: string
    value: string
    onChange: (value: string) => void
}

function PctInput({ name, label, value, onChange }: PctInputProps) {
    return (
        <div className="flex w-24 items-center gap-1">
            <input
                type="number"
                inputMode="decimal"
                name={name}
                aria-label={label}
                value={value}
                onChange={(e) => onChange(sanitizePct(e.target.value))}
                className="w-full rounded-lg border border-subtle bg-elevated px-2 py-1.5 text-right text-body text-fg outline-none focus:border-accent"
            />
            <span className="text-caption text-muted">%</span>
        </div>
    )
}



export const CartPanel = ({lines, onIncrement, onDecrement, onRemove}:CartPanelProps) =>{
    const itemCount = lines.reduce((sum, line) => sum + line.qty, 0)
    const subtotal = lines.reduce((sum, line) => sum + lineTotal(line), 0)

    const [discountPct, setDiscountPct] = useState('0')
    const [taxPct, setTaxPct] = useState('5')
    const [payment,setPayment] = useState<PaymentMethod>('Cash')
    const [tendered,setTendered] = useState('')

    const discountRate = parsePct(discountPct)
    const taxRate = parsePct(taxPct)
    const discountAmount = subtotal * (discountRate / 100)
    const taxable = subtotal - discountAmount
    const tax = taxable * (taxRate / 100)
    const total = taxable + tax
    const tenderedValue = Number.parseFloat(tendered) || 0
    const change = Math.max(0, tenderedValue - total)


    const handleCharge = () => {
        console.log("POS sale (static, no API):",{
            lines,
            discountPct: discountRate,
            taxPct: taxRate,
            payment,
            subtotal,
            discountAmount,
            tax,
            total,
            tendered: tenderedValue,
            change
        })
    }

    return(
        <aside className="flex w-full flex-col gap-4 rounded-[14px] bg-surface p-6 lg:w-100 lg:shrink-0">
          <div className="flex items-center justify-between">
            <p className="m-0 text-caption text-muted">Walk-in customer (optional)</p>
            <p className="m-0 text-caption text-muted">
              {itemCount} {itemCount === 1 ? 'item' : 'items'}
            </p>
          </div>
          <div className="flex flex-col gap-4">
            {lines.length === 0 ? (
              <p className="m-0 text-body text-muted">Cart is empty. Add a medicine.</p>
            ) : (
              lines.map((line) => (
                <div key={line.id} className="flex flex-col gap-1">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-body text-fg">{line.name}</span>
                    <span className="text-body text-fg">{formatMoney(lineTotal(line))}</span>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-caption text-muted">{formatMoney(line.unitPrice)} each</span>
                    <div className="flex items-center gap-2.5">
                      <button
                        type="button"
                        aria-label={`Decrease ${line.name}`}
                        onClick={() => onDecrement(line.id)}
                        className="flex size-5.5 items-center justify-center rounded-md bg-elevated text-fg outline-none hover:text-accent"
                      >
                        <Minus className="size-3" strokeWidth={2.5} />
                      </button>
                      <span className="min-w-3 text-center text-caption text-fg">{line.qty}</span>
                      <button
                        type="button"
                        aria-label={`Increase ${line.name}`}
                        onClick={() => onIncrement(line.id)}
                        className="flex size-5.5 items-center justify-center rounded-md bg-elevated text-fg outline-none hover:text-accent"
                      >
                        <Plus className="size-3" strokeWidth={2.5} />
                      </button>
                      <button
                        type="button"
                        aria-label={`Remove ${line.name}`}
                        onClick={() => onRemove(line.id)}
                        className="flex size-5.5 items-center justify-center rounded-md bg-elevated text-fg outline-none hover:text-critical"
                    >
                        <Trash2 className="size-3" strokeWidth={2.5} />
                    </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
          <div className="flex flex-col gap-2.5 border-y border-subtle py-4">
            <div className="flex items-center justify-between">
              <span className="text-body text-muted">Subtotal</span>
              <span className="text-body text-fg">{formatMoney(subtotal)}</span>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-body text-muted">Discount</span>
              <PctInput
                name="discountPct"
                label="Discount percent"
                value={discountPct}
                onChange={setDiscountPct}
              />
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-body text-muted">Tax</span>
              <div className="flex items-center gap-3">
                <PctInput
                  name="taxPct"
                  label="Tax percent"
                  value={taxPct}
                  onChange={setTaxPct}
                />
                <span className="min-w-16 text-right text-body text-fg">{formatMoney(tax)}</span>
              </div>
            </div>
            <div className="flex items-center justify-between pt-1.5">
              <span className="text-h2 font-semibold text-fg">Total</span>
              <span className="text-h2 font-semibold text-accent">{formatMoney(total)}</span>
            </div>
          </div>
          <div className="grid grid-cols-3">
            {PAYMENT_METHODS.map((method) => {
              const selected = payment === method
              return (
                <button
                  key={method}
                  type="button"
                  onClick={() => setPayment(method)}
                  className={`py-3 text-body outline-none ${
                    selected
                      ? 'border border-accent text-fg'
                      : 'border border-subtle text-muted'
                  }`}
                >
                  {method}
                </button>
              )
            })}
          </div>
          <div className="flex items-end gap-3">
            <InputField
              label="Amount tendered"
              name="tendered"
              placeholder="Tendered: 0.00"
              value={tendered}
              onChange={(e) => setTendered(sanitizeDecimal(e.target.value))}
            />
            <div className="shrink-0 pb-0.5 text-right">
              <p className="m-0 text-caption text-muted">Change</p>
              <p className="m-0 text-body text-fg">{formatMoney(change)}</p>
            </div>
          </div>
          <Button
            type="button"
            variant="primary"
            className="w-full"
            disabled={lines.length === 0}
            onClick={handleCharge}
          >
            Charge {formatMoney(total)}
          </Button>
        </aside>
      )
}