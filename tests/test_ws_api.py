import json

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from chat import services
from chat.api import WsView
from chat.models import Connection, Message
from chat.ws import ChatConnection
from tests.conftest import FakeWs

pytestmark = pytest.mark.django_db


def frame(**kwargs):
    return json.dumps(kwargs)


def handshake(user, ws):
    request = RequestFactory().post("/ws")
    request.user = user
    request.wscontext = ws
    return WsView.as_view()(request)


class TestNonWebsocketRequest:
    def test_is_rejected_by_the_decorator(self):
        request = RequestFactory().post("/ws")
        request.user = AnonymousUser()
        request.wscontext = None
        response = WsView.as_view()(request)
        assert response.status_code == 400

    def test_websocket_events_accept_header_is_not_406(self, client, alice, published):
        # regression: DRF content negotiation must ignore Pushpin's Accept
        # header, and django-grip must round-trip the event framing
        client.post("/api/login", {"username": "alice", "password": "secret123"})
        response = client.post(
            "/ws",
            data=b"OPEN\r\n",
            content_type="application/websocket-events",
            HTTP_ACCEPT="application/websocket-events",
            HTTP_CONNECTION_ID="test-conn",
        )
        assert response.status_code == 200
        assert response.content.startswith(b"OPEN")


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
