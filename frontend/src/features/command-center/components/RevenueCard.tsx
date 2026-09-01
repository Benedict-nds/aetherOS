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
        <section className="flex min-w-0 flex-1 flex-col gap-3.5 rounded-[14px] bg-surface p-5">
            <h2 className="m-0 text-h2 font-semibold text-fg">This week's revenue</h2>
            <div className="flex items-center gap-2.5">
                <span className="text-display font-bold text-fg">$31,720</span>
                <span className="text-caption text-healthy">↑ 14% vs last week</span>
            </div>
            <div className="flex h-22.5 items-end gap-2.5" aria-hidden="true">
                {BARS.map((bar) => (
                <div key={bar.day} className={`rounded-md bg-accent ${bar.className}`} />
                ))}
            </div>
    </section>
    )
}