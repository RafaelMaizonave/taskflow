import os
import secrets
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

backend = Path(__file__).resolve().parents[2] / "backend"


def stop(_signal, _frame):
    raise SystemExit(0)


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
with tempfile.TemporaryDirectory(prefix="taskflow-browser-") as directory:
    environment = os.environ.copy()
    environment.update(
        JWT_SECRET=secrets.token_urlsafe(48),
        DATABASE_URL=f"sqlite:///{directory}/browser.db",
        CORS_ORIGINS="[]",
        # Desktop e mobile rodam em paralelo no mesmo IP. O limite de
        # produção (20/min por rota) responde 429 e impede o login.
        AUTH_RATE_LIMIT="10000",
    )
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
            "18765",
        ],
        cwd=backend,
        env=environment,
    )
    try:
        raise SystemExit(process.wait())
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
