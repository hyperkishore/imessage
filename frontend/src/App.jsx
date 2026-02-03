import { useState, useEffect } from 'react'
import Login from './components/Login'
import Setup from './components/Setup'
import Dashboard from './components/Dashboard'
import './App.css'

function App() {
  const [view, setView] = useState('loading')
  const [sender, setSender] = useState(null)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const res = await fetch('/api/sender', { credentials: 'include' })
      if (res.ok) {
        const data = await res.json()
        setSender(data)
        setView('dashboard')
      } else if (res.status === 401) {
        setView('login')
      } else {
        setView('setup')
      }
    } catch (e) {
      setView('login')
    }
  }

  const handleLogin = async (password) => {
    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ password })
      })

      const data = await res.json()

      if (data.success) {
        checkAuth()
        return { success: true }
      }
      return { success: false, error: data.error || 'Invalid password' }
    } catch (e) {
      return { success: false, error: 'Network error' }
    }
  }

  const handleSetup = async (name, phone) => {
    try {
      const res = await fetch('/api/setup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ name, phone })
      })

      const data = await res.json()

      if (data.success) {
        checkAuth()
        return { success: true }
      }
      return { success: false, error: data.error || 'Setup failed' }
    } catch (e) {
      return { success: false, error: 'Network error' }
    }
  }

  const handleLogout = async () => {
    await fetch('/logout', { credentials: 'include' })
    setSender(null)
    setView('login')
  }

  if (view === 'loading') {
    return (
      <div className="loading" role="status" aria-live="polite">
        <span>Loading…</span>
      </div>
    )
  }

  if (view === 'login') {
    return <Login onLogin={handleLogin} />
  }

  if (view === 'setup') {
    return <Setup onSetup={handleSetup} />
  }

  return (
    <Dashboard
      sender={sender}
      onLogout={handleLogout}
      onEditProfile={() => setView('setup')}
    />
  )
}

export default App
