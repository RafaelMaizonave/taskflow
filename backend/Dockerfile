FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked
COPY . .
CMD ["uv", "run", "ruff", "check", "."]
