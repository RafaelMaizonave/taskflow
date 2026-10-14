# TaskFlow

Aplicação de gerenciamento de tarefas planejada com FastAPI e Vue 3. Este primeiro commit entrega **somente a estrutura e ferramentas**; autenticação, API e CRUD ainda não foram implementados.

## Stack e arquitetura

Python 3.12, FastAPI, SQLAlchemy 2, SQLite, Pydantic 2, PyJWT e Argon2. Frontend com Vue 3, TypeScript, Vite, Pinia, Vue Router, Axios e Tailwind CSS.

Backend em camadas: routers definem HTTP; services coordenam regras e transações; repositories concentram consultas; models e schemas separam persistência e contratos. Veja [o plano e as issues](docs/PLAN.md).

```text
backend/app/{routers,services,repositories,models,schemas}
backend/tests/
frontend/src/{api,components,router,stores,types,views}
.github/workflows/ci.yml
docs/issues/
```

## Pré-requisitos

- Python 3.12 e uv (validado com uv 0.12.23).
- Node.js 24 e npm 11.
- Git.

## Instalação e qualidade

Na raiz do repositório:

```bash
cd backend
uv sync --locked
uv run ruff check .
uv run ruff format --check .
cd ../frontend
npm ci
npm run lint
npm run build
npm run dev
```

O frontend inicial exibe uma página informativa na porta 5173. O backend ainda não possui servidor implementado. Não há suíte de testes nesta etapa: `pytest` será habilitado no CI junto com os testes de integração, evitando tratar uma execução sem testes como sucesso.

## Variáveis de ambiente

`backend/.env.example` documenta DATABASE_URL, JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES e CORS_ORIGINS. O segredo está vazio de propósito; gere um valor forte localmente quando a autenticação for implementada. Nunca versione `.env`. A aplicação futura deverá rejeitar configuração sem segredo.

`frontend/.env.example` define VITE_API_BASE_URL. Variáveis VITE são públicas e nunca devem conter segredos. As configurações de backend ainda não são consumidas nesta etapa.

## Entregas seguintes

API em `/api/v1/auth` e `/api/v1/tasks`, health em `/health`, Swagger em `/docs`, testes com banco isolado, dashboard e Docker Compose serão implementados conforme o plano. A execução com Docker ainda não está disponível.

O token será mantido em memória: recarregar a página exigirá novo login. Logout local não revoga um JWT já emitido. Para produção, avaliar cookies HttpOnly/Secure, proteção CSRF, rotação e revogação de tokens, rate limiting, recuperação de senha, migrações de banco e observabilidade.
