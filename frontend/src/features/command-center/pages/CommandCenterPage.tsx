import { StatCard } from '@/components/ui'
import { AiRecommendationsCard } from '../components/AiRecommendationsCard'
import { RevenueCard } from '../components/RevenueCard'

export const CommandCenterPage = () => {
  return (
    <div className="flex flex-wrap gap-4">
      <StatCard label="Today's Sales" value="₵0.00" hint="No sales recorded yet" />
      <StatCard label="Low Stock Items" value={0} hint="Items below reorder point" />
      <StatCard label="Expiring Soon" value={0} hint="Medicines within 30 days" />
      <StatCard label="Open Orders" value={0} hint="Purchase orders in progress" />
      <AiRecommendationsCard />
      <RevenueCard />
    </div>
  )
}
