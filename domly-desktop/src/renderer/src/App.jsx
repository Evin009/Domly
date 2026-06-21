import { useState } from 'react'
import Login from './views/Login'
import Enrollment from './views/Enrollment'
import Home from './views/Home'

export default function App() {
  const [view, setView] = useState('login')

  if (view === 'enrollment') {
    return <Enrollment onComplete={() => setView('home')} />
  }

  if (view === 'home') {
    return <Home onReEnroll={() => setView('enrollment')} />
  }

  return (
    <Login
      onSuccess={({ is_enrolled }) => setView(is_enrolled ? 'home' : 'enrollment')}
    />
  )
}
