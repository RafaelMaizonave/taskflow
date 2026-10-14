import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import create_app


@pytest.fixture
def client(settings):
    app = create_app(settings)
    with TestClient(app) as client:
        yield client


def test_health_and_openapi(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "/health" in client.get("/openapi.json").json()["paths"]
    assert client.get("/docs").status_code == 200


@pytest.mark.parametrize(
    "origin, allowed",
    [
        ("http://localhost:5173", True),
        ("https://untrusted.example", False),
    ],
)
def test_cors_preflight(client, origin, allowed):
    response = client.options(
        "/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    assert response.status_code == (200 if allowed else 400)
    assert response.headers.get("access-control-allow-origin") == (
        origin if allowed else None
    )


def test_health_reports_database_unavailable(client):
    from app.presentation.dependencies import get_session

    def broken_session():
        session = Session(close_resets_only=False)
        session.close()
        yield session

    client.app.dependency_overrides[get_session] = broken_session
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"detail": "Banco indisponível"}
