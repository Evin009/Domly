import { useState } from 'react'

export default function Register({ onSuccess, onSwitch }) {
  const [form, setForm] = useState({
    email: '',
    password: '',
    sr_email: '',
    sr_password: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const result = await window.domly.invoke('auth:signup', form)
      if (result.success) {
        onSuccess()
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
      <p className="subtitle">Create your account</p>

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

        <div className="section-label">SmartRent Account</div>

        <input
          type="email"
          placeholder="SmartRent Email"
          value={form.sr_email}
          onChange={set('sr_email')}
          required
        />
        <input
          type="password"
          placeholder="SmartRent Password"
          value={form.sr_password}
          onChange={set('sr_password')}
          required
        />

        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={loading}>
          {loading ? 'Creating account...' : 'Create Account'}
        </button>
      </form>

      <p className="switch-link">
        Already have an account?{' '}
        <button className="link-btn" onClick={onSwitch}>
          Sign In
        </button>
      </p>
    </div>
  )
}
