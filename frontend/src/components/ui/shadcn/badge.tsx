import type { ReactNode } from 'react'
import { cn } from '@/lib/cn'

type Status = 'healthy' | 'low' | 'critical'

type StatusBadgeProps = {
  status: Status
  children: ReactNode
  className?: string
}

const STATUS_STYLES: Record<Status, { dot: string; text: string }> = {
  healthy: { dot: 'bg-healthy', text: 'text-healthy' },
  low: { dot: 'bg-warning', text: 'text-warning' },
  critical: { dot: 'bg-critical', text: 'text-critical' },
}

export function StatusBadge({ status, children, className }: StatusBadgeProps) {
  const styles = STATUS_STYLES[status]

  return (
    <span
      data-slot="badge"
      className={cn(
        'inline-flex items-center justify-center gap-1.5 rounded-full bg-elevated px-2.5 py-1 text-caption font-medium',
        styles.text,
        className,
      )}
    >
      <span className={cn('size-2 shrink-0 rounded-full', styles.dot)} aria-hidden="true" />
      {children}
    </span>
  )
}
