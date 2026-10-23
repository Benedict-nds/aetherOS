import type { ComponentProps } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/cn'

const alertVariants = cva('rounded-[14px] border border-subtle bg-surface px-5 py-4 text-body', {
  variants: {
    variant: {
      default: 'text-muted',
      destructive: 'text-critical',
      success: 'text-healthy',
    },
  },
  defaultVariants: {
    variant: 'default',
  },
})

export function Alert({
  className,
  variant = 'default',
  ...props
}: ComponentProps<'div'> & VariantProps<typeof alertVariants>) {
  return (
    <div
      data-slot="alert"
      role={variant === 'success' ? 'status' : 'alert'}
      className={cn(alertVariants({ variant }), className)}
      {...props}
    />
  )
}
