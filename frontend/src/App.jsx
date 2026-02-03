import { useState, useEffect } from 'react'
import Login from './components/Login'
import Setup from './components/Setup'
import Dashboard from './components/Dashboard'
import './App.css'

const API_BASE = 'http://127.0.0.1:5001'

function App() {
  const [view, setView] = useState('loading')
  const [sender, setSender] = useState(null)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/sender`, { credentials: 'include' })
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

  const getCsrfToken = async (url) => {
    const page = await fetch(`${API_BASE}${url}`, { credentials: 'include' })
    const html = await page.text()
    const match = html.match(/name="csrf_token" value="([^"]+)"/)
    return match ? match[1] : ''
  }

  const handleLogin = async (password) => {
    const token = await getCsrfToken('/login')

    const formData = new FormData()
    formData.append('password', password)
    formData.append('csrf_token', token)

    const res = await fetch(`${API_BASE}/login`, {
      method: 'POST',
      body: formData,
      credentials: 'include',
      redirect: 'manual'
    })

    if (res.type === 'opaqueredirect' || res.status === 302 || res.ok) {
      checkAuth()
      return { success: true }
    }
    return { success: false, error: 'Invalid password' }
  }

  const handleSetup = async (name, phone) => {
    const token = await getCsrfToken('/setup')

    const formData = new FormData()
    formData.append('name', name)
    formData.append('phone', phone)
    formData.append('csrf_token', token)

    const res = await fetch(`${API_BASE}/setup`, {
      method: 'POST',
      body: formData,
      credentials: 'include',
      redirect: 'manual'
    })

    if (res.type === 'opaqueredirect' || res.status === 302 || res.ok) {
      checkAuth()
      return { success: true }
    }
    return { success: false, error: 'Setup failed' }
  }

  const handleLogout = async () => {
    await fetch(`${API_BASE}/logout`, { credentials: 'include' })
    setSender(null)
    setView('login')
  }

  if (view === 'loading') {
    return <div className="loading">Loading...</div>
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
      apiBase={API_BASE}
    />
  )
}

export default App
