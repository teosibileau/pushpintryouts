import json

from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from chat import selectors, services
from chat.serializers import MessageFrameSerializer


def _send(ws, payload: dict) -> None:
    ws.send(json.dumps(payload))


def _send_error(ws, detail) -> None:
    _send(ws, {"event": "error", "detail": detail})


def _enter_chat(ws, user) -> None:
    for message in selectors.message_list_recent():
        _send(ws, services.message_payload(message))
    roster = sorted(set(selectors.online_usernames()) | {user.username})
    _send(ws, {"event": "roster", "usernames": roster})
    ws.subscribe(services.CHAT_CHANNEL)
    _send(ws, {"event": "authenticated", "username": user.username})
    services.connection_open(connection_id=ws.id, user=user)


def _handle_frame(ws, raw: str) -> None:
    try:
        frame = json.loads(raw)
        action = frame.get("action")
    except (json.JSONDecodeError, AttributeError):
        _send_error(ws, "invalid frame")
        return

    if action == "message":
        user = services.connection_user(connection_id=ws.id)
        if user is None:
            _send_error(ws, "not authenticated")
            return
        serializer = MessageFrameSerializer(data=frame)
        if not serializer.is_valid():
            _send_error(ws, serializer.errors)
            return
        services.message_create(user=user, **serializer.validated_data)
    else:
        _send_error(ws, f"unknown action: {action}")


@csrf_exempt
def ws_view(request):
    ws = request.wscontext
    if ws is None:
        return HttpResponseBadRequest("websocket only")

    if ws.is_opening():
        # the handshake carries the session cookie; anonymous sockets are refused
        if not request.user.is_authenticated:
            return HttpResponse(status=401)
        ws.accept()
        _enter_chat(ws, request.user)

    while ws.can_recv():
        try:
            raw = ws.recv()
        except OSError:
            # abrupt disconnect (tab closed, network drop); the socket is gone
            services.connection_close(connection_id=ws.id)
            break
        if raw is None:
            services.connection_close(connection_id=ws.id)
            ws.close()
            break
        _handle_frame(ws, raw)

    return HttpResponse()
