import { useState, useEffect } from 'react'
import './Dashboard.css'

function Dashboard({ sender, onLogout, onEditProfile }) {
  const [agents, setAgents] = useState([])
  const [selectedSender, setSelectedSender] = useState('local')
  const [sheetUrl, setSheetUrl] = useState('')
  const [template, setTemplate] = useState('')
  const [messages, setMessages] = useState([])
  const [status, setStatus] = useState({ type: '', text: '' })
  const [loading, setLoading] = useState(false)
  const [csrfToken, setCsrfToken] = useState('')
  const [confirmModal, setConfirmModal] = useState({ open: false, message: '', onConfirm: null })

  useEffect(() => {
    loadAgents()
    fetchCsrfToken()
  }, [])

  const fetchCsrfToken = async () => {
    try {
      const res = await fetch(`/`, { credentials: 'include' })
      const html = await res.text()
      const match = html.match(/csrfToken = '([^']+)'/)
      if (match) setCsrfToken(match[1])
    } catch (e) {
      console.log('Could not fetch CSRF token')
    }
  }

  const loadAgents = async () => {
    try {
      const res = await fetch(`/api/agents`, { credentials: 'include' })
      if (res.ok) {
        const data = await res.json()
        setAgents(data)
      }
    } catch (e) {
      console.log('Could not load agents')
    }
  }

  const showStatus = (text, type = 'success') => {
    setStatus({ text, type })
    setTimeout(() => setStatus({ type: '', text: '' }), 5000)
  }

  const handlePreview = async () => {
    if (!sheetUrl || !template) {
      showStatus('Please fill in both fields', 'error')
      return
    }

    setLoading(true)
    try {
      const res = await fetch(`/preview`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        credentials: 'include',
        body: JSON.stringify({ sheet_url: sheetUrl, template })
      })

      const data = await res.json()

      if (!res.ok) {
        showStatus(data.error || 'Failed to load preview', 'error')
        return
      }

      setMessages(data.previews.map(p => ({ ...p, status: null })))
      showStatus(`Loaded ${data.count} messages`)
    } catch (e) {
      showStatus('Network error: ' + e.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleSendOne = async (index) => {
    const msg = messages[index]
    const messageText = msg.message

    try {
      let res, data

      if (selectedSender === 'local') {
        res = await fetch(`/send-one`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
          },
          credentials: 'include',
          body: JSON.stringify({ phone: msg.phone, message: messageText })
        })
        data = await res.json()

        const newMessages = [...messages]
        newMessages[index] = {
          ...msg,
          status: data.success ? 'sent' : 'failed',
          error: data.error
        }
        setMessages(newMessages)
        showStatus(
          data.success ? `Sent to ${msg.phone}` : `Failed: ${data.error}`,
          data.success ? 'success' : 'error'
        )
      } else {
        res = await fetch(`/api/queue`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
          },
          credentials: 'include',
          body: JSON.stringify({
            agent_id: parseInt(selectedSender),
            phone: msg.phone,
            message: messageText
          })
        })
        data = await res.json()

        const newMessages = [...messages]
        newMessages[index] = {
          ...msg,
          status: data.success ? 'queued' : 'failed',
          error: data.error
        }
        setMessages(newMessages)
        showStatus(
          data.success ? `Queued for ${msg.phone}` : `Failed: ${data.error}`,
          data.success ? 'success' : 'error'
        )
      }
    } catch (e) {
      showStatus('Error: ' + e.message, 'error')
    }
  }

  const executeSendAll = async () => {
    for (let i = 0; i < messages.length; i++) {
      if (!messages[i].status) {
        await handleSendOne(i)
        await new Promise(r => setTimeout(r, 500))
      }
    }
  }

  const handleSendAll = () => {
    const unsent = messages.filter(m => !m.status)
    if (!unsent.length) return

    const action = selectedSender === 'local' ? 'Send' : 'Queue'
    setConfirmModal({
      open: true,
      message: `${action} ${unsent.length} messages?`,
      onConfirm: () => {
        setConfirmModal({ open: false, message: '', onConfirm: null })
        executeSendAll()
      }
    })
  }

  const updateMessage = (index, newMessage) => {
    const newMessages = [...messages]
    newMessages[index] = { ...newMessages[index], message: newMessage }
    setMessages(newMessages)
  }

  const processedCount = messages.filter(m => m.status === 'sent' || m.status === 'queued').length

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>iMessage Sender</h1>
        <div className="header-actions">
          <div className="sender-badge">
            Sending as <strong>{sender.name}</strong>
            <span className="phone">{sender.phone}</span>
            <button className="link-btn" onClick={onEditProfile} aria-label="Edit sender profile">edit</button>
          </div>
          <button className="link-btn" onClick={onLogout} aria-label="Log out of application">logout</button>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="card">
          <label htmlFor="sender-select">Send From</label>
          <select
            id="sender-select"
            name="sender"
            value={selectedSender}
            onChange={(e) => setSelectedSender(e.target.value)}
            className="sender-select"
          >
            <option value="local">This Mac - {sender.name} ({sender.phone})</option>
            {agents.map(agent => (
              <option key={agent.id} value={agent.id}>
                {agent.is_online ? '●' : '○'} {agent.name} ({agent.phone})
              </option>
            ))}
          </select>
          <span className="hint">
            {selectedSender === 'local'
              ? 'Messages will be sent directly from this Mac'
              : 'Messages will be queued for the remote agent'}
          </span>
        </div>

        <div className="card">
          <label htmlFor="sheet-url">Google Sheet URL</label>
          <input
            type="url"
            id="sheet-url"
            name="sheetUrl"
            value={sheetUrl}
            onChange={(e) => setSheetUrl(e.target.value)}
            placeholder="https://docs.google.com/spreadsheets/d/…"
            autoComplete="url"
          />
          <span className="hint">Must be public and have a "phone" column</span>
        </div>

        <div className="card">
          <label htmlFor="message-template">Message Template</label>
          <textarea
            id="message-template"
            name="template"
            value={template}
            onChange={(e) => setTemplate(e.target.value)}
            placeholder="Hi {name}, just following up on {topic}…"
            rows={3}
          />
          <span className="hint">Use {'{column_name}'} for variables from your sheet</span>
        </div>

        <button
          className="btn-primary"
          onClick={handlePreview}
          disabled={loading}
        >
          {loading ? 'Loading…' : 'Load Preview'}
        </button>

        <div
          className={`status-bar ${status.type}`}
          role="status"
          aria-live="polite"
          aria-atomic="true"
        >
          {status.text}
        </div>

        {messages.length > 0 && (
          <div className="card messages-card">
            <div className="messages-header">
              <h3>Messages ({messages.length})</h3>
              <div className="messages-actions">
                <span className="count">{processedCount}/{messages.length} processed</span>
                <span className={`mode-badge ${selectedSender === 'local' ? 'local' : 'remote'}`}>
                  {selectedSender === 'local' ? 'Direct Send' : 'Queue Mode'}
                </span>
              </div>
            </div>

            <div className="messages-list">
              {messages.map((msg, idx) => (
                <div key={idx} className={`message-row ${msg.status || ''}`}>
                  <div className="message-info">
                    <div className="phone">{msg.phone}</div>
                    <div className="name">{msg.name}</div>
                  </div>
                  <textarea
                    value={msg.message}
                    onChange={(e) => updateMessage(idx, e.target.value)}
                    disabled={msg.status === 'sent' || msg.status === 'queued'}
                    rows={2}
                    aria-label={`Message to ${msg.name || msg.phone}`}
                  />
                  <button
                    className={`btn-send ${msg.status || ''}`}
                    onClick={() => handleSendOne(idx)}
                    disabled={msg.status === 'sent' || msg.status === 'queued'}
                    aria-label={`${msg.status === 'sent' ? 'Sent to' : msg.status === 'queued' ? 'Queued for' : msg.status === 'failed' ? 'Retry sending to' : 'Send to'} ${msg.name || msg.phone}`}
                  >
                    {msg.status === 'sent' ? 'Sent' :
                     msg.status === 'queued' ? 'Queued' :
                     msg.status === 'failed' ? 'Retry' : 'Send'}
                  </button>
                </div>
              ))}
            </div>

            <div className="messages-footer">
              <button className="btn-success" onClick={handleSendAll}>
                Send All
              </button>
            </div>
          </div>
        )}
      </main>

      {confirmModal.open && (
        <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
          <div className="modal-content">
            <h2 id="confirm-title">Confirm Action</h2>
            <p>{confirmModal.message}</p>
            <div className="modal-actions">
              <button
                className="btn-cancel"
                onClick={() => setConfirmModal({ open: false, message: '', onConfirm: null })}
              >
                Cancel
              </button>
              <button
                className="btn-confirm"
                onClick={confirmModal.onConfirm}
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
