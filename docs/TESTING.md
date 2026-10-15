# Testes e verificações

Comandos resumidos (requerem Docker):

| Comando | O que executa |
| --- | --- |
| `make test` | Backend + frontend unitário + E2E |
| `make test-backend` | Ruff check/format --check + Pytest |
| `make test-frontend` | ESLint + typecheck + Vitest |
| `make test-e2e` | Playwright (imagem `e2e`) |
| `make test-infra` | `scripts/validate_compose.py` via container |
| `make lint` | Ruff + ESLint + typecheck |
| `make check` | Lint + Pytest + Vitest + build frontend + E2E |

Todos retornam código de saída diferente de zero em falha e identificam a etapa. Usam contêineres temporários (`--rm`) e não alteram o volume `taskflow-data` de desenvolvimento.

## Escopo dos testes

- **Backend (Pytest + HTTPX):** configuração, SQLite, sessões, health, CORS, autenticação, CRUD, filtros, isolamento entre usuários e servidores Uvicorn reais.
- **Frontend (Vitest):** sessão, estado/filtros/resumo e formulário de tarefas.
- **E2E (Playwright):** aplicação compilada em Chromium desktop/mobile — cadastro, login, CRUD, filtros, Kanban, perfil, senha, logout, persistência da sessão e isolamento entre contas. Emulação mobile não substitui aparelho físico.
- **Infra:** sobe um projeto Compose isolado, valida proxy/Swagger/persistência e remove volume/contêineres ao final.

## CI

O workflow em `.github/workflows/ci.yml` executa qualidade backend, qualidade frontend (inclui E2E) e validação Compose. Confira o status atual no GitHub após cada push.
