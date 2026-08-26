import json

from chat import selectors, services
from chat.serializers import MessageFrameSerializer


class ChatConnection:
    """Wraps a GRIP websocket context for one delivery of events."""

    def __init__(self, ws):
        self.ws = ws

    def process(self, user) -> bool:
        """Handle every event in this delivery. False means the handshake
        was refused and the caller should respond 401."""
        if self.ws.is_opening():
            if not user.is_authenticated:
                return False
            self.ws.accept()
            self._enter_chat(user)
        self._pump()
        return True

    def handle_frame(self, raw: str) -> None:
        try:
            frame = json.loads(raw)
            action = frame.get("action")
        except (json.JSONDecodeError, AttributeError):
            self._send_error("invalid frame")
            return

        if action == "message":
            self._handle_message(frame)
        else:
            self._send_error(f"unknown action: {action}")

    def _handle_message(self, frame: dict) -> None:
        user = services.connection_user(connection_id=self.ws.id)
        if user is None:
            self._send_error("not authenticated")
            return
        serializer = MessageFrameSerializer(data=frame)
        if not serializer.is_valid():
            self._send_error(serializer.errors)
            return
        services.message_create(user=user, **serializer.validated_data)

    def _enter_chat(self, user) -> None:
        for message in selectors.message_list_recent():
            self._send(services.message_payload(message))
        roster = sorted(set(selectors.online_usernames()) | {user.username})
        self._send({"event": "roster", "usernames": roster})
        self.ws.subscribe(services.CHAT_CHANNEL)
        self._send({"event": "authenticated", "username": user.username})
        services.connection_open(connection_id=self.ws.id, user=user)

    def _pump(self) -> None:
        while self.ws.can_recv():
            try:
                raw = self.ws.recv()
            except OSError:
                # abrupt disconnect (tab closed, network drop); the socket is gone
                self._disconnect()
                break
            if raw is None:
                self._close()
                break
            self.handle_frame(raw)

    def _close(self) -> None:
        services.connection_close(connection_id=self.ws.id)
        self.ws.close()

    def _disconnect(self) -> None:
        services.connection_close(connection_id=self.ws.id)

    def _send(self, payload: dict) -> None:
        self.ws.send(json.dumps(payload))

    def _send_error(self, detail) -> None:
        self._send({"event": "error", "detail": detail})
