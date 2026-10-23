import { useState } from 'react'
import type { ComponentProps, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Button,
  Checkbox,
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
  Input,
} from '@/components/ui'
import { useAuth } from '@/app/useAuth'
import { getErrorMessage } from '@/lib/api/client'
import { cn } from '@/lib/cn'

export function LoginForm({ className, ...props }: ComponentProps<'form'>) {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [keepSignedIn, setKeepSignedIn] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email, password, keepSignedIn)
      navigate('/')
    } catch (err) {
      setError(getErrorMessage(err, 'Invalid credentials'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className={cn('flex flex-col gap-6', className)} onSubmit={handleSubmit} {...props}>
      <FieldGroup>
        <div className="flex flex-col gap-1.5">
          <h1 className="m-0 text-display font-bold text-fg">Welcome back</h1>
          <FieldDescription className="text-body leading-normal">
            Sign in to your pharmacy workspace. Your AI copilot has already prepared
            today&rsquo;s priorities.
          </FieldDescription>
        </div>

        <Field data-invalid={error ? true : undefined}>
          <FieldLabel htmlFor="email">Email</FieldLabel>
          <Input
            id="email"
            name="email"
            type="email"
            placeholder="you@pharmacy.com"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </Field>

        <Field>
          <div className="flex items-center">
            <FieldLabel htmlFor="password">Password</FieldLabel>
            <button
              type="button"
              className="ml-auto cursor-pointer border-0 bg-transparent p-0 text-caption text-accent hover:underline"
            >
              Forgot your password?
            </button>
          </div>
          <Input
            id="password"
            name="password"
            type="password"
            placeholder="••••••••••"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </Field>

        <Field orientation="horizontal">
          <Checkbox
            id="keep-signed-in"
            checked={keepSignedIn}
            onCheckedChange={(checked) => setKeepSignedIn(checked === true)}
          />
          <FieldLabel htmlFor="keep-signed-in" className="text-body text-muted">
            Keep me signed in
          </FieldLabel>
        </Field>

        {error ? <FieldError>{error}</FieldError> : null}

        <Field>
          <Button type="submit" variant="primary" className="w-full" disabled={submitting}>
            {submitting ? 'Signing in…' : 'Sign in'}
          </Button>
        </Field>

        <div className="flex items-start gap-2.5 rounded-[10px] border border-subtle bg-surface px-4 py-3.5">
          <span
            className="mt-1 size-2 shrink-0 rounded-full bg-healthy shadow-[0_0_6px_var(--status-healthy)]"
            aria-hidden="true"
          />
          <FieldDescription>
            HIPAA-aligned encryption. Your patient and inventory data never leaves your control.
          </FieldDescription>
        </div>
      </FieldGroup>
    </form>
  )
}
