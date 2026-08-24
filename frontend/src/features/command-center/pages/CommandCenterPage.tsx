import { Plus } from 'lucide-react'
import { StatCard, Button } from '@/components/ui'
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

export const CommandCenterPage = () => {
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
        <StatCard label="Expiring soon" value={7} hint="medicines within 30 days" />
        <StatCard label="Low stock" value={12} hint="below reorder point" />
        <StatCard label="Pending invoices" value={3} hint="from 2 suppliers" />
        <StatCard label="Yesterday's revenue" value="$5,240" hint="+14% vs prior day" />
      </div>

      <div className="flex flex-col gap-4 lg:flex-row">
        <AiRecommendationsCard />
        <RevenueCard />
      </div>

      <RecentActivity />
    </div>
  )
}
