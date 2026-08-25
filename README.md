# Pushpin chat PoC

Single-group chat where the browser talks only to a WebSocket. Pushpin
translates the socket into GRIP WebSocket-over-HTTP requests against a
plain WSGI Django backend. Registration, login, messaging and presence
all travel as JSON frames on the one socket; Django and Pushpin are not
reachable from the host.

## Topology

```
browser ── ws://localhost:5173/ws ──▶ vite (proxy) ──▶ pushpin ──▶ django ──▶ postgres
                                                        ▲                │
                                                        └── publish ◀────┘
```

## Run

```
ahoy docker build
ahoy docker up
ahoy docker log
```

Open http://localhost:5173 in two browsers, register two users, chat.

## Protocol

Client → server frames:

- `{"action": "register", "username": "...", "password": "..."}`
- `{"action": "login", "username": "...", "password": "..."}`
- `{"action": "message", "text": "..."}`

Server → client frames: `authenticated`, `message`, `roster`, `joined`,
`left`, `error`.

Auth is a Postgres table mapping Pushpin's connection id to a user,
written at login and removed on disconnect. No sessions, no tokens.
The table is wiped on Django startup since sockets cannot survive a
stack restart.
