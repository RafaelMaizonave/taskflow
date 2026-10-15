"""Valida o Compose com projeto, portas e volume descartáveis."""

import json
import os
import secrets
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    environment = os.environ | {
        "JWT_SECRET": secrets.token_urlsafe(48),
        "BACKEND_PORT": "0",
        "FRONTEND_PORT": "0",
    }
    project = f"taskflow-validation-{secrets.token_hex(6)}"

    def compose(*args: str) -> str:
        return subprocess.run(
            ["docker", "compose", "--project-name", project, *args],
            cwd=ROOT,
            env=environment,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()

    def endpoint(service: str, port: int) -> str:
        return f"http://{compose('port', service, str(port))}"

    def request(
        base: str,
        path: str,
        method: str = "GET",
        data: dict | None = None,
        token: str | None = None,
    ):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        body = json.dumps(data).encode() if data is not None else None
        with urlopen(
            Request(base + path, data=body, headers=headers, method=method), timeout=10
        ) as response:
            payload = response.read()
            return json.loads(payload) if payload else None

    try:
        compose("config", "--quiet")
        compose("up", "--build", "--detach", "--wait")
        backend = endpoint("backend", 8000)
        frontend = endpoint("frontend", 5173)
        for url in [backend + "/docs", frontend]:
            with urlopen(url, timeout=10) as response:
                assert response.status == 200, url
        credentials = {"email": "compose@example.com", "password": "Senha-segura-123"}
        request(backend, "/api/v1/auth/register", "POST", credentials)
        token = request(backend, "/api/v1/auth/login", "POST", credentials)[
            "access_token"
        ]
        task = request(
            backend,
            "/api/v1/tasks",
            "POST",
            {"titulo": "Persistir após recriação"},
            token,
        )
        assert request(frontend, "/api/v1/tasks", token=token) == [task]
        compose("up", "--detach", "--wait", "--force-recreate", "backend")
        backend = endpoint("backend", 8000)
        token = request(backend, "/api/v1/auth/login", "POST", credentials)[
            "access_token"
        ]
        assert request(backend, f"/api/v1/tasks/{task['id']}", token=token) == task
        print("Compose: serviços, Swagger, proxy e persistência aprovados.")
    finally:
        compose("down", "--volumes", "--remove-orphans")


if __name__ == "__main__":
    main()
