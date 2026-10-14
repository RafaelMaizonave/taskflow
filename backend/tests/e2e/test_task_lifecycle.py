import os
import secrets
import socket
import subprocess
import sys
import time

import httpx
import pytest


def test_real_server_authenticated_task_lifecycle(tmp_path):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    environment = os.environ.copy()
    environment.update(
        JWT_SECRET=secrets.token_urlsafe(48),
        DATABASE_URL=f"sqlite:///{tmp_path / 'tasks.db'}",
    )
    with (tmp_path / "tasks.log").open("w+") as log:
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
                        pytest.fail(log.read())
                    try:
                        if client.get("/health", timeout=1).status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    if time.monotonic() >= deadline:
                        pytest.fail("Servidor não iniciou")
                    time.sleep(0.1)
                headers = []
                for email in ["owner@example.com", "other@example.com"]:
                    credentials = {"email": email, "password": "Senha-segura-123"}
                    assert (
                        client.post(
                            "/api/v1/auth/register", json=credentials
                        ).status_code
                        == 201
                    )
                    login = client.post("/api/v1/auth/login", json=credentials)
                    assert login.status_code == 200
                    headers.append(
                        {"Authorization": f"Bearer {login.json()['access_token']}"}
                    )
                owner, other = headers
                response = client.post(
                    "/api/v1/tasks",
                    headers=owner,
                    json={"titulo": "Validar entrega", "descricao": "E2E"},
                )
                assert response.status_code == 201
                task = response.json()
                path = f"/api/v1/tasks/{task['id']}"
                assert client.get(path, headers=owner).json() == task
                assert client.get("/api/v1/tasks", headers=other).json() == []
                assert client.get(path, headers=other).status_code == 404
                assert (
                    client.patch(
                        path, headers=other, json={"titulo": "Invadida"}
                    ).status_code
                    == 404
                )
                assert client.delete(path, headers=other).status_code == 404
                updated = client.patch(
                    path, headers=owner, json={"status": "completed"}
                )
                assert updated.status_code == 200
                assert updated.json()["status"] == "completed"
                assert updated.json()["descricao"] == "E2E"
                listed = client.get(
                    "/api/v1/tasks",
                    headers=owner,
                    params={"q": "VALIDAR", "status": "completed"},
                )
                assert len(listed.json()) == 1
                assert client.delete(path, headers=owner).status_code == 204
                assert client.get(path, headers=owner).status_code == 404
                assert client.get("/api/v1/tasks", headers=owner).json() == []
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
