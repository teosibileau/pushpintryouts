import json

import pytest

from chat import services
from chat.models import Connection, Message
from chat.views import _handle_frame

pytestmark = pytest.mark.django_db


def frame(**kwargs):
    return json.dumps(kwargs)


class TestFrameParsing:
    def test_invalid_json(self, ws, published):
        _handle_frame(ws, "not json")
        assert ws.events("error") == [{"event": "error", "detail": "invalid frame"}]

    def test_unknown_action(self, ws, published):
        _handle_frame(ws, frame(action="dance"))
        assert ws.events("error")[0]["detail"] == "unknown action: dance"

    def test_missing_fields_reports_serializer_errors(self, ws, published):
        _handle_frame(ws, frame(action="login", username="alice"))
        assert "password" in ws.events("error")[0]["detail"]


class TestRegister:
    def test_enters_chat(self, ws, published):
        _handle_frame(ws, frame(action="register", username="bob", password="pw12345"))
        assert ws.events("authenticated") == [{"event": "authenticated", "username": "bob"}]
        assert ws.events("roster") == [{"event": "roster", "usernames": ["bob"]}]
        assert ws.subscribed == [services.CHAT_CHANNEL]
        assert Connection.objects.filter(connection_id=ws.id, user__username="bob").exists()

    def test_taken_username(self, ws, alice, published):
        _handle_frame(ws, frame(action="register", username="alice", password="pw12345"))
        assert ws.events("error")[0]["detail"] == "username taken"
        assert ws.subscribed == []


class TestLogin:
    def test_wrong_password(self, ws, alice, published):
        _handle_frame(ws, frame(action="login", username="alice", password="nope"))
        assert ws.events("error")[0]["detail"] == "invalid credentials"
        assert ws.subscribed == []

    def test_receives_history_and_roster(self, ws, alice, published):
        services.message_create(user=alice, text="old message")
        _handle_frame(ws, frame(action="login", username="alice", password="secret123"))
        assert [m["text"] for m in ws.events("message")] == ["old message"]
        assert ws.events("roster") == [{"event": "roster", "usernames": ["alice"]}]


class TestMessage:
    def test_unauthenticated_connection_is_rejected(self, ws, published):
        _handle_frame(ws, frame(action="message", text="hi"))
        assert ws.events("error")[0]["detail"] == "not authenticated"
        assert not Message.objects.exists()

    def test_authenticated_connection_creates_message(self, ws, alice, published):
        _handle_frame(ws, frame(action="login", username="alice", password="secret123"))
        _handle_frame(ws, frame(action="message", text="hi"))
        assert Message.objects.filter(user=alice, text="hi").exists()
