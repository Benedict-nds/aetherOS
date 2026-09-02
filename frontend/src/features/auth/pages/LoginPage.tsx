import { useState } from 'react'
import type { FormEvent } from 'react'
import { Navigate, useNavigate, useNavigation } from 'react-router-dom'
import { Button, InputField } from '@/components/ui'

import { useAuth } from '@/app/auth'
import { getErrorMessage } from '@/lib/api/client'

const logoSrc = '/assets/logo.png'

export const LoginPage = () => {
  const navigate = useNavigate()
  const { user, isReady, login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [keepSignedIn, setKeepSignedIn] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)


  if (isReady && user) {
    return <Navigate to="/" replace />
  }

  const handleSubmit = async (e: FormEvent) => {
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
    <div className="flex min-h-screen bg-base max-login:flex-col">
      <div className="flex flex-1 flex-col items-center justify-center border-r border-subtle bg-surface max-login:hidden">
        <div className="mb-7">
          <img src={logoSrc} alt="AetherQore" className="h-23 w-auto object-contain drop-shadow-[0_4px_18px_rgba(140,160,190,0.25)]" />
        </div>
        <div className="text-h1 font-semibold tracking-tight text-fg">AetherQore</div>
        <div className="mt-1.5 text-body text-muted">Pharmacy Operating System</div>
      </div>

      <div className="flex flex-1 flex-col items-center justify-between bg-base px-12 pt-16 pb-8 max-login:px-6 max-login:pt-10 max-login:pb-6">
        <div className="my-auto w-full max-w-90">
          <div className="mb-16 flex items-center gap-2">
            <img src={logoSrc} alt="" className="h-5.5 w-auto object-contain" />
            <span className="text-h2 font-semibold text-fg">AetherQore</span>
          </div>

          <div>
            <h1 className="text-display mb-2.5 font-bold text-fg">Welcome back</h1>
            <p className="mb-7 text-body leading-normal text-muted">
              Sign in to your pharmacy workspace. Your AI copilot has already
              prepared today&rsquo;s priorities.
            </p>

            <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
              <InputField
                label="Email"
                name="email"
                type="email"
                placeholder="you@pharmacy.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />

              <InputField
                label="Password"
                name="password"
                type="password"
                placeholder="••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />

              <div className="-mt-0.5 flex items-center justify-between">
                <label className="flex cursor-pointer items-center gap-1.5">
                  <input
                    type="checkbox"
                    className='size-3.5 accent-accent'
                    checked={keepSignedIn}
                    onChange={(e) => setKeepSignedIn(e.target.checked)}
                  />
                  <span className='text-body text-muted'>Keep me signed in</span>
                </label>
                <button type="button" className="cursor-pointer border-0 bg-transparent p-0 text-body text-accent hover:underline">
                  Forgot password?
                </button>
              </div>

              {error ? (
                <p className="m-0 text-caption text-critical">{error}</p>
              ) : null}

              <Button type="submit" variant="primary" className="mt-1 w-full" disabled={submitting}>
                {submitting ? 'Signing in…' : 'Sign in'}
              </Button>
            </form>

            <div className="mt-6 flex items-start gap-2.5 rounded-[10px] border border-subtle bg-surface px-4 py-3.5 text-caption text-muted">
              <span className="mt-1 size-2 shrink-0 rounded-full bg-healthy shadow-[0_0_6px_var(--status-healthy)]" aria-hidden="true" />
              <span>
                HIPAA-aligned encryption. Your patient and inventory data
                never leaves your control.
              </span>
            </div>
          </div>
        </div>

        <div className="text-caption text-muted">
          © 2026 AetherQore, Inc. · Privacy · Terms
        </div>
      </div>
    </div>
  )
}
