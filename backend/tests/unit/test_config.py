import pytest
from pydantic import ValidationError

from app.infrastructure.config import Settings

SECRET = "test-only-secret-" * 4


def test_secret_is_required(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize("secret", ["", "short", " " * 40])
def test_rejects_weak_secret(secret):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, jwt_secret=secret)


def test_secret_is_redacted():
    settings = Settings(_env_file=None, jwt_secret=SECRET)
    assert SECRET not in repr(settings)
    assert SECRET not in settings.model_dump_json()


@pytest.mark.parametrize(
    "origin",
    [
        "*",
        "https://*.example.com",
        "ftp://host",
        "https://host/path",
        "https://user:pass@host",
        "https://host:wrong",
    ],
)
def test_rejects_invalid_cors_origins(origin):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, jwt_secret=SECRET, cors_origins=[origin])


def test_default_cors_does_not_allow_any_origin(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert Settings(_env_file=None, jwt_secret=SECRET).cors_origins == []


@pytest.mark.parametrize("value", [0, -1, 1441])
def test_rejects_invalid_token_lifetime(value):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, jwt_secret=SECRET, access_token_expire_minutes=value)


@pytest.mark.parametrize(
    "url", ["postgresql://localhost/db", "sqlite://", "sqlite:///db?mode=ro"]
)
def test_rejects_unsupported_database(url):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, jwt_secret=SECRET, database_url=url)
