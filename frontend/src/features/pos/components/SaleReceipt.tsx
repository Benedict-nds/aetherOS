import { createPortal } from 'react-dom'
import { Printer } from 'lucide-react'
import { Button, Card } from '@/components/ui'
import type { Sale } from '@/lib/api/types'

const PAYMENT_LABELS = { cash: 'Cash', momo: 'MoMo', card: 'Card' } as const

function formatMoney(value: number | string) {
  return `GH₵ ${Number(value).toFixed(2)}`
}

function ReceiptDetails({ sale }: { sale: Sale }) {
  const date = new Date(sale.created_at)
  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col gap-1">
        <h1 className="m-0 text-h1 font-semibold text-fg">Sale receipt #{sale.id}</h1>
        <p className="m-0 text-body text-muted">AetherQore</p>
        <time dateTime={sale.created_at} className="text-body text-muted">
          {Number.isNaN(date.getTime()) ? sale.created_at : date.toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })}
        </time>
        <p className="m-0 text-body text-fg">Cashier: {sale.cashier.full_name}</p>
      </header>
      <div className="overflow-x-auto">
        <table className="w-full min-w-140 border-collapse text-left text-body">
          <caption className="sr-only">Sale items</caption>
          <thead>
            <tr className="border-b border-subtle">
              {['Medicine', 'Batch', 'Qty', 'Unit price', 'Line total'].map((column) => (
                <th key={column} scope="col" className="px-3 py-3 font-medium text-muted">{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sale.lines.map((line) => (
              <tr key={line.id} className="border-b border-subtle">
                <td className="px-3 py-3">{line.medicine_name}</td>
                <td className="px-3 py-3">{line.batch_number}</td>
                <td className="px-3 py-3">{line.quantity.toLocaleString()}</td>
                <td className="whitespace-nowrap px-3 py-3">{formatMoney(line.unit_price)}</td>
                <td className="whitespace-nowrap px-3 py-3">{formatMoney(line.line_total)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <dl className="m-0 flex flex-col gap-2 self-end text-body">
        {[
          ['Total', formatMoney(sale.total)],
          ['Amount paid', formatMoney(sale.amount_paid)],
          ['Change due', formatMoney(sale.change_due)],
          ['Payment method', PAYMENT_LABELS[sale.payment_method]],
        ].map(([label, value]) => (
          <div key={label} className="flex justify-between gap-8">
            <dt className="text-muted">{label}</dt>
            <dd className="m-0 font-semibold text-fg">{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

export function SaleReceipt({ sale, onNewSale }: { sale: Sale; onNewSale: () => void }) {
  return (
    <>
      <Card className="mx-auto w-full max-w-4xl gap-6 p-6">
        <p role="status" className="m-0 text-body text-healthy">Sale completed</p>
        <ReceiptDetails sale={sale} />
        <div className="flex flex-wrap justify-end gap-3">
          <Button variant="secondary" onClick={() => window.print()}><Printer className="size-4" aria-hidden="true" />Print</Button>
          <Button onClick={onNewSale}>New sale</Button>
        </div>
      </Card>
      {createPortal(
        <article className="sale-receipt-print hidden" aria-hidden="true">
          <style>{`
            @media print {
              @page { margin: 12mm; }
              body > :not(.sale-receipt-print) { display: none !important; }
              body > .sale-receipt-print { display: block !important; color: black; background: white; }
              .sale-receipt-print * { color: inherit !important; background: transparent !important; }
              .sale-receipt-print table { min-width: 0; width: 100%; }
              .sale-receipt-print tr { break-inside: avoid; }
              .sale-receipt-print th, .sale-receipt-print td { border-bottom: 1px solid; }
              .sale-receipt-print header, .sale-receipt-print dl { break-inside: avoid; }
            }
          `}</style>
          <ReceiptDetails sale={sale} />
        </article>,
        document.body,
      )}
    </>
  )
}
