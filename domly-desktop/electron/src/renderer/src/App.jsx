import { useState } from 'react'
import Login from './views/Login'
import Register from './views/Register'

export default function App() {
  const [view, setView] = useState('login') // 'login' | 'register' | 'home'
  const [token, setToken] = useState(null)

  if (view === 'register') {
    return (
      <Register
        onSuccess={() => setView('login')}
        onSwitch={() => setView('login')}
      />
    )
  }

  if (view === 'home') {
    return (
      <div className="home">
        <div className="home-icon">🏠</div>
        <h2>Domly is ready</h2>
        <p>Say <span className="wake-word">"Hey Domly"</span> to start</p>
      </div>
    )
  }

  return (
    <Login
      onSuccess={(t) => { setToken(t); setView('home') }}
      onSwitch={() => setView('register')}
    />
  )
}
