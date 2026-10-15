# TaskFlow

Aplicação web de gerenciamento de tarefas pessoais: cadastro, login com sessão em cookie HttpOnly, dashboard com resumo real, lista e Kanban, prioridades, tags, prazos, busca, filtros e perfil editável. Cada conta vê apenas as próprias tarefas.

Demonstração: https://taskflows.duckdns.org

## Tecnologias

| Camada | Stack |
| --- | --- |
| Backend | Python 3.12, FastAPI, SQLAlchemy, SQLite, uv, Pytest, Ruff |
| Frontend | Vue 3, TypeScript, Vite, Pinia, Tailwind CSS, Vitest, Playwright |
| Infra | Docker Compose V2, GitHub Actions |

## Pré-requisitos

**Com Docker (recomendado):**

- [Docker](https://docs.docker.com/get-docker/) com Compose V2 (Desktop ou Engine)
- Make é opcional — use os scripts em `scripts/` se preferir

Não é necessário instalar Python, Node ou uv no host para o fluxo Docker.

**Sem Docker:**

- Python 3.12 e [uv](https://docs.astral.sh/uv/)
- Node.js 24 e npm 11

## Como executar

```bash
git clone https://github.com/RafaelMaizonave/taskflow.git
cd taskflow
```

### Com Docker

```bash
make run
```

Alternativas sem Make:

```bash
./scripts/dev.sh run
```

```powershell
.\scripts\dev.ps1 run
```

Na primeira execução o ambiente gera `.env` com `JWT_SECRET` seguro (sem exibir o valor), constrói as imagens, sobe os serviços e aguarda os health checks. Execuções seguintes reutilizam cache e **preservam** o banco no volume Docker.

### Sem Docker

Abra dois terminais na raiz do repositório.

**1. Backend**

```bash
cd backend
uv sync --locked
test -e .env || (umask 077; printf 'JWT_SECRET=%s\nCORS_ORIGINS=["http://localhost:5173"]\n' "$(openssl rand -hex 32)" > .env)
uv run uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload
```

**2. Frontend**

```bash
cd frontend
npm ci
npm run dev
```

O Vite encaminha `/api` para `http://127.0.0.1:8000`. O backend usa `backend/.env` (não o `.env` da raiz, que é do Compose). Variáveis opcionais: `backend/.env.example` e `frontend/.env.example`.

Detalhes (portas, WSL, hot reload, testes locais): [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Acessar a aplicação

| Recurso | URL |
| --- | --- |
| Demonstração | https://taskflows.duckdns.org |
| Frontend | http://localhost:5173 |
| Swagger / OpenAPI | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

Não há usuário padrão: crie uma conta pela interface.

## Comandos disponíveis

| Comando | Responsabilidade |
| --- | --- |
| `make help` | Lista os comandos |
| `make setup` | Valida Docker e prepara `.env` |
| `make run` | Prepara e inicia a aplicação |
| `make stop` | Para os serviços (preserva o banco) |
| `make restart` | Reinicia os serviços |
| `make logs` | Acompanha logs (`SERVICE=frontend` opcional) |
| `make ps` | Estado dos contêineres |
| `make test` | Pytest + Vitest + Playwright |
| `make test-backend` | Qualidade e testes do backend |
| `make test-frontend` | Lint, tipos e Vitest |
| `make test-e2e` | Playwright |
| `make test-infra` | Validação isolada do Compose |
| `make lint` | Ruff + ESLint + typecheck |
| `make format` | Formata backend e frontend |
| `make build` | Constrói imagens |
| `make check` | Lint, testes e build do frontend |
| `make clean` | Remove contêineres sem apagar o volume |
| `make reset` | Apaga contêineres e o volume do banco (pede confirmação) |

Os mesmos nomes funcionam em `./scripts/dev.sh` e `.\scripts\dev.ps1`.

## Testes

```bash
make test      # suíte completa
make check     # qualidade + testes + build (validação de entrega)
make test-infra
```

Detalhes: [docs/TESTING.md](docs/TESTING.md).

## Arquitetura

```text
backend/app/
├── domain/          # Entidades e regras
├── application/     # Casos de uso e ports (Protocol)
├── infrastructure/  # SQLite, Argon2, JWT, Settings
└── presentation/    # HTTP, schemas Pydantic
frontend/src/        # Vue 3 (api, components, router, stores, views)
```

Clean Architecture no backend: domínio e casos de uso não importam FastAPI nem SQLAlchemy. O frontend usa Composition API, Router e Pinia; o Vite faz proxy de `/api` para o backend.
