import { useEffect, useRef, useState } from 'react'

export default function App() {
  const wsRef = useRef(null)
  const [connected, setConnected] = useState(false)
  const [me, setMe] = useState(null)
  const [messages, setMessages] = useState([])
  const [roster, setRoster] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${proto}://${location.host}/ws`)
    wsRef.current = ws
    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onmessage = (e) => {
      const frame = JSON.parse(e.data)
      switch (frame.event) {
        case 'authenticated':
          setMe(frame.username)
          setError(null)
          break
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
  }, [])

  const send = (payload) => wsRef.current?.send(JSON.stringify(payload))

  if (!me) {
    return <AuthForm connected={connected} error={error} onSubmit={send} />
  }
  return (
    <Chat
      me={me}
      messages={messages}
      roster={roster}
      error={error}
      onSend={(text) => send({ action: 'message', text })}
    />
  )
}

function AuthForm({ connected, error, onSubmit }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const submit = (action) => (e) => {
    e.preventDefault()
    onSubmit({ action, username, password })
  }

  return (
    <div className="auth">
      <h1>Pushpin Chat</h1>
      <p className="status">{connected ? 'socket connected' : 'connecting…'}</p>
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
          <button type="submit" disabled={!connected}>
            Login
          </button>
          <button type="button" disabled={!connected} onClick={submit('register')}>
            Register
          </button>
        </div>
      </form>
      {error && <p className="error">{error}</p>}
    </div>
  )
}

function Chat({ me, messages, roster, error, onSend }) {
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
