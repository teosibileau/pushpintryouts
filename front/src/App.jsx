import { useEffect, useRef, useState } from 'react'

const tokens = {
  get access() {
    try {
      return localStorage.getItem('access')
    } catch {
      return null
    }
  },
  save(access, refresh) {
    try {
      localStorage.setItem('access', access)
      localStorage.setItem('refresh', refresh)
    } catch {}
  },
  clear() {
    try {
      localStorage.removeItem('access')
      localStorage.removeItem('refresh')
    } catch {}
  },
}

async function api(path, options = {}) {
  const headers = options.body ? { 'Content-Type': 'application/json' } : {}
  if (tokens.access) headers.Authorization = `Bearer ${tokens.access}`
  const res = await fetch(`/api/${path}`, {
    method: options.body ? 'POST' : 'GET',
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  })
  const data = res.status === 204 ? null : await res.json().catch(() => null)
  return { ok: res.ok, data }
}

export default function App() {
  const wsRef = useRef(null)
  const [checked, setChecked] = useState(false)
  const [me, setMe] = useState(null)
  const [messages, setMessages] = useState([])
  const [roster, setRoster] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!tokens.access) {
      setChecked(true)
      return
    }
    api('me').then(({ ok, data }) => {
      if (ok) setMe(data.username)
      else tokens.clear()
      setChecked(true)
    })
  }, [])

  useEffect(() => {
    if (!me) return
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${proto}://${location.host}/ws?token=${tokens.access}`)
    wsRef.current = ws
    ws.onmessage = (e) => {
      const frame = JSON.parse(e.data)
      switch (frame.event) {
        case 'message':
          setMessages((prev) => [...prev, frame])
          break
        case 'roster':
          setRoster(frame.usernames)
          break
        case 'joined':
          setRoster((prev) => (prev.includes(frame.username) ? prev : [...prev, frame.username].sort()))
          setMessages((prev) => [...prev, { system: true, text: `${frame.username} joined` }])
          break
        case 'left':
          setRoster((prev) => prev.filter((u) => u !== frame.username))
          setMessages((prev) => [...prev, { system: true, text: `${frame.username} left` }])
          break
        case 'error':
          setError(typeof frame.detail === 'string' ? frame.detail : JSON.stringify(frame.detail))
          break
      }
    }
    return () => ws.close()
  }, [me])

  const authenticate = async (action, username, password) => {
    const { ok, data } = await api(action, { body: { username, password } })
    if (ok) {
      tokens.save(data.access, data.refresh)
      setError(null)
      setMe(data.username)
    } else {
      setError(data?.detail ? JSON.stringify(data.detail) : 'request failed')
    }
  }

  const logoutUser = () => {
    tokens.clear()
    wsRef.current?.close()
    setMe(null)
    setMessages([])
    setRoster([])
    setError(null)
  }

  if (!checked) return null
  if (!me) {
    return <AuthForm error={error} onSubmit={authenticate} />
  }
  return (
    <Chat
      me={me}
      messages={messages}
      roster={roster}
      error={error}
      onSend={(text) => wsRef.current?.send(JSON.stringify({ action: 'message', text }))}
      onLogout={logoutUser}
    />
  )
}

function AuthForm({ error, onSubmit }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const submit = (action) => (e) => {
    e.preventDefault()
    onSubmit(action, username, password)
  }

  return (
    <div className="auth">
      <h1>Pushpin Chat</h1>
      <form onSubmit={submit('login')}>
        <input
          placeholder="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoFocus
        />
        <input
          type="password"
          placeholder="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <div className="buttons">
          <button type="submit">Login</button>
          <button type="button" onClick={submit('register')}>
            Register
          </button>
        </div>
      </form>
      {error && <p className="error">{error}</p>}
    </div>
  )
}

function Chat({ me, messages, roster, error, onSend, onLogout }) {
  const [text, setText] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const submit = (e) => {
    e.preventDefault()
    if (!text.trim()) return
    onSend(text)
    setText('')
  }

  return (
    <div className="chat">
      <aside>
        <h2>Online</h2>
        <ul>
          {roster.map((u) => (
            <li key={u}>{u === me ? `${u} (you)` : u}</li>
          ))}
        </ul>
        <button className="logout" onClick={onLogout}>
          Logout
        </button>
      </aside>
      <main>
        <div className="messages">
          {messages.map((m, i) =>
            m.system ? (
              <p key={i} className="system">
                {m.text}
              </p>
            ) : (
              <p key={i}>
                <strong>{m.username}</strong> {m.text}
              </p>
            ),
          )}
          <div ref={bottomRef} />
        </div>
        {error && <p className="error">{error}</p>}
        <form onSubmit={submit}>
          <input
            placeholder="say something…"
            value={text}
            onChange={(e) => setText(e.target.value)}
            autoFocus
          />
          <button type="submit">Send</button>
        </form>
      </main>
    </div>
  )
}
