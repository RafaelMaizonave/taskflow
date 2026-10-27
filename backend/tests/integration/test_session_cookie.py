from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient

from app.main import create_app

BROWSER = {"X-Requested-With": "XMLHttpRequest"}


def test_cookie_session_logout_and_csrf(settings):
    with TestClient(create_app(settings)) as client:
        data = {"email": "cookie@example.com", "password": "Senha-segura-123"}
        client.post("/api/v1/auth/register", json=data)
        response = client.post("/api/v1/auth/login", json=data)
        bearer = response.json()["access_token"]
        cookie = response.headers["set-cookie"]
        assert "HttpOnly" in cookie
        assert "SameSite=strict" in cookie
        assert "Max-Age=1800" in cookie
        assert "Path=/api/v1" in cookie
        assert client.get("/api/v1/auth/me").status_code == 200
        assert (
            client.post("/api/v1/tasks", json={"titulo": "Bloqueada"}).status_code
            == 403
        )
        assert (
            client.post(
                "/api/v1/tasks", json={"titulo": "Permitida"}, headers=BROWSER
            ).status_code
            == 201
        )
        assert client.post("/api/v1/auth/logout").status_code == 403
        assert client.post("/api/v1/auth/logout", headers=BROWSER).status_code == 204
        assert client.get("/api/v1/auth/me").status_code == 401
        assert (
            client.get(
                "/api/v1/auth/me", headers={"Authorization": f"Bearer {bearer}"}
            ).status_code
            == 401
        )


def test_expired_cookie_and_https_flags(settings):
    with TestClient(create_app(settings), base_url="https://testserver") as client:
        data = {"email": "https@example.com", "password": "Senha-segura-123"}
        client.post("/api/v1/auth/register", json=data)
        response = client.post("/api/v1/auth/login", json=data)
        assert "Secure" in response.headers["set-cookie"]
        expired = jwt.encode(
            {
                "sub": "1",
                "iat": datetime.now(UTC) - timedelta(hours=1),
                "exp": datetime.now(UTC) - timedelta(seconds=1),
            },
            settings.jwt_secret.get_secret_value(),
            algorithm="HS256",
        )
        client.cookies.clear()
        client.cookies.set("taskflow_session", expired, path="/api/v1")
        assert client.get("/api/v1/auth/me").status_code == 401


def session_token(set_cookie: str) -> str:
    value = set_cookie.split(";", 1)[0]
    marker = "taskflow_session="
    assert value.startswith(marker)
    return value.removeprefix(marker)


def test_password_change_refreshes_current_cookie(settings):
    with TestClient(create_app(settings)) as client:
        data = {"email": "renew@example.com", "password": "Senha-segura-123"}
        client.post("/api/v1/auth/register", json=data)
        login = client.post("/api/v1/auth/login", json=data)
        previous = login.json()["access_token"]
        changed = client.post(
            "/api/v1/auth/change-password",
            headers=BROWSER,
            json={
                "current_password": data["password"],
                "password": "Nova-senha-12345",
            },
        )
        assert changed.status_code == 204
        cookie = changed.headers["set-cookie"]
        assert "HttpOnly" in cookie
        assert "Path=/api/v1" in cookie
        renewed = session_token(cookie)
        assert renewed != previous
        secret = settings.jwt_secret.get_secret_value()
        previous_claims = jwt.decode(previous, secret, algorithms=["HS256"])
        renewed_claims = jwt.decode(renewed, secret, algorithms=["HS256"])
        assert renewed_claims["sub"] == previous_claims["sub"]
        assert renewed_claims["tv"] == previous_claims["tv"] + 1
        assert client.get("/api/v1/auth/me").status_code == 200
        created = client.post(
            "/api/v1/tasks",
            json={"titulo": "Depois da senha"},
            headers=BROWSER,
        )
        assert created.status_code == 201
        assert (
            client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {previous}"},
            ).status_code
            == 401
        )
