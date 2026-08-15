import type { ReactNode } from 'react'

type StatusBadgeProps = {
  status: 'healthy' | 'low' | 'critical'
  children: ReactNode
}

export const StatusBadge = ({ status, children }: StatusBadgeProps) => {
  return (
    <span className={`status-badge status-badge--${status}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {children}
    </span>
  )
}
