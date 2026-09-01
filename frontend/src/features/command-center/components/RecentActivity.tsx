const ITEMS = [
    { message: 'AI Copilot flagged 3 medicines expiring within 30 days', time: '2m ago' },
    { message: 'Grace T. completed a sale · $48.20', time: '11m ago' },
    { message: 'Shipment #4821 received and imported to inventory', time: '38m ago' },
    { message: 'Cash drawer end-of-day reconciliation matched', time: 'yesterday' },
] as const



export const RecentActivity = () =>{
    return (
        <section className="flex w-full flex-col gap-3.5 rounded-[14px] bg-surface p-5">
        <h2 className="m-0 text-h2 font-semibold text-fg">Recent activity</h2>
        {ITEMS.map((item) => (
          <div key={item.time} className="flex items-center justify-between gap-4">
            <p className="m-0 text-body text-muted">{item.message}</p>
            <span className="shrink-0 text-caption text-muted">{item.time}</span>
          </div>
        ))}
      </section>
    )
}