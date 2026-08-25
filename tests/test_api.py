import pytest
from rest_framework_simplejwt.tokens import RefreshToken

pytestmark = pytest.mark.django_db


def bearer(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}


class TestRegister:
    def test_creates_user_and_returns_tokens(self, client):
        response = client.post(
            "/api/register", {"username": "bob", "password": "pw12345"}
        )
        assert response.status_code == 201
        body = response.json()
        assert body["username"] == "bob"
        assert body["access"] and body["refresh"]

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
    def test_valid_credentials_return_tokens(self, client, alice):
        response = client.post(
            "/api/login", {"username": "alice", "password": "secret123"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["username"] == "alice"
        assert body["access"] and body["refresh"]

    def test_wrong_password(self, client, alice):
        response = client.post("/api/login", {"username": "alice", "password": "nope"})
        assert response.status_code == 401


class TestRefresh:
    def test_refresh_returns_new_access(self, client, alice):
        refresh = str(RefreshToken.for_user(alice))
        response = client.post("/api/refresh", {"refresh": refresh})
        assert response.status_code == 200
        assert response.json()["access"]


class TestMe:
    def test_bearer_token_identifies_user(self, client, alice):
        response = client.get("/api/me", **bearer(alice))
        assert response.status_code == 200
        assert response.json() == {"username": "alice"}

    def test_anonymous_is_401(self, client):
        assert client.get("/api/me").status_code == 401

    def test_garbage_token_is_401(self, client):
        response = client.get("/api/me", HTTP_AUTHORIZATION="Bearer garbage")
        assert response.status_code == 401
