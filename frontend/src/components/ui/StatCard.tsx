type StatCardProps = {
  label: string
  value: string | number
  hint?: string
  tone?: 'default' | 'critical' | 'warning' | 'healthy'
}

const VALUE_TONE_STYLES: Record<NonNullable<StatCardProps['tone']>, string> = {
  default: 'text-fg',
  critical: 'text-critical',
  warning: 'text-warning',
  healthy: 'text-healthy',
}

export const StatCard = ({ label, value, hint, tone = 'default' }: StatCardProps) => {
  return (
    <div className="flex w-full min-w-0 flex-col gap-2.5 rounded-[14px] bg-surface p-5">
      <div className="text-caption text-muted">{label}</div>
      <div className={`text-display font-bold ${VALUE_TONE_STYLES[tone]}`}>{value}</div>
      {hint ? <div className="text-caption text-muted">{hint}</div> : null}
    </div>
  )
}
