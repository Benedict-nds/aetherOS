import type { ComponentProps } from 'react'
import { cn } from '@/lib/cn'

export function Input({ className, type = 'text', ...props }: ComponentProps<'input'>) {
  return (
    <input
      data-slot="input"
      type={type}
      className={cn(
        'w-full rounded-lg border border-subtle bg-elevated px-3.5 py-3 text-body text-fg outline-none placeholder:text-muted focus:border-accent disabled:opacity-50',
        className,
      )}
      {...props}
    />
  )
}
