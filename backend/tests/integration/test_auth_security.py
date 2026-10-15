from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient

from app.main import create_app

BROWSER = {"X-Requested-With": "XMLHttpRequest"}


def test_logout_and_password_change_revoke_bearer_tokens(settings):
    with TestClient(create_app(settings)) as client:
        data = {"email": "revoke@example.com", "password": "Senha-segura-123"}
        client.post("/api/v1/auth/register", json=data)
        first = client.post("/api/v1/auth/login", json=data).json()["access_token"]
        headers = {"Authorization": f"Bearer {first}"}
        assert client.get("/api/v1/auth/me", headers=headers).status_code == 200

        assert (
            client.post("/api/v1/auth/logout", headers=BROWSER | headers).status_code
            == 204
        )
        assert client.get("/api/v1/auth/me", headers=headers).status_code == 401

        second = client.post("/api/v1/auth/login", json=data).json()["access_token"]
        headers = {"Authorization": f"Bearer {second}"}
        assert (
            client.post(
                "/api/v1/auth/change-password",
                headers=headers,
                json={
                    "current_password": data["password"],
                    "password": "Nova-senha-12345",
                },
            ).status_code
            == 204
        )
        assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
        renewed = client.post(
            "/api/v1/auth/login",
            json={"email": data["email"], "password": "Nova-senha-12345"},
        )
        assert renewed.status_code == 200
        assert (
            client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {renewed.json()['access_token']}"},
            ).status_code
            == 200
        )


def test_token_without_version_claim_is_rejected(settings):
    with TestClient(create_app(settings)) as client:
        data = {"email": "legacy-token@example.com", "password": "Senha-segura-123"}
        client.post("/api/v1/auth/register", json=data)
        now = datetime.now(UTC)
        token = jwt.encode(
            {
                "sub": "1",
                "iat": now,
                "exp": now + timedelta(minutes=30),
            },
            settings.jwt_secret.get_secret_value(),
            algorithm="HS256",
        )
        assert (
            client.get(
                "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
            ).status_code
            == 401
        )


def test_auth_endpoints_are_rate_limited(tmp_path):
    from app.infrastructure.config import Settings

    settings = Settings(
        _env_file=None,
        jwt_secret="test-only-secret-" * 4,
        database_url=f"sqlite:///{tmp_path / 'rate.db'}",
        cors_origins=["http://localhost:5173"],
        auth_rate_limit=3,
        auth_rate_window_seconds=60,
    )
    with TestClient(create_app(settings)) as client:
        payload = {"email": "limit@example.com", "password": "wrong-password"}
        statuses = [
            client.post("/api/v1/auth/login", json=payload).status_code
            for _ in range(4)
        ]
        assert statuses[:3] == [401, 401, 401]
        assert statuses[3] == 429
        limited = client.post("/api/v1/auth/login", json=payload)
        assert limited.status_code == 429
        assert limited.json() == {
            "detail": "Muitas tentativas. Tente novamente em instantes."
        }
        assert "retry-after" in {key.lower() for key in limited.headers}
