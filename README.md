# Pushpin chat PoC

Single-group chat behind Pushpin. Registration and login are normal
HTTP calls to a DRF api that return a JWT pair (simplejwt); the access
token authenticates api calls as a Bearer header and the WebSocket
handshake as a ?token= query parameter, since browsers cannot set
headers on an upgrade. Pushpin translates the socket into GRIP
WebSocket-over-HTTP requests against a plain WSGI Django backend.
Messages and presence travel as frames on the socket. Django and
Pushpin are not reachable from the host.

## Topology

```
browser ── http://localhost:5173 ──▶ vite dev server
              /api/* and /ws  ──▶  (proxy) ──▶ pushpin ──▶ django ──▶ postgres
                                                 ▲                │
                                                 └── publish ◀────┘
```

The Vite dev server on port 5173 is the only published port. It serves
the React app and proxies `/api` and `/ws` to Pushpin, which is the
sole way into Django. Django publishes outbound frames to Pushpin's
control port (5561) via `django-grip`.

## Stack

- `backend/`: Django 5 + DRF, WSGI under gunicorn, Poetry-managed.
  HackSoft-style layout: `services.py` and `selectors.py` hold the
  logic, `apis.py` and `views.py` stay thin.
- `front/`: React + Vite, one WebSocket plus a few fetch calls.
- `.docker/`: the Dockerfiles (backend, front, pushpin) and pushpin's
  routes file (`* django:8000,over_http`).
- Postgres 16 for users, messages and live connections.

## Run

```
ahoy docker build
ahoy docker up
ahoy docker log
```

Open http://localhost:5173 in two browsers, register two users, chat.

Everything is baked into images at build time, with no bind mounts, so
after changing code rebuild the affected service:
`ahoy docker build front && ahoy docker up front` (same for django).

Other useful commands: `ahoy test` (pytest in the django container),
`ahoy manage <cmd>` (manage.py), `ahoy docker ps|stop|reset|destroy`.

## Protocol

HTTP (JSON): `POST /api/register` and `POST /api/login` return
`{username, access, refresh}`; `POST /api/refresh` renews the access
token; `GET /api/me` identifies the Bearer token. There is no logout
endpoint: discarding the tokens is the logout.

WebSocket: the client connects to `/ws?token=<access>`; handshakes
without a valid token are refused with a 401. On an authenticated
handshake the server pushes the last 50 messages, the
online roster and an `authenticated` frame, then subscribes the
connection to the group channel. The only client → server frame is
`{"action": "message", "text": "..."}`; server → client frames are
`authenticated`, `message`, `roster`, `joined`, `left`, `error`.

Frames after the handshake carry no browser cookie, so a Postgres
table maps Pushpin's connection id to a user, written at handshake and
removed on disconnect. Presence broadcasts fire on a user's first
connection and last disconnect, so extra tabs stay silent. The table
is wiped on Django startup since sockets cannot survive a stack
restart.

## Tests and CI

`ahoy test` runs the pytest suite (services, frame protocol, api
endpoints, handshake auth) against Postgres inside the stack. GitHub
Actions runs three jobs on push and PR: ruff lint and format check,
the pytest suite against a Postgres service, and a Vite production
build. Ruff and the test deps are in the Poetry dev group, so the same
checks run identically in the container, locally and in CI.
