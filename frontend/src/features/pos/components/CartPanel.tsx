import { Trash2, Minus, Plus } from "lucide-react";
import { Alert, Button, Card, Input, InputField, Tabs, TabsList, TabsTrigger } from "@/components/ui";
import { useState } from "react";
import { getErrorMessage } from "@/lib/api/client";
import { createSaleRequest } from "@/lib/api/sales";
import type { SalePaymentMethod } from "@/lib/api/types";


export type CartLine = {
    id: string
    name: string
    unitPrice: number
    qty: number
}


type PaymentMethod = "Cash" | "MoMo" | "Card"


const PAYMENT_METHODS: PaymentMethod[] = ['Cash', 'MoMo', 'Card']

const PAYMENT_API_VALUES: Record<PaymentMethod, SalePaymentMethod> = {
    Cash: 'cash',
    MoMo: 'momo',
    Card: 'card',
}


type CartPanelProps = {
    lines:CartLine[]
    onIncrement: (id:string) => void
    onDecrement: (id:string) => void
    onRemove: (id:string) => void
    /** Called after the API accepts the sale so the page can empty the cart and refresh stock. */
    onSaleComplete: () => void
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
            <Input
                type="text"
                inputMode="decimal"
                name={name}
                aria-label={label}
                value={value}
                onChange={(e) => onChange(sanitizePct(e.target.value))}
                className="px-2 py-1.5 text-right"
            />
            <span className="text-caption text-muted">%</span>
        </div>
    )
}



export const CartPanel = ({lines, onIncrement, onDecrement, onRemove, onSaleComplete}:CartPanelProps) =>{
    const itemCount = lines.reduce((sum, line) => sum + line.qty, 0)
    const subtotal = lines.reduce((sum, line) => sum + lineTotal(line), 0)

    const [discountPct, setDiscountPct] = useState('0')
    const [taxPct, setTaxPct] = useState('5')
    const [payment,setPayment] = useState<PaymentMethod>('Cash')
    const [tendered,setTendered] = useState('')
    const [isCharging, setIsCharging] = useState(false)
    const [chargeError, setChargeError] = useState<string | null>(null)
    const [chargeSuccess, setChargeSuccess] = useState<string | null>(null)

    const discountRate = parsePct(discountPct)
    const taxRate = parsePct(taxPct)
    const discountAmount = subtotal * (discountRate / 100)
    const taxable = subtotal - discountAmount
    const tax = taxable * (taxRate / 100)
    const total = taxable + tax
    const tenderedValue = Number.parseFloat(tendered) || 0
    const change = Math.max(0, tenderedValue - total)


    // Discount, tax and tendered are display-only. The server prices the sale from FEFO batches,
    // so only the medicine ids, quantities and payment method are sent.
    const handleCharge = async () => {
        if (isCharging || lines.length === 0) return

        setChargeError(null)
        setChargeSuccess(null)
        setIsCharging(true)
        try {
            await createSaleRequest({
                payment_method: PAYMENT_API_VALUES[payment],
                lines: lines.map((line) => ({
                    medicine_id: Number(line.id),
                    quantity: line.qty,
                })),
            })
            setTendered('')
            setChargeSuccess('Sale completed.')
            onSaleComplete()
        } catch (err) {
            // covers 409 (e.g. not enough stock) as well: the API message is shown and the cart is kept
            setChargeError(getErrorMessage(err, 'Could not complete the sale'))
        } finally {
            setIsCharging(false)
        }
    }

    return(
        <Card className="w-full gap-4 p-6 lg:w-100 lg:shrink-0">
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
                      <Button
                        type="button"
                        variant="ghost"
                        aria-label={`Decrease ${line.name}`}
                        onClick={() => onDecrement(line.id)}
                        className="size-5.5 min-h-0 rounded-md bg-elevated p-0 hover:text-accent"
                      >
                        <Minus className="size-3" strokeWidth={2.5} />
                      </Button>
                      <span className="min-w-3 text-center text-caption text-fg">{line.qty}</span>
                      <Button
                        type="button"
                        variant="ghost"
                        aria-label={`Increase ${line.name}`}
                        onClick={() => onIncrement(line.id)}
                        className="size-5.5 min-h-0 rounded-md bg-elevated p-0 hover:text-accent"
                      >
                        <Plus className="size-3" strokeWidth={2.5} />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        aria-label={`Remove ${line.name}`}
                        onClick={() => onRemove(line.id)}
                        className="size-5.5 min-h-0 rounded-md bg-elevated p-0 hover:text-critical"
                    >
                        <Trash2 className="size-3" strokeWidth={2.5} />
                    </Button>
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
          <Tabs
            value={payment}
            onValueChange={(value) => {
              if (value === 'Cash' || value === 'MoMo' || value === 'Card') setPayment(value)
            }}
            className="gap-0"
          >
            <TabsList className="grid w-full grid-cols-3" aria-label="Payment method">
              {PAYMENT_METHODS.map((method) => (
                <TabsTrigger key={method} value={method}>
                  {method}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
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
          {chargeError ? <Alert variant="destructive">{chargeError}</Alert> : null}
          {chargeSuccess ? <Alert variant="success">{chargeSuccess}</Alert> : null}
          <Button
            type="button"
            variant="primary"
            className="w-full"
            disabled={lines.length === 0 || isCharging}
            onClick={handleCharge}
          >
            {isCharging ? 'Charging…' : `Charge ${formatMoney(total)}`}
          </Button>
        </Card>
      )
}