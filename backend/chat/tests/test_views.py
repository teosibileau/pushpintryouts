import json

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from chat import services
from chat.models import Connection, Message
from chat.tests.conftest import FakeWs
from chat.views import WsView
from chat.ws import ChatConnection

pytestmark = pytest.mark.django_db


def frame(**kwargs):
    return json.dumps(kwargs)


def handshake(user, ws):
    request = RequestFactory().post("/ws")
    request.user = user
    request.wscontext = ws
    return WsView.as_view()(request)


class TestHandshake:
    def test_anonymous_is_refused(self, published):
        ws = FakeWs(opening=True)
        response = handshake(AnonymousUser(), ws)
        assert response.status_code == 401
        assert not ws.accepted

    def test_authenticated_enters_chat(self, alice, published):
        services.message_create(user=alice, text="old message")
        ws = FakeWs(opening=True)
        response = handshake(alice, ws)
        assert response.status_code == 200
        assert ws.accepted
        assert [m["text"] for m in ws.events("message")] == ["old message"]
        assert ws.events("roster") == [{"event": "roster", "usernames": ["alice"]}]
        assert ws.events("authenticated") == [
            {"event": "authenticated", "username": "alice"}
        ]
        assert ws.subscribed == [services.CHAT_CHANNEL]
        assert Connection.objects.filter(connection_id=ws.id, user=alice).exists()


class TestFrameParsing:
    def test_invalid_json(self, ws, published):
        ChatConnection(ws).handle_frame("not json")
        assert ws.events("error") == [{"event": "error", "detail": "invalid frame"}]

    def test_unknown_action(self, ws, published):
        ChatConnection(ws).handle_frame(frame(action="login"))
        assert ws.events("error")[0]["detail"] == "unknown action: login"


class TestMessage:
    def test_unauthenticated_connection_is_rejected(self, ws, published):
        ChatConnection(ws).handle_frame(frame(action="message", text="hi"))
        assert ws.events("error")[0]["detail"] == "not authenticated"
        assert not Message.objects.exists()

    def test_authenticated_connection_creates_message(self, ws, alice, published):
        services.connection_open(connection_id=ws.id, user=alice)
        ChatConnection(ws).handle_frame(frame(action="message", text="hi"))
        assert Message.objects.filter(user=alice, text="hi").exists()

    def test_missing_text_reports_serializer_errors(self, ws, alice, published):
        services.connection_open(connection_id=ws.id, user=alice)
        ChatConnection(ws).handle_frame(frame(action="message"))
        assert "text" in ws.events("error")[0]["detail"]
