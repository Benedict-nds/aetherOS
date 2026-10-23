import type { ComponentProps } from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/cn'

const buttonVariants = cva(
  'inline-flex cursor-pointer items-center justify-center gap-2 rounded-[10px] px-5 py-3 text-body font-semibold outline-none focus-visible:outline-2 focus-visible:outline-accent disabled:cursor-not-allowed disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'border-0 bg-accent text-[var(--bg-base)]',
        secondary: 'border border-subtle bg-elevated text-fg',
        ghost: 'border-0 bg-transparent text-fg',
      },
    },
    defaultVariants: {
      variant: 'primary',
    },
  },
)

export function Button({
  className,
  variant = 'primary',
  asChild = false,
  type = 'button',
  ...props
}: ComponentProps<'button'> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  if (asChild) {
    return <Slot data-slot="button" className={cn(buttonVariants({ variant }), className)} {...props} />
  }

  return (
    <button
      data-slot="button"
      type={type}
      className={cn(buttonVariants({ variant }), className)}
      {...props}
    />
  )
}

export { buttonVariants }
