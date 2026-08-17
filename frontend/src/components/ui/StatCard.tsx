type StatCardProps = {
  label: string
  value: string | number
  hint?: string
}

export const StatCard = ({ label, value, hint }: StatCardProps) => {
  return (
    <div className="stat-card">
      <div className="stat-card__label">{label}</div>
      <div className="stat-card__value">{value}</div>
      {hint ? <div className="stat-card__hint">{hint}</div> : null}
    </div>
  )
}
