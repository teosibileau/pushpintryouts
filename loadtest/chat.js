// k6 stress test for the chat: each VU registers, opens a websocket
// through the full chain, and chatters. Measures handshake time (connect
// to `authenticated` frame) and message round-trip (send to own message
// coming back down the socket, which traverses nginx -> pushpin ->
// django-pool -> publish -> pushpin fan-out).
//
//   brew install k6
//   k6 run loadtest/chat.js                          # gentle default
//   k6 run -e VUS=100 -e DURATION=2m loadtest/chat.js
//   k6 run -e MSG_INTERVAL=2 loadtest/chat.js        # chattier users
//   k6 run -e BASE=http://localhost:5173 loadtest/chat.js  # dev stack
//
// Fan-out grows quadratically: VUS sockets each sending every
// MSG_INTERVAL seconds means pushpin delivers VUS^2/MSG_INTERVAL
// frames/s downstream. Ramp VUS and MSG_INTERVAL separately.
//
// Every message lands in the Message table; test users pile up too.
// Cleanup afterwards:
//
//   ahoy deploy env kamal app exec -c config/deploy.django.yml \
//     "python manage.py shell -c \"from django.contrib.auth.models import User; from chat.models import Message; Message.objects.filter(user__username__startswith='k6_').delete(); User.objects.filter(username__startswith='k6_').delete()\""

import http from 'k6/http'
import ws from 'k6/ws'
import { check } from 'k6'
import { Trend, Counter } from 'k6/metrics'

const BASE = __ENV.BASE || 'https://ppchat.corvus.observer'
const WS_BASE = BASE.replace('https', 'wss').replace('http', 'ws')
const MSG_INTERVAL = Number(__ENV.MSG_INTERVAL || 5) // seconds between messages
const SESSION = Number(__ENV.SESSION || 30) // seconds each socket stays open

const handshakeTime = new Trend('chat_handshake_ms')
const messageRtt = new Trend('chat_message_rtt_ms')
const wsErrors = new Counter('chat_ws_errors')
const serverErrors = new Counter('chat_server_error_frames')

export const options = {
  scenarios: {
    chatters: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: __ENV.RAMP || '30s', target: Number(__ENV.VUS || 20) },
        { duration: __ENV.DURATION || '1m', target: Number(__ENV.VUS || 20) },
        { duration: '15s', target: 0 },
      ],
    },
  },
  thresholds: {
    chat_handshake_ms: ['p(95)<2000'],
    chat_message_rtt_ms: ['p(95)<1000'],
    chat_ws_errors: ['count==0'],
    http_req_failed: ['rate<0.01'],
  },
}

export default function () {
  const username = `k6_${__ENV.RUN || 'run'}_${__VU}_${__ITER}`
  const res = http.post(
    `${BASE}/api/register`,
    JSON.stringify({ username, password: 'stresstest123' }),
    { headers: { 'Content-Type': 'application/json' } },
  )
  if (!check(res, { 'registered (201)': (r) => r.status === 201 || r.status === 200 })) {
    return
  }
  const token = res.json('access')

  const started = Date.now()
  const result = ws.connect(`${WS_BASE}/ws?token=${token}`, {}, (socket) => {
    socket.on('open', () => {
      socket.setTimeout(() => socket.close(), SESSION * 1000)
    })

    socket.on('message', (raw) => {
      const frame = JSON.parse(raw)
      switch (frame.event) {
        case 'authenticated':
          handshakeTime.add(Date.now() - started)
          socket.setInterval(() => {
            socket.send(JSON.stringify({ action: 'message', text: `${username} ${Date.now()}` }))
          }, MSG_INTERVAL * 1000)
          break
        case 'message': {
          // round-trip: only time our own messages, via the stamped text
          const [sender, sentAt] = frame.text ? frame.text.split(' ') : []
          if (sender === username) messageRtt.add(Date.now() - Number(sentAt))
          break
        }
        case 'error':
          serverErrors.add(1)
          break
      }
    })

    socket.on('error', () => wsErrors.add(1))
  })

  check(result, { 'ws handshake (101)': (r) => r && r.status === 101 })
}
