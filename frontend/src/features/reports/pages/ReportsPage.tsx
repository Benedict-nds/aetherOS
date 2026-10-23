import { useState } from 'react'
import {
  Field,
  FieldLabel,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui'
import { LowStockTable } from '../components/LowStockTable'
import { ExpiryTable } from '../components/ExpiryTable'

type ReportTab = 'low-stock' | 'expiry'

export const ReportsPage = () => {
  const [tab, setTab] = useState<ReportTab>('low-stock')
  const [withinDays, setWithinDays] = useState('90')

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
              <Select value={withinDays} onValueChange={setWithinDays}>
                <SelectTrigger id="expiry-window" className="w-auto min-w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[30, 60, 90].map((days) => (
                    <SelectItem key={days} value={String(days)}>
                      {days} days
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
          ) : null}
        </div>
        <TabsContent value="low-stock">
          <LowStockTable />
        </TabsContent>
        <TabsContent value="expiry">
          <ExpiryTable key={withinDays} withinDays={Number(withinDays)} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
