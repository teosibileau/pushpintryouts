import pytest

from chat import services
from chat.models import Connection, Message
from chat.tests.conftest import published_events

pytestmark = pytest.mark.django_db


class TestUserRegister:
    def test_creates_user_with_hashed_password(self):
        user = services.user_register(username="bob", password="pw12345")
        assert user.check_password("pw12345")

    def test_duplicate_username_returns_none(self, alice):
        assert services.user_register(username="alice", password="other") is None


class TestUserLogin:
    def test_valid_credentials(self, alice):
        assert services.user_login(username="alice", password="secret123") == alice

    def test_wrong_password_returns_none(self, alice):
        assert services.user_login(username="alice", password="nope") is None


class TestConnectionOpen:
    def test_first_connection_broadcasts_joined(self, alice, published):
        services.connection_open(connection_id="c1", user=alice)
        assert {"event": "joined", "username": "alice"} in published_events(published)

    def test_second_connection_is_silent(self, alice, published):
        services.connection_open(connection_id="c1", user=alice)
        published.reset_mock()
        services.connection_open(connection_id="c2", user=alice)
        assert published_events(published) == []


class TestConnectionClose:
    def test_last_connection_broadcasts_left(self, alice, published):
        services.connection_open(connection_id="c1", user=alice)
        services.connection_close(connection_id="c1")
        assert {"event": "left", "username": "alice"} in published_events(published)
        assert not Connection.objects.exists()

    def test_non_last_connection_is_silent(self, alice, published):
        services.connection_open(connection_id="c1", user=alice)
        services.connection_open(connection_id="c2", user=alice)
        published.reset_mock()
        services.connection_close(connection_id="c1")
        assert published_events(published) == []

    def test_unknown_connection_is_a_noop(self, published):
        services.connection_close(connection_id="ghost")
        assert published_events(published) == []


class TestMessageCreate:
    def test_persists_and_broadcasts(self, alice, published):
        message = services.message_create(user=alice, text="hi")
        assert Message.objects.count() == 1
        events = published_events(published)
        assert events[0]["event"] == "message"
        assert events[0]["username"] == "alice"
        assert events[0]["text"] == "hi"
        assert events[0]["created_at"] == message.created_at.isoformat()
