import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { Field, FieldLabel, Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui'
import { LowStockTable } from '../components/LowStockTable'
import { ExpiryTable } from '../components/ExpiryTable'

type ReportTab = 'low-stock' | 'expiry'

export const ReportsPage = () => {
  const [tab, setTab] = useState<ReportTab>('low-stock')
  const [withinDays, setWithinDays] = useState(90)

  return (
    <div className="flex flex-col gap-6">
      <h1 className="m-0 text-display font-bold text-fg">Reports</h1>
      <Tabs
        value={tab}
        onValueChange={(value) => {
          if (value === 'low-stock' || value === 'expiry') setTab(value)
        }}
      >
        <div className="flex flex-wrap items-center justify-between gap-4">
          <TabsList aria-label="Report type">
            <TabsTrigger value="low-stock">Low stock</TabsTrigger>
            <TabsTrigger value="expiry">Expiry</TabsTrigger>
          </TabsList>
          {tab === 'expiry' ? (
            <Field orientation="horizontal" className="w-auto gap-3">
              <FieldLabel htmlFor="expiry-window" className="text-body">
                Expiry window
              </FieldLabel>
              <span className="relative">
                <select
                  id="expiry-window"
                  value={withinDays}
                  onChange={(event) => setWithinDays(Number(event.target.value))}
                  className="min-w-40 appearance-none rounded-lg border border-subtle bg-elevated py-2.5 pl-4 pr-9 text-body text-fg outline-none focus:border-accent"
                >
                  {[30, 60, 90].map((days) => (
                    <option key={days} value={days}>
                      {days} days
                    </option>
                  ))}
                </select>
                <ChevronDown
                  aria-hidden="true"
                  className="pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-muted"
                  strokeWidth={1.75}
                />
              </span>
            </Field>
          ) : null}
        </div>
        <TabsContent value="low-stock">
          <LowStockTable />
        </TabsContent>
        <TabsContent value="expiry">
          <ExpiryTable key={withinDays} withinDays={withinDays} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
