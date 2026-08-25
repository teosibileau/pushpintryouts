import json

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django_grip import publish
from gripcontrol import WebSocketMessageFormat

from chat.models import Connection, Message

CHAT_CHANNEL = "chat"


def _broadcast(payload: dict) -> None:
    publish(CHAT_CHANNEL, WebSocketMessageFormat(json.dumps(payload)))


def message_payload(message: Message) -> dict:
    return {
        "event": "message",
        "username": message.user.username,
        "text": message.text,
        "created_at": message.created_at.isoformat(),
    }


def user_register(*, username: str, password: str) -> User | None:
    try:
        with transaction.atomic():
            return User.objects.create_user(username=username, password=password)
    except IntegrityError:
        return None


def user_login(*, username: str, password: str) -> User | None:
    return authenticate(username=username, password=password)


def connection_open(*, connection_id: str, user: User) -> None:
    first = not Connection.objects.filter(user=user).exists()
    Connection.objects.update_or_create(
        connection_id=connection_id, defaults={"user": user}
    )
    if first:
        _broadcast({"event": "joined", "username": user.username})


def connection_close(*, connection_id: str) -> None:
    connection = (
        Connection.objects.select_related("user")
        .filter(connection_id=connection_id)
        .first()
    )
    if connection is None:
        return
    user = connection.user
    connection.delete()
    if not Connection.objects.filter(user=user).exists():
        _broadcast({"event": "left", "username": user.username})


def connection_user(*, connection_id: str) -> User | None:
    connection = (
        Connection.objects.select_related("user")
        .filter(connection_id=connection_id)
        .first()
    )
    return connection.user if connection else None


def message_create(*, user: User, text: str) -> Message:
    message = Message.objects.create(user=user, text=text)
    _broadcast(message_payload(message))
    return message
