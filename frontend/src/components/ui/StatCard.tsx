type StatCardProps = {
  label: string
  value: string | number
  hint?: string
}

export const StatCard = ({ label, value, hint }: StatCardProps) => {
  return (
    <div className="flex w-full min-w-0 flex-col gap-2.5 rounded-[14px] bg-surface p-5">
      <div className="text-caption text-muted">{label}</div>
      <div className="text-display font-bold text-fg">{value}</div>
      {hint ? <div className="text-caption text-muted">{hint}</div> : null}
    </div>
  )
}
