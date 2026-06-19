import { useState } from 'react'

export default function Login({ onSuccess, onSwitch }) {
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const result = await window.domly.invoke('auth:login', form)
      if (result.success) {
        onSuccess(result.token)
      } else {
        setError(result.error)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="logo">Domly</div>
      <p className="subtitle">Sign in to your account</p>

      <form onSubmit={handleSubmit} className="auth-form">
        <input
          type="email"
          placeholder="Email"
          value={form.email}
          onChange={set('email')}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={form.password}
          onChange={set('password')}
          required
        />

        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={loading}>
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
      </form>

      <p className="switch-link">
        Don't have an account?{' '}
        <button className="link-btn" onClick={onSwitch}>
          Register
        </button>
      </p>
    </div>
  )
}
