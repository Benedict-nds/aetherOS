import type { ComponentProps, ReactNode } from 'react'
import { useMemo } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/cn'
import { Label } from './label'
import { Separator } from './separator'

export function FieldSet({ className, ...props }: ComponentProps<'fieldset'>) {
  return (
    <fieldset
      data-slot="field-set"
      className={cn('flex flex-col gap-6', className)}
      {...props}
    />
  )
}

export function FieldLegend({
  className,
  variant = 'legend',
  ...props
}: ComponentProps<'legend'> & { variant?: 'legend' | 'label' }) {
  return (
    <legend
      data-slot="field-legend"
      data-variant={variant}
      className={cn(
        'mb-3 font-medium text-fg',
        variant === 'legend' ? 'text-h2' : 'text-caption',
        className,
      )}
      {...props}
    />
  )
}

export function FieldGroup({ className, ...props }: ComponentProps<'div'>) {
  return (
    <div
      data-slot="field-group"
      className={cn('@container/field-group flex w-full flex-col gap-4', className)}
      {...props}
    />
  )
}

const fieldVariants = cva(
  'group/field flex w-full gap-1.5 data-[invalid=true]:text-critical',
  {
    variants: {
      orientation: {
        vertical: 'flex-col [&>*]:w-full [&>.sr-only]:w-auto',
        horizontal: 'flex-row items-center [&>[data-slot=field-label]]:flex-auto',
        responsive:
          'flex-col @md/field-group:flex-row @md/field-group:items-center [&>*]:w-full @md/field-group:[&>*]:w-auto',
      },
    },
    defaultVariants: {
      orientation: 'vertical',
    },
  },
)

export function Field({
  className,
  orientation = 'vertical',
  ...props
}: ComponentProps<'div'> & VariantProps<typeof fieldVariants>) {
  return (
    <div
      role="group"
      data-slot="field"
      data-orientation={orientation}
      className={cn(fieldVariants({ orientation }), className)}
      {...props}
    />
  )
}

export function FieldContent({ className, ...props }: ComponentProps<'div'>) {
  return (
    <div
      data-slot="field-content"
      className={cn('flex flex-1 flex-col gap-1.5', className)}
      {...props}
    />
  )
}

export function FieldLabel({ className, ...props }: ComponentProps<typeof Label>) {
  return <Label data-slot="field-label" className={cn('w-fit', className)} {...props} />
}

export function FieldTitle({ className, ...props }: ComponentProps<'div'>) {
  return (
    <div
      data-slot="field-title"
      className={cn('text-caption font-medium text-fg', className)}
      {...props}
    />
  )
}

export function FieldDescription({ className, ...props }: ComponentProps<'p'>) {
  return (
    <p
      data-slot="field-description"
      className={cn('m-0 text-caption text-muted', className)}
      {...props}
    />
  )
}

export function FieldSeparator({
  children,
  className,
  ...props
}: ComponentProps<'div'> & { children?: ReactNode }) {
  return (
    <div
      data-slot="field-separator"
      className={cn('relative my-1 h-5 text-caption text-muted', className)}
      {...props}
    >
      <Separator className="absolute inset-0 top-1/2" />
      {children ? (
        <span
          data-slot="field-separator-content"
          className="relative mx-auto block w-fit bg-base px-2"
        >
          {children}
        </span>
      ) : null}
    </div>
  )
}

export function FieldError({
  className,
  children,
  errors,
  ...props
}: ComponentProps<'div'> & {
  errors?: Array<{ message?: string } | undefined>
}) {
  const content = useMemo(() => {
    if (children) return children
    if (!errors?.length) return null
    const uniqueErrors = [...new Map(errors.map((error) => [error?.message, error])).values()]
    if (uniqueErrors.length === 1) return uniqueErrors[0]?.message
    return (
      <ul className="m-0 list-disc pl-4">
        {uniqueErrors.map(
          (error, index) =>
            error?.message ? <li key={index}>{error.message}</li> : null,
        )}
      </ul>
    )
  }, [children, errors])

  if (!content) return null

  return (
    <div
      role="alert"
      data-slot="field-error"
      className={cn('m-0 text-caption text-critical', className)}
      {...props}
    >
      {content}
    </div>
  )
}
