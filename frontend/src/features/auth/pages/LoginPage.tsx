import { Navigate } from 'react-router-dom'
import { useAuth } from '@/app/useAuth'
import { LoginForm } from '../components/LoginForm'

const logoSrc = '/assets/logo.png'

export const LoginPage = () => {
  const { user, isReady } = useAuth()

  if (isReady && user) {
    return <Navigate to="/" replace />
  }

  return (
    <div className="grid min-h-svh bg-base login:grid-cols-2">
      <div className="flex flex-col gap-4 p-6 login:p-10">
        <div className="flex justify-center gap-2 login:justify-start">
          <div className="flex items-center gap-2">
            <img src={logoSrc} alt="" className="h-5.5 w-auto object-contain" />
            <span className="text-h2 font-semibold text-fg">AetherQore</span>
          </div>
        </div>
        <div className="flex flex-1 items-center justify-center">
          <div className="w-full max-w-90">
            <LoginForm />
          </div>
        </div>
        <div className="text-center text-caption text-muted login:text-left">
          © 2026 AetherQore, Inc. · Privacy · Terms
        </div>
      </div>

      <div className="relative hidden flex-col items-center justify-center border-l border-subtle bg-surface login:flex">
        <div className="mb-7">
          <img
            src={logoSrc}
            alt="AetherQore"
            className="h-23 w-auto object-contain drop-shadow-[0_4px_18px_rgba(140,160,190,0.25)]"
          />
        </div>
        <div className="text-h1 font-semibold tracking-tight text-fg">AetherQore</div>
        <div className="mt-1.5 text-body text-muted">Pharmacy Operating System</div>
      </div>
    </div>
  )
}
