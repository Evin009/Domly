import { useState } from 'react'
import { api, setToken } from '../api/client'

export default function Login({ onSuccess }) {
  const [form, setForm] = useState({ sr_email: '', sr_password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { token, is_enrolled } = await api.login(form.sr_email, form.sr_password)
      setToken(token)
      onSuccess({ is_enrolled })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="logo">Domly</div>
      <p className="subtitle">Sign in with your SmartRent account</p>

      <form onSubmit={handleSubmit} className="auth-form">
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
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
      </form>
    </div>
  )
}
