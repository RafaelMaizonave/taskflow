import pytest

from app.infrastructure.config import Settings


@pytest.fixture
def settings(tmp_path):
    return Settings(
        _env_file=None,
        jwt_secret="test-only-secret-" * 4,
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        cors_origins=["http://localhost:5173"],
        auth_rate_limit=10_000,
        auth_rate_window_seconds=60,
    )
