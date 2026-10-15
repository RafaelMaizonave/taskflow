# TaskFlow

Aplicação web de gerenciamento de tarefas pessoais: cadastro, login com sessão em cookie HttpOnly, dashboard com resumo real, lista e Kanban, prioridades, tags, prazos, busca, filtros e perfil editável. Cada conta vê apenas as próprias tarefas.

## Tecnologias

| Camada | Stack |
| --- | --- |
| Backend | Python 3.12, FastAPI, SQLAlchemy, SQLite, uv, Pytest, Ruff |
| Frontend | Vue 3, TypeScript, Vite, Pinia, Tailwind CSS, Vitest, Playwright |
| Infra | Docker Compose V2, GitHub Actions |

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) com Compose V2 (Desktop ou Engine)
- Make é opcional — use os scripts em `scripts/` se preferir

Não é necessário instalar Python, Node ou uv no host para o fluxo Docker.

## Como executar

```bash
git clone https://github.com/RafaelMaizonave/taskflow.git
cd taskflow
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

## Acessar a aplicação

| Recurso | URL |
| --- | --- |
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

## Documentação adicional

| Documento | Conteúdo |
| --- | --- |
| [docs/BACKEND.md](docs/BACKEND.md) | Contratos REST e autenticação |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Execução sem Docker, portas, WSL, hot reload |
| [docs/TESTING.md](docs/TESTING.md) | Suítes e CI |
| [docs/PLAN.md](docs/PLAN.md) | Plano e issues |
| [docs/REDESIGN.md](docs/REDESIGN.md) | Interface e migração de dados |

## Decisões técnicas

- Sessão via cookie HttpOnly (SameSite=Strict; Secure em HTTPS); a API também aceita Bearer.
- SQLite em volume Docker nomeado; `stop`/`restart`/`clean` não apagam dados — só `reset` com confirmação.
- Portas vinculadas a `127.0.0.1`; `JWT_SECRET` obrigatório (≥32 caracteres), gerado automaticamente no primeiro `run`.
- SQLAlchemy síncrono; migração SQLite versionada preserva contas e tarefas ao evoluir o esquema.
- Imagens voltadas a desenvolvimento e testes, não a produção. Limitações conhecidas (sem refresh token, rate limiting ou recuperação de senha) estão em [docs/BACKEND.md](docs/BACKEND.md).
