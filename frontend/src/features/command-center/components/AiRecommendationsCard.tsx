import { Link } from "react-router-dom";
import { Card, CardTitle } from "@/components/ui";

const RECS = [
    {
        dot: 'bg-warning',
        body: 'Metformin 850mg will run out in ~4 days. Reorder from Nova Health.',
        action: 'Reorder',
        to: '/reports',
      },
      {
        dot: 'bg-critical',
        body: 'Azithromycin batch AZM-6640 expires Dec 28. Consider a clearance markdown.',
        action: 'Review',
        to: '/reports',
      },
] as const


export const AiRecommendationsCard = () =>{
    return (
        <Card className="min-w-0 flex-1 gap-4">
            <CardTitle className="text-h2 font-semibold text-fg">Today's AI recommendations</CardTitle>
            {RECS.map((rec) => (
                <div key={rec.action} className="flex items-center justify-between gap-2.5">
                <div className="flex min-w-0 flex-1 items-start gap-2.5">
                    <span className={`mt-1.5 size-2 shrink-0 rounded-full ${rec.dot}`} />
                    <p className="m-0 text-body text-fg">{rec.body}</p>
                </div>
                <Link to={rec.to} className="shrink-0 text-caption text-accent">
                    {rec.action}
                </Link>
                </div>
            ))}
        </Card>
    )
}
