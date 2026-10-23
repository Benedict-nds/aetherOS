import { Card, CardTitle } from '@/components/ui'

const BARS = [
    {day:"Mon", className:"h-9 flex-1 opacity-35"},
    {day:"Tue", className:"h-12.5 w-[42px] shrink-0 opacity-45"},
    {day:"Wed", className:"h-7.5 w-[42px] shrink-0 opacity-35"},
    {day:"Thu", className:"h-15 w-[42px] shrink-0 opacity-50"},
    {day:"Fri", className:"h-[45px] w-[42px] shrink-0 opacity-40"},
    {day:"Sat", className:"h-[70px] w-[42px] shrink-0 opacity-55"},
    {day:"Sun", className:"h-[90px] w-[42px] shrink-0"},
] as const


export const RevenueCard = () =>{
    return (
        <Card className="min-w-0 flex-1 gap-3.5">
            <CardTitle className="text-h2 font-semibold text-fg">This week's revenue</CardTitle>
            <div className="flex items-center gap-2.5">
                <span className="text-display font-bold text-fg">$31,720</span>
                <span className="text-caption text-healthy">↑ 14% vs last week</span>
            </div>
            <div className="flex h-22.5 items-end gap-2.5" aria-hidden="true">
                {BARS.map((bar) => (
                <div key={bar.day} className={`rounded-md bg-accent ${bar.className}`} />
                ))}
            </div>
        </Card>
    )
}
