# Pushpin chat PoC

Single-group chat behind Pushpin. Registration and login are normal
HTTP calls to a DRF api that sets a Django session cookie; the cookie
then authenticates the WebSocket handshake, and Pushpin translates the
socket into GRIP WebSocket-over-HTTP requests against a plain WSGI
Django backend. Messages and presence travel as frames on the socket.
Django and Pushpin are not reachable from the host.

## Topology

```
browser ── ws://localhost:5173/ws ──▶ vite (proxy) ──▶ pushpin ──▶ django ──▶ postgres
                                                        ▲                │
                                                        └── publish ◀────┘
```

## Run

Note for colima users: the VM must mount this directory for the front
bind mount to work, e.g. `colima start --mount "$PWD:w"`. The pushpin
routes file is baked into a small derived image instead of bind-mounted
for the same reason.

```
ahoy docker build
ahoy docker up
ahoy docker log
```

Open http://localhost:5173 in two browsers, register two users, chat.

## Protocol

HTTP (JSON, session cookie): `POST /api/register`, `POST /api/login`,
`POST /api/logout`, `GET /api/me`.

WebSocket: anonymous handshakes are refused with a 401. On an
authenticated handshake the server pushes the last 50 messages, the
online roster and an `authenticated` frame, then subscribes the
connection to the group channel. The only client → server frame is
`{"action": "message", "text": "..."}`; server → client frames are
`authenticated`, `message`, `roster`, `joined`, `left`, `error`.

Frames after the handshake carry no browser cookie, so a Postgres
table maps Pushpin's connection id to a user, written at handshake and
removed on disconnect. The table is wiped on Django startup since
sockets cannot survive a stack restart.
