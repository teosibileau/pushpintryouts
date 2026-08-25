import json
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User


class FakeWs:
    """Stands in for gripcontrol's WebSocketContext in view tests."""

    def __init__(self, connection_id="conn-1", opening=False):
        self.id = connection_id
        self.opening = opening
        self.accepted = False
        self.closed = False
        self.sent = []
        self.subscribed = []
        self.incoming = []

    def is_opening(self):
        return self.opening

    def accept(self):
        self.accepted = True

    def close(self):
        self.closed = True

    def can_recv(self):
        return bool(self.incoming)

    def recv(self):
        return self.incoming.pop(0)

    def send(self, raw):
        self.sent.append(json.loads(raw))

    def subscribe(self, channel):
        self.subscribed.append(channel)

    def events(self, name):
        return [f for f in self.sent if f.get("event") == name]


@pytest.fixture
def ws():
    return FakeWs()


@pytest.fixture
def published():
    with patch("chat.services.publish") as mock:
        yield mock


def published_events(published):
    return [json.loads(call.args[1].content) for call in published.call_args_list]


@pytest.fixture
def alice(db):
    return User.objects.create_user(username="alice", password="secret123")
