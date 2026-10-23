import { Card, CardTitle } from '@/components/ui'

const ITEMS = [
    { message: 'AI Copilot flagged 3 medicines expiring within 30 days', time: '2m ago' },
    { message: 'Grace T. completed a sale · $48.20', time: '11m ago' },
    { message: 'Shipment #4821 received and imported to inventory', time: '38m ago' },
    { message: 'Cash drawer end-of-day reconciliation matched', time: 'yesterday' },
] as const



export const RecentActivity = () =>{
    return (
        <Card className="w-full gap-3.5">
        <CardTitle className="text-h2 font-semibold text-fg">Recent activity</CardTitle>
        {ITEMS.map((item) => (
          <div key={item.time} className="flex items-center justify-between gap-4">
            <p className="m-0 text-body text-muted">{item.message}</p>
            <span className="shrink-0 text-caption text-muted">{item.time}</span>
          </div>
        ))}
      </Card>
    )
}
