import type { ReactNode } from 'react'

type StatusBadgeProps = {
  status: 'healthy' | 'low' | 'critical'
  children: ReactNode
}

const STATUS_STYLES: Record<StatusBadgeProps['status'], { dot: string; text: string }> = {
  healthy: { dot: 'bg-healthy', text: 'text-healthy' },
  low: { dot: 'bg-warning', text: 'text-warning' },
  critical: { dot: 'bg-critical', text: 'text-critical' },
}

export const StatusBadge = ({ status, children }: StatusBadgeProps) => {
  const styles = STATUS_STYLES[status]

  return (
    <span
      className={`inline-flex items-center justify-center gap-1.5 rounded-full bg-elevated px-2.5 py-1 text-caption font-medium ${styles.text}`}
    >
      <span className={`size-2 shrink-0 rounded-full ${styles.dot}`} aria-hidden="true" />
      {children}
    </span>
  )
}
