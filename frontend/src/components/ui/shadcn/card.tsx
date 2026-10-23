import type { ComponentProps } from 'react'
import { cn } from '@/lib/cn'

export function Card({ className, ...props }: ComponentProps<'div'>) {
  return (
    <div
      data-slot="card"
      className={cn('flex flex-col gap-2.5 rounded-[14px] bg-surface p-5 text-fg', className)}
      {...props}
    />
  )
}

export function CardTitle({ className, ...props }: ComponentProps<'div'>) {
  return <div data-slot="card-title" className={cn('text-caption text-muted', className)} {...props} />
}

export function CardDescription({ className, ...props }: ComponentProps<'div'>) {
  return <div data-slot="card-description" className={cn('text-caption text-muted', className)} {...props} />
}

type StatCardProps = {
  label: string
  value: string | number
  hint?: string
  tone?: 'default' | 'critical' | 'warning' | 'healthy'
  className?: string
}

const VALUE_TONE_STYLES: Record<NonNullable<StatCardProps['tone']>, string> = {
  default: 'text-fg',
  critical: 'text-critical',
  warning: 'text-warning',
  healthy: 'text-healthy',
}

export function StatCard({ label, value, hint, tone = 'default', className }: StatCardProps) {
  return (
    <Card className={cn('w-full min-w-0', className)}>
      <CardTitle>{label}</CardTitle>
      <div className={cn('text-display font-bold', VALUE_TONE_STYLES[tone])}>{value}</div>
      {hint ? <CardDescription>{hint}</CardDescription> : null}
    </Card>
  )
}
