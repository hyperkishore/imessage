import { useState } from 'react'
import './Setup.css'

function Setup({ onSetup, initialData }) {
  const [name, setName] = useState(initialData?.name || '')
  const [phone, setPhone] = useState(initialData?.phone || '')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (name.length < 2) {
      setError('Name must be at least 2 characters')
      return
    }

    if (!/^[\+]?[\d\s\-\(\)\.]{10,}$/.test(phone)) {
      setError('Please enter a valid phone number')
      return
    }

    setLoading(true)
    const result = await onSetup(name, phone)

    if (!result.success) {
      setError(result.error || 'Setup failed')
      setLoading(false)
    }
  }

  return (
    <div className="setup-container">
      <div className="setup-card">
        <div className="setup-icon">📱</div>
        <h1>Sender Setup</h1>
        <p className="setup-subtitle">Configure your iMessage sender profile</p>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">Your Name</label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="John Smith"
              required
            />
            <span className="hint">How recipients will see your name</span>
          </div>

          <div className="form-group">
            <label htmlFor="phone">Phone Number</label>
            <input
              type="tel"
              id="phone"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+1 (555) 123-4567"
              required
            />
            <span className="hint">Your iMessage phone number on this Mac</span>
          </div>

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Saving...' : 'Continue'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default Setup
