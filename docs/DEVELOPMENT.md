# Desenvolvimento avançado

Fluxo recomendado: Docker via `make` ou `scripts/dev.sh` / `scripts/dev.ps1` (veja o README). Este documento cobre execução sem Docker, portas, segredos e detalhes de infraestrutura.

## Pré-requisitos sem Docker

- Python 3.12 e [uv](https://docs.astral.sh/uv/) (validado com 0.12.23)
- Node.js 24 e npm 11
- Para E2E local: Chromium do Playwright (`npx playwright install --with-deps chromium`)

## Backend manual

```bash
cd backend
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
# Somente se backend/.env ainda não existir:
test -e .env || (umask 077; printf 'JWT_SECRET=%s\nCORS_ORIGINS=["http://localhost:5173"]\n' "$(openssl rand -hex 32)" > .env)
uv run uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload
```

O backend lê `backend/.env`. O Compose lê `.env` na raiz. São contratos distintos; não misture os arquivos.

## Frontend manual

```bash
cd frontend
npm ci
npm run lint
npm run typecheck
npm run test:unit
npm run test:e2e
npm run dev
```

`VITE_API_BASE_URL` (padrão `/api/v1`) está documentado em `frontend/.env.example`. O Vite encaminha `/api` para o backend: no Compose, `API_PROXY_TARGET=http://backend:8000`; na execução manual, o padrão é `http://127.0.0.1:8000`. `API_PROXY_TARGET` vem do processo que inicia o Vite, não do arquivo `.env`. Variáveis `VITE_*` são públicas e não devem conter segredos.

Se houver Chromium do sistema:

```bash
PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/chromium npm run test:e2e
```

A instalação de dependências Linux do navegador pode solicitar privilégios administrativos.

## Configuração e segurança

| Contexto | Arquivo | Conteúdo típico |
| --- | --- | --- |
| Docker Compose | `.env` (raiz) | `JWT_SECRET` (obrigatório, ≥32 caracteres); `BACKEND_PORT` / `FRONTEND_PORT` opcionais |
| Execução manual do backend | `backend/.env` | Ver `backend/.env.example` |
| Frontend | `frontend/.env` (opcional) | Ver `frontend/.env.example` |

`make setup` / `make run` geram `.env` na raiz sem exibir o segredo e sem sobrescrever um arquivo existente. Nunca versione `.env`.

Não execute `docker compose config` sem `--quiet` ao compartilhar logs: a saída resolvida pode conter segredos.

## Portas e CORS

As portas são publicadas apenas em `127.0.0.1`. Padrões: backend `8000`, frontend `5173`.

Ao alterar `FRONTEND_PORT`, o Compose ajusta `CORS_ORIGINS` para `http://localhost:<porta>`. O proxy do Vite usa a mesma origem do frontend; CORS importa sobretudo para acesso direto à API.

## Persistência

O SQLite fica no volume nomeado `taskflow-data` (`/app/data/taskflow.db` no contêiner).

| Comando | Volume do banco |
| --- | --- |
| `make stop` / `make restart` / `make clean` | Preservado |
| `make reset` (com confirmação) | Apagado |

Nunca use `docker compose down -v` em fluxos comuns.

## Hot reload

- Frontend: `frontend/src` montado no contêiner; alterações no código acionam o Vite.
- Backend: `backend/app` montado com Uvicorn `--reload`.
- Mudanças em dependências (`package.json`, `uv.lock`) ou Dockerfiles exigem `make build` ou `make run` novamente.

## Serviços de ferramenta no Compose

| Serviço | Profile | Uso |
| --- | --- | --- |
| `backend-quality` | `tools` | Ruff e Pytest |
| `e2e` | `tests` | Playwright com Chromium |

Ativados sob demanda pelos alvos `make test*` / `make lint`; não ficam em execução com o frontend.

## Validação de infraestrutura

```bash
make test-infra
# ou, com Python 3.12 e Docker no host:
python3 scripts/validate_compose.py
```

Cria projeto Compose exclusivo, portas livres e volume descartável; verifica frontend, Swagger, proxy e persistência; remove tudo ao terminar. Não usa o banco de desenvolvimento.

## Windows e WSL

Com Docker Desktop no Windows, use PowerShell:

```powershell
.\scripts\dev.ps1 run
```

No WSL2, prefira o filesystem Linux do projeto (não `/mnt/c/...`) e `./scripts/dev.sh` ou `make`. Habilite a integração WSL da distribuição em uso nas configurações do Docker Desktop. Não instale um segundo daemon Docker dentro do WSL se o Desktop já estiver integrado.

## Imagens

Os Dockerfiles usam lockfiles (`uv.lock`, `package-lock.json`). `.dockerignore` exclui segredos e dependências do host. As imagens atendem a desenvolvimento e testes; não representam implantação de produção.
