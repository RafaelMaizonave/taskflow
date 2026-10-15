import os
import secrets
import socket
import subprocess
import sys
import time

import httpx


def test_auth_flow_survives_server_restart(tmp_path):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    environment = os.environ.copy()
    environment.update(
        JWT_SECRET=secrets.token_urlsafe(48),
        DATABASE_URL=f"sqlite:///{tmp_path / 'e2e.db'}",
        CORS_ORIGINS='["http://localhost:5173"]',
    )
    for _ in range(2):
        with (tmp_path / "server.log").open("w+") as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "app.main:create_app",
                    "--factory",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                ],
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            try:
                with httpx.Client(
                    base_url=f"http://127.0.0.1:{port}", trust_env=False
                ) as client:
                    deadline = time.monotonic() + 15
                    while True:
                        if process.poll() is not None:
                            log.seek(0)
                            raise AssertionError(log.read())
                        try:
                            response = client.get("/health", timeout=1)
                            break
                        except httpx.TransportError:
                            if time.monotonic() >= deadline:
                                raise AssertionError("Servidor não iniciou") from None
                            time.sleep(0.1)
                    assert response.status_code == 200
                    payload = {
                        "email": "e2e@example.com",
                        "password": "e2e-password-123",
                    }
                    if _ == 0:
                        assert (
                            client.post(
                                "/api/v1/auth/register", json=payload
                            ).status_code
                            == 201
                        )
                    else:
                        assert (
                            client.post(
                                "/api/v1/auth/register", json=payload
                            ).status_code
                            == 409
                        )
                    login = client.post("/api/v1/auth/login", json=payload)
                    assert login.status_code == 200
                    headers = {
                        "Authorization": f"Bearer {login.json()['access_token']}"
                    }
                    assert (
                        client.get("/api/v1/auth/me", headers=headers).json().items()
                        >= {
                            "id": 1,
                            "email": "e2e@example.com",
                        }.items()
                    )
                    assert client.get("/api/v1/auth/me").status_code == 200
                    assert (
                        client.post(
                            "/api/v1/auth/logout",
                            headers={"X-Requested-With": "XMLHttpRequest"},
                        ).status_code
                        == 204
                    )
                    assert client.get("/api/v1/auth/me").status_code == 401
                assert (tmp_path / "e2e.db").exists()
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
