import { useState } from 'react'
import type { FormEvent } from 'react'
import { Button, InputField } from '../../../components/ui'
import '../../../styles/login.css'

const logoSrc = '/assets/logo.png'

export const LoginPage = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [keepSignedIn, setKeepSignedIn] = useState(false)

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    // wire up auth here
  }

  return (
    <div className="login">
      <div className="login__left">
        <div className="login__brandmark">
          <img src={logoSrc} alt="AetherQore" className="login__logo-large" />
        </div>
        <div className="login__brandname">AetherQore</div>
        <div className="login__brandsub">Pharmacy Operating System</div>
      </div>

      <div className="login__right">
        <div className="login__panel">
          <div className="login__panel-header">
            <img src={logoSrc} alt="" className="login__logo-small" />
            <span className="login__panel-brand">AetherQore</span>
          </div>

          <div className="login__panel-body">
            <h1 className="login__title">Welcome back</h1>
            <p className="login__subtitle">
              Sign in to your pharmacy workspace. Your AI copilot has already
              prepared today&rsquo;s priorities.
            </p>

            <form className="login__form" onSubmit={handleSubmit}>
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

              <div className="login__row">
                <label className="login__checkbox">
                  <input
                    type="checkbox"
                    checked={keepSignedIn}
                    onChange={(e) => setKeepSignedIn(e.target.checked)}
                  />
                  <span>Keep me signed in</span>
                </label>
                <a href="#" className="login__forgot">
                  Forgot password?
                </a>
              </div>

              <Button type="submit" variant="primary" className="login__submit">
                Sign in
              </Button>
            </form>

            <div className="login__security">
              <span className="login__security-dot" aria-hidden="true" />
              <span>
                HIPAA-aligned encryption. Your patient and inventory data
                never leaves your control.
              </span>
            </div>
          </div>
        </div>

        <div className="login__footer">
          © 2026 AetherQore, Inc. · <a href="#">Privacy</a> · <a href="#">Terms</a>
        </div>
      </div>
    </div>
  )
}