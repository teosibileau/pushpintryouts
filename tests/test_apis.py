import pytest

pytestmark = pytest.mark.django_db


class TestRegister:
    def test_creates_user_and_session(self, client):
        response = client.post(
            "/api/register", {"username": "bob", "password": "pw12345"}
        )
        assert response.status_code == 201
        assert response.json() == {"username": "bob"}
        assert client.get("/api/me").json() == {"username": "bob"}

    def test_taken_username(self, client, alice):
        response = client.post(
            "/api/register", {"username": "alice", "password": "pw12345"}
        )
        assert response.status_code == 400
        assert response.json() == {"detail": "username taken"}

    def test_missing_fields(self, client):
        response = client.post("/api/register", {"username": "bob"})
        assert response.status_code == 400


class TestLogin:
    def test_valid_credentials_set_session(self, client, alice):
        response = client.post(
            "/api/login", {"username": "alice", "password": "secret123"}
        )
        assert response.status_code == 200
        assert client.get("/api/me").json() == {"username": "alice"}

    def test_wrong_password(self, client, alice):
        response = client.post("/api/login", {"username": "alice", "password": "nope"})
        assert response.status_code == 401
        assert client.get("/api/me").status_code == 401


class TestLogout:
    def test_clears_session(self, client, alice):
        client.post("/api/login", {"username": "alice", "password": "secret123"})
        response = client.post("/api/logout")
        assert response.status_code == 204
        assert client.get("/api/me").status_code == 401


class TestMe:
    def test_anonymous_is_401(self, client):
        assert client.get("/api/me").status_code == 401
