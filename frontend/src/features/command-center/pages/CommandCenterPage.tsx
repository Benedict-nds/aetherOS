import { useEffect, useState } from 'react'
import { Plus } from 'lucide-react'
import { StatCard, Button } from '@/components/ui'
import { getDashboardSummaryRequest, getErrorMessage } from '@/lib/api/client'
import type { DashboardSummary } from '@/lib/api/types'
import { AiRecommendationsCard } from '../components/AiRecommendationsCard'
import { RevenueCard } from '../components/RevenueCard'
import { RecentActivity } from '../components/RecentActivity'

// TODO: replace with the signed-in user from your auth context/provider
const CURRENT_USER = { firstName: 'Amara' }

function getGreeting() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}

function formatMoney(amount: number, currency: string) {
  return new Intl.NumberFormat('en-GH', { style: 'currency', currency }).format(amount)
}

export const CommandCenterPage = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    getDashboardSummaryRequest()
      .then((res) => setSummary(res.data))
      .catch((err) => setLoadError(getErrorMessage(err, 'Could not load dashboard summary')))
      .finally(() => setIsLoading(false))
  }, [])

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between gap-4">
        <h1 className="m-0 text-display font-bold text-fg">Command Center</h1>
        <div className="flex items-center gap-3">
          <div className="size-9 shrink-0 rounded-full bg-elevated" aria-hidden="true" />
          <Button variant="primary">
            <Plus className="size-4" strokeWidth={2.5} />
            New Sale
          </Button>
        </div>
      </div>

      <div>
        <h2 className="m-0 text-h2 font-semibold text-fg">
          {getGreeting()}, {CURRENT_USER.firstName}
        </h2>
        <p className="m-0 mt-1 text-body text-muted">
          Here&rsquo;s what needs your attention today.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {isLoading ? (
          <div className="col-span-2 rounded-[14px] bg-surface p-5 text-body text-muted lg:col-span-4">
            Loading dashboard stats…
          </div>
        ) : loadError ? (
          <div className="col-span-2 rounded-[14px] bg-surface p-5 text-body text-muted lg:col-span-4">
            {loadError}
          </div>
        ) : (
          <>
            <StatCard
              label="Expiring soon"
              value={summary?.expiring_soon_count ?? 0}
              hint="medicines within 30 days"
            />
            <StatCard
              label="Low stock"
              value={summary?.low_stock_count ?? 0}
              hint="below reorder point"
            />
            <StatCard
              label="Pending invoices"
              value={summary?.open_orders_count ?? 0}
              hint="from 2 suppliers"
            />
            <StatCard
              label="Today's sales"
              value={
                summary
                  ? formatMoney(summary.today_sales.amount, summary.today_sales.currency)
                  : formatMoney(0, 'GHS')
              }
            />
          </>
        )}
      </div>

      <div className="flex flex-col gap-4 lg:flex-row">
        <AiRecommendationsCard />
        <RevenueCard />
      </div>

      <RecentActivity />
    </div>
  )
}
