from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.infrastructure.auth import get_passwords
from app.infrastructure.database.models import UserModel
from app.main import create_app


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as client:
        yield client


def credentials(email="rafael@example.com", password="Senha-segura-123"):
    return {"email": email, "password": password}


def test_register_login_and_current_user(client):
    data = credentials("  Rafael@EXAMPLE.com  ")
    response = client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["email"] == "rafael@example.com"
    assert response.json()["name"] == ""
    assert response.json()["created_at"] is not None
    with client.app.state.database.session() as session:
        user = session.scalar(select(UserModel))
        assert user.password_hash != data["password"]
        assert get_passwords().verify(user.password_hash, data["password"])
    token = client.post("/api/v1/auth/login", json=data).json()
    assert token["token_type"] == "bearer"
    assert token["expires_in"] == 1800
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token['access_token']}"}
    )
    assert response.json()["id"] == 1
    assert response.json()["email"] == "rafael@example.com"
    assert response.json()["name"] == ""
    assert response.json()["created_at"] is not None
    assert "password" not in response.text


def test_duplicate_email_and_rollback(client):
    assert client.post("/api/v1/auth/register", json=credentials()).status_code == 201
    assert (
        client.post(
            "/api/v1/auth/register", json=credentials("RAFAEL@example.com")
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/v1/auth/register", json=credentials("outro@example.com")
        ).status_code
        == 201
    )


def test_invalid_logins_are_uniform(client):
    client.post("/api/v1/auth/register", json=credentials())
    missing = client.post("/api/v1/auth/login", json=credentials("unknown@example.com"))
    wrong = client.post(
        "/api/v1/auth/login", json=credentials(password="wrong-password")
    )
    assert missing.status_code == wrong.status_code == 401
    assert missing.json() == wrong.json()
    assert missing.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "changes",
    [
        {"password": "segredo"},
        {"password": "x" * 129},
        {"email": "invalid"},
        {"extra": "blocked"},
        {"password": None},
    ],
)
def test_validation_never_exposes_credentials(client, changes):
    data = credentials() | changes
    response = client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 422
    assert all("input" not in item for item in response.json()["detail"])
    assert str(data["password"]) not in response.text


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Basic invalid"}, {"Authorization": "Bearer invalid"}],
)
def test_authentication_required(client, headers):
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "changes,algorithm",
    [
        ({"exp": None}, "HS256"),
        ({"sub": None}, "HS256"),
        ({"iat": None}, "HS256"),
        ({"exp": 0}, "HS256"),
        ({"sub": "0"}, "HS256"),
        ({"sub": "-1"}, "HS256"),
        ({"sub": "abc"}, "HS256"),
        ({"sub": "9999999999999999999999"}, "HS256"),
        ({}, "HS384"),
        ({"exp": "9999999999"}, "HS256"),
        ({"exp": []}, "HS256"),
        ({"iat": {}}, "HS256"),
    ],
)
def test_invalid_jwt_claims(client, settings, changes, algorithm):
    now = datetime.now(UTC)
    claims = {"sub": "1", "iat": now, "exp": now + timedelta(minutes=1)} | changes
    claims = {key: value for key, value in claims.items() if value is not None}
    token = jwt.encode(
        claims, settings.jwt_secret.get_secret_value(), algorithm=algorithm
    )
    assert (
        client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 401
    )


def test_deleted_user_is_rejected(client):
    client.post("/api/v1/auth/register", json=credentials())
    token = client.post("/api/v1/auth/login", json=credentials()).json()["access_token"]
    with client.app.state.database.session() as session:
        session.execute(delete(UserModel))
        session.commit()
    assert (
        client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 401
    )


@pytest.mark.parametrize(
    "algorithm,secret", [("HS256", "other-test-secret-" * 4), ("none", None)]
)
def test_unsigned_or_wrong_signature_tokens_are_rejected(client, algorithm, secret):
    client.post("/api/v1/auth/register", json=credentials())
    now = datetime.now(UTC)
    token = jwt.encode(
        {"sub": "1", "iat": now, "exp": now + timedelta(minutes=1)},
        secret,
        algorithm=algorithm,
    )
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_profile_changes_and_password_require_current_secret(client):
    data = credentials()
    user = client.post("/api/v1/auth/register", json=data | {"name": " Rafael "}).json()
    assert user["name"] == "Rafael"
    token = client.post("/api/v1/auth/login", json=data).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    updated = client.patch(
        "/api/v1/auth/me",
        headers=headers,
        json={"name": "Rafa", "email": " NOVO@example.com "},
    )
    assert updated.status_code == 200
    assert updated.json()["email"] == "novo@example.com"
    assert updated.json()["created_at"] == user["created_at"]
    payload = {"current_password": "incorreta", "password": "Nova-senha-123"}
    assert (
        client.post(
            "/api/v1/auth/change-password", headers=headers, json=payload
        ).status_code
        == 403
    )
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    assert (
        client.post(
            "/api/v1/auth/change-password",
            headers=headers,
            json=payload | {"current_password": data["password"]},
        ).status_code
        == 204
    )
    assert (
        client.post(
            "/api/v1/auth/login", json=credentials("novo@example.com")
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login", json=credentials("novo@example.com", "Nova-senha-123")
        ).status_code
        == 200
    )
    assert "password" not in client.get("/api/v1/auth/me", headers=headers).text


def test_profile_duplicate_email_rolls_back(client):
    client.post("/api/v1/auth/register", json=credentials())
    client.post("/api/v1/auth/register", json=credentials("other@example.com"))
    token = client.post("/api/v1/auth/login", json=credentials()).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert (
        client.patch(
            "/api/v1/auth/me", headers=headers, json={"email": "other@example.com"}
        ).status_code
        == 409
    )
    assert (
        client.get("/api/v1/auth/me", headers=headers).json()["email"]
        == "rafael@example.com"
    )
