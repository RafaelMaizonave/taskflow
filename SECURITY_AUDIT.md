# Auditoria de Segurança — TaskFlow

| Campo | Valor |
| --- | --- |
| Data | 2026-10-15 (atualizado com remediação P0) |
| Escopo | Repositório completo (`backend/`, `frontend/`, Compose, CI) |
| Referências | OWASP Top 10:2025, OWASP API Security Top 10:2023, OWASP ASVS (orientação) |
| Método | Revisão de código + testes não destrutivos locais (TestClient/pytest) |
| Alterações de código | P0 aplicado: TF-001 (rate limit) e TF-002 (revogação de sessão) |

---

## Resumo executivo

O TaskFlow apresenta uma **base de segurança acima da média para um MVP**: isolamento por proprietário nas tarefas (anti-IDOR), hash Argon2, JWT com algoritmo fixo, cookies `HttpOnly` + `SameSite=strict`, proteção CSRF por header customizado em mutações autenticadas por cookie, schemas Pydantic com `extra="forbid"`, CORS sem curingas e testes de autorização negativos.

O estado geral é **parcialmente conforme**: adequado para desenvolvimento local controlado, **ainda não pronto para exposição pública na internet** sem remediações de autenticação, configuração e observabilidade.

### Principais riscos (após P0)

1. ~~Ausência de rate limiting~~ → **Remediado (TF-001)**.
2. ~~Sessões JWT não revogáveis~~ → **Remediado (TF-002)** via `token_version` / claim `tv`.
3. **Documentação OpenAPI (`/docs`, `/redoc`, `/openapi.json`) exposta** por padrão.
4. **Sem headers de segurança HTTP** e **sem Content-Security-Policy**.
5. **Enumeração de contas** via `409` no registro.
6. **Observabilidade de segurança inexistente** (sem logs/alertas de authz/authn).

### Contagem por severidade

| Severidade | Confirmadas abertas | Remediadas (P0) | Riscos potenciais / preventivos |
| --- | ---: | ---: | ---: |
| Crítica | 0 | 0 | 0 |
| Alta | 0 | 2 | 0 |
| Média | 6 | 0 | 3 |
| Baixa | 3 | 0 | 2 |
| **Total** | **9** | **2** | **5** |

### Controles existentes (validado no código/testes)

- Autorização por `user_id` em todas as operações de tarefa; IDOR responde `404` (não distingue existência).
- Argon2id para senhas; verificação dummy no login de usuário inexistente (mitiga timing).
- JWT HS256 com `algorithms=["HS256"]`, claims obrigatórias `sub`/`exp`/`iat`, rejeição de `alg=none` e assinatura inválida.
- Cookie `taskflow_session`: `HttpOnly`, `SameSite=strict`, `Path=/api/v1`, `Secure` em HTTPS.
- Mutações com sessão por cookie exigem `X-Requested-With: XMLHttpRequest`.
- Mass assignment bloqueado (`extra="forbid"`; `user_id`/`password_hash` rejeitados).
- Busca `q` com `icontains(..., autoescape=True)` (sem curingas SQL/LIKE injetáveis).
- Frontend: sessão em cookie (`withCredentials`), sem token em `localStorage`; sem `v-html`.
- Segredo JWT obrigatório (≥ 32 caracteres), `SecretStr`, `.env` no `.gitignore`.
- Testes de integração cobrem isolamento, JWT inválido, CSRF de cookie e validação.

---

## 1. Reconhecimento da aplicação

### Stack e versões observadas (ambiente local inspecionado)

| Camada | Tecnologia | Versão observada / declaração |
| --- | --- | --- |
| Backend | Python | 3.12 (requerido `>=3.12,<3.13`) |
| API | FastAPI | 0.143.1 (`>=0.115,<1`) |
| Servidor | Uvicorn | 0.54.0 |
| ORM | SQLAlchemy | 2.0.54 |
| Auth crypto | Argon2 (`argon2-cffi`) / PyJWT | 25.1.0 / 2.15.1 |
| Frontend | Vue 3 + Vite + Pinia + Vue Router + Axios | Vue 3.5.x, Vite 7.x |
| Persistência | SQLite | arquivo local / volume Docker |
| CI | GitHub Actions | quality + pytest + Playwright |

### Autenticação e autorização

- **Cadastro/login** em `/api/v1/auth/*`.
- **Sessão browser**: cookie HttpOnly `taskflow_session` + CSRF header em não-GET.
- **Sessão API/Bearer**: `Authorization: Bearer <JWT>` (também retornado no corpo do login).
- **Autorização**: identidade só do token; tarefas sempre filtradas por `user_id` do autenticado. Não há papéis (RBAC); modelo single-tenant por usuário.

### Endpoints

| Superfície | Auth |
| --- | --- |
| `GET /health` | Público |
| `GET /docs`, `/redoc`, `/openapi.json` | Público (padrão FastAPI) |
| `POST /api/v1/auth/register`, `/login` | Público |
| `POST /api/v1/auth/logout` | Cookie + header browser |
| `GET|PATCH /api/v1/auth/me`, `POST /change-password` | Cookie ou Bearer |
| `CRUD /api/v1/tasks` | Cookie ou Bearer |

### Segredos e configuração

- `JWT_SECRET` (obrigatório), `DATABASE_URL`, `CORS_ORIGINS`, `ACCESS_TOKEN_EXPIRE_MINUTES`.
- Compose injeta `JWT_SECRET` do `.env`; CORS fixo para `http://localhost:5173`.
- Nenhum segredo de aplicação embutido no frontend (`VITE_API_BASE_URL` apenas).

### Superfície de ataque e ativos

- Contas (e-mail/senha), JWT de sessão, tarefas (dados pessoais de produtividade), schema OpenAPI, banco SQLite, pipeline CI/dependências.

---

## Matriz OWASP Top 10:2025

| Categoria | Status | Severidade | Evidência | Recomendação |
| --- | --- | --- | --- | --- |
| **A01 Broken Access Control** | Conforme (API) / Parcial (frontend) | Baixa–Média | Isolamento de tarefas validado; redirect pós-login sem allowlist | Manter testes IDOR; validar `redirect` |
| **A02 Security Misconfiguration** | Vulnerável | Média | `/docs` aberto; sem security headers; Compose com Vite `development` | Desabilitar docs em prod; headers; build estático |
| **A03 Software Supply Chain Failures** | Parcial | Média | Lockfiles presentes; CI sem audit; `vitest`/`tinypool` com CVEs | `npm audit`/`pip-audit` no CI; atualizar Vitest |
| **A04 Cryptographic Failures** | Parcial | Média | Argon2 + HS256 OK; JWT sem `iss`/`aud`/`jti`; token no body; `Secure` só se scheme HTTPS | Não devolver Bearer se cookie basta; claims; confiar em proxy TLS |
| **A05 Injection** | Conforme | — | ORM parametrizado; `autoescape` em LIKE; Pydantic | Manter; evitar SQL cru |
| **A06 Insecure Design** | Parcial | Média | Rate limit e revogação aplicados; ainda sem paginação; senha só por tamanho | Paginação; política de senha |
| **A07 Authentication Failures** | Parcial | Média | Rate limit + `token_version`; permanece enumeração 409 | Respostas uniformes no register |
| **A08 Software/Data Integrity Failures** | Parcial | Baixa–Média | Lockfiles + `uv sync --locked`/`npm ci`; sem assinatura de artefatos; sem Dependabot | Pin + scan; integrity no deploy |
| **A09 Logging and Alerting Failures** | Vulnerável | Média | Sem logs de authn/authz; sem request ID | Logging estruturado sem segredos + alertas |
| **A10 Mishandling Exceptional Conditions** | Parcial | Baixa | Handlers de domínio/validação; erros não tratados podem vazar stack via middleware padrão em alguns cenários | Handler global 500 genérico; fail-closed (já predominante) |

### Complemento API Security Top 10:2023 (resumo)

| Item | Avaliação |
| --- | --- |
| API1 BOLA | **Mitigado** (filtro por owner + testes) |
| API2 Broken Authentication | **Parcial** (JWT sólido, sem rate limit/revogação) |
| API3 Broken Object Property Level Auth | **Mitigado** (`extra="forbid"`) |
| API4 Unrestricted Resource Consumption | **Vulnerável** (sem rate limit/paginação) |
| API5 BFLA | N/A (sem papéis admin) |
| API6 Unrestricted Access to Sensitive Business Flows | **Parcial** (register/login abertos sem throttle) |
| API7 SSRF | Não aplicável no escopo atual |
| API8 Security Misconfiguration | **Parcial** (docs/CORS/headers) |
| API9 Improper Inventory Management | **Parcial** (OpenAPI sempre ligado) |
| API10 Unsafe Consumption of APIs | N/A (sem integrações externas) |

---

## Detalhamento dos achados

Legenda de tipo: **C** confirmado · **P** potencial · **R** recomendação preventiva.

---

### TF-001 — Ausência de rate limiting em autenticação

| Campo | Valor |
| --- | --- |
| Tipo | **C** → **Remediado (P0)** |
| OWASP | A07 / A06 · API4/API2 |
| CWE | CWE-307 |
| Severidade | **Alta** (corrigida) |
| Arquivos | `backend/app/infrastructure/rate_limit.py`; `backend/app/presentation/rate_limit.py`; rotas `/login` e `/register`; settings `AUTH_RATE_LIMIT` / `AUTH_RATE_WINDOW_SECONDS` |

**Remediação:** Limiter em memória (janela deslizante) por IP+rota; excesso → `429` + `Retry-After`. Padrão 20 req/60s. Limitação: não compartilhado entre múltiplos workers/processos.

**Testes:** `test_auth_endpoints_are_rate_limited`, `test_sliding_window_blocks_after_limit`.

---

### TF-002 — Logout e troca de senha não revogam JWT

| Campo | Valor |
| --- | --- |
| Tipo | **C** → **Remediado (P0)** |
| OWASP | A07 · API2 |
| CWE | CWE-613 |
| Severidade | **Alta** (corrigida) |
| Arquivos | `token_version` em `User`/`UserModel`; claim JWT `tv`; migração schema v2; `AuthService.revoke_sessions` / `change_password` |

**Remediação:** JWT inclui `tv`; autenticação exige igualdade com `users.token_version`. Logout (sessão válida) e troca de senha incrementam a versão. Troca de senha emite novo token e renova o cookie para manter a sessão atual.

**Testes:** `test_logout_and_password_change_revoke_bearer_tokens`, `test_cookie_session_logout_and_csrf`, `test_token_without_version_claim_is_rejected`.

---

### TF-003 — Documentação OpenAPI exposta

| Campo | Valor |
| --- | --- |
| Tipo | **C** |
| OWASP | A02 · API9 |
| CWE | CWE-200 |
| Severidade | **Média** |
| Arquivos | `backend/app/main.py` (`FastAPI(...)` sem `docs_url=None`); confirmado `GET /docs`/`/redoc`/`/openapi.json` → `200` |

**Impacto:** Facilita reconhecimento da API, schemas e vetores por atacantes externos.

**Correção:** Desabilitar `/docs`, `/redoc` e `/openapi.json` quando `ENV=production` (ou flag explícita); manter só em desenvolvimento.

**Testes:** Com settings de produção, esses caminhos retornam `404`.

---

### TF-004 — Ausência de headers de segurança HTTP

| Campo | Valor |
| --- | --- |
| Tipo | **C** |
| OWASP | A02 |
| CWE | CWE-693 / CWE-1021 |
| Severidade | **Média** |
| Arquivos | `backend/app/main.py`; `frontend/index.html` (sem CSP meta); resposta `/health` sem headers de segurança |

**Evidência:** Resposta local de `/health` sem `Content-Security-Policy`, `X-Frame-Options`/`frame-ancestors`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, `Strict-Transport-Security`.

**Impacto:** Maior impacto de XSS futuro, clickjacking e MIME sniffing.

**Correção:** Middleware (ou reverse proxy) com headers seguros; CSP estrita no frontend servido em produção.

**Testes:** Asserção de presença dos headers em respostas da API e do frontend estático.

---

### TF-005 — Enumeração de e-mails no cadastro

| Campo | Valor |
| --- | --- |
| Tipo | **C** |
| OWASP | A07 |
| CWE | CWE-204 |
| Severidade | **Média** |
| Arquivos | `backend/app/infrastructure/auth.py` (`ConflictError("E-mail já cadastrado")`); `backend/app/presentation/errors.py` → HTTP 409 |

**Evidência:** `POST /register` duplicado → `409` com mensagem explícita. Login já uniformiza falhas (`401` idêntico).

**Impacto:** Descoberta de contas existentes para phishing/credential stuffing.

**Correção:** Resposta uniforme no registro (ex.: `201` genérico ou mensagem “se o e-mail for válido, enviaremos instruções”) **ou** aceitar o trade-off documentado com rate limit agressivo. Preferência UX vs. privacidade deve ser explícita.

**Testes:** Respostas indistinguíveis (timing aproximado + corpo) para e-mail novo vs. existente, se a correção for uniformização.

---

### TF-006 — JWT duplicado no corpo da resposta de login

| Campo | Valor |
| --- | --- |
| Tipo | **C** |
| OWASP | A04 / A07 |
| CWE | CWE-522 (exposição) |
| Severidade | **Média** |
| Arquivos | `backend/app/presentation/auth.py` (`TokenResponse`); `frontend/src/api/auth.ts` / `stores/auth.ts` (não persiste o token, mas o recebe) |

**Evidência:** Login define cookie HttpOnly **e** devolve `access_token` no JSON. Frontend usa cookie (`withCredentials`) e não grava o token — porém o Bearer continua utilizável e capturável em logs de proxy, extensões e XSS que leiam o corpo XHR.

**Impacto:** Amplia a superfície além do cookie HttpOnly.

**Correção:** Para o fluxo browser, retornar apenas metadados (`expires_in`) e cookie; reservar Bearer para clientes API explícitos (ou header separado). Se Bearer for necessário, não espelhar no cookie (um mecanismo só).

**Testes:** Contrato do login browser sem `access_token`; clientes API documentados à parte.

---

### TF-007 — Flag `Secure` do cookie só baseada em `request.url.scheme`

| Campo | Valor |
| --- | --- |
| Tipo | **P** |
| OWASP | A02 / A04 |
| CWE | CWE-614 |
| Severidade | **Média** |
| Arquivos | `backend/app/presentation/session_cookie.py` linhas 23 e 34 |

**Evidência:** `secure=request.url.scheme == "https"`. Em HTTP local, cookie sai sem `Secure` (esperado). Atrás de TLS terminator que não propaga scheme/`X-Forwarded-Proto` corretamente, o cookie pode permanecer sem `Secure` em produção.

**Impacto:** Interceptação do cookie em rede não confiável se o app “achar” que está em HTTP.

**Correção:** Setting explícito `COOKIE_SECURE=true` em produção; ou confiar em proxy headers de forma segura (`TrustedHost` + forwarded config).

**Testes:** Com setting de produção forçado, `Set-Cookie` contém `Secure` mesmo se o TestClient usar `http://`.

---

### TF-008 — Redirect pós-login sem allowlist

| Campo | Valor |
| --- | --- |
| Tipo | **P** |
| OWASP | A01 |
| CWE | CWE-601 |
| Severidade | **Média** |
| Arquivos | `frontend/src/views/AuthView.vue` (~linha 50); `frontend/src/router/index.ts` (~linha 48) |

**Evidência:** `router.push((route.query.redirect as string) || '/app/dashboard')` sem validar que o destino é path relativo interno (ex.: começa com `/` e não com `//`).

**Impacto:** Phishing via open redirect se o roteador/navegador aceitar destino externo ou protocol-relative.

**Correção:** Aceitar apenas paths relativos que comecem com `/` e não com `//`, preferencialmente allowlist (`/app/...`).

**Testes:** Unitário rejeitando `//evil.com`, `https://evil.com`, `javascript:...`.

---

### TF-009 — Falha de logging e alertas de segurança

| Campo | Valor |
| --- | --- |
| Tipo | **C** |
| OWASP | A09 |
| CWE | CWE-778 |
| Severidade | **Média** |
| Arquivos | Árvore `backend/app/` — sem módulo de logging de segurança |

**Evidência:** Não há registro estruturado de login falho/sucedido, 401/403 em recursos, logout, troca de senha ou correlation ID.

**Impacto:** Detecção tardia de abuso; forense limitada.

**Correção:** Logging estruturado (sem senha/token); `X-Request-ID`; métricas de 401/429; alertas básicos.

**Testes:** Em falha de login, logger de teste recebe evento sem campos sensíveis.

---

### TF-010 — Dependências de desenvolvimento com CVEs (Vitest/tinypool)

| Campo | Valor |
| --- | --- |
| Tipo | **C** |
| OWASP | A03 |
| CWE | CWE-1395 |
| Severidade | **Média** (runtime produtivo: **Baixa**; CI/dev: **Média**) |
| Evidência | `npm audit`: tinypool ≤2.1.1 (Critical RCE via prototype pollution); `@vitest/mocker` (Moderate path traversal). Cadeia via `vitest@3.2.7` (devDependency). |

**Impacto:** Risco principal no pipeline CI e máquinas de desenvolvimento, não no bundle de produção Vue.

**Correção:** Atualizar Vitest para linha corrigida; falhar CI em vulnerabilidades high/critical de produção; opcionalmente `npm audit --omit=dev` + scan separado de devDeps.

---

### TF-011 — Compose entrega frontend via Vite `development`

| Campo | Valor |
| --- | --- |
| Tipo | **C** (no desenho atual de execução) |
| OWASP | A02 / A06 |
| CWE | CWE-1188 |
| Severidade | **Média** |
| Arquivos | `frontend/Dockerfile` (target `development`); `docker-compose.yml` |

**Evidência:** Imagem frontend só define estágio de desenvolvimento; Compose usa HMR/`npm run dev` com `--host 0.0.0.0` (portas publicadas em `127.0.0.1` no Compose — mitiga exposição remota no host, mas o modo dev permanece inadequado como “produção”).

**Impacto:** Superfície do Vite dev server, source maps e HMR se o bind/proxy for exposto indevidamente.

**Correção:** Estágio `production` com `npm run build` + nginx/caddy estático; Compose de prod separado do de desenvolvimento.

---

### TF-012 — CI sem varredura de vulnerabilidades de dependências

| Campo | Valor |
| --- | --- |
| Tipo | **R** |
| OWASP | A03 / A08 |
| Severidade | **Média** |
| Arquivos | `.github/workflows/ci.yml` |

**Evidência:** CI roda lint/testes/`uv sync --locked`/`npm ci`, mas não `pip-audit`/`npm audit`/OSV/Dependabot.

**Correção:** Job de audit + Dependabot/Renovate.

---

### TF-013 — Política de senha apenas por comprimento

| Campo | Valor |
| --- | --- |
| Tipo | **R** |
| OWASP | A07 |
| CWE | CWE-521 |
| Severidade | **Baixa** |
| Arquivos | `backend/app/presentation/auth.py` (`min_length=8`) |

**Correção:** Checagem contra lista de senhas vazadas (ex. API local/HIBP k-anonymity) e/ou score de complexidade proporcional ao risco; manter Argon2.

---

### TF-014 — JWT sem `iss`, `aud` e `jti`

| Campo | Valor |
| --- | --- |
| Tipo | **R** |
| OWASP | A04 |
| CWE | CWE-345 |
| Severidade | **Baixa** |
| Arquivos | `backend/app/infrastructure/auth.py` (`JwtTokens.issue` / `subject`) |

**Evidência:** Payload só com `sub`, `iat`, `exp`. Algoritmo está fixo (bom), mas falta binding de audiência/emissor e id para revogação.

**Correção:** Emitir e validar `iss`/`aud`; adicionar `jti` alinhado a TF-002.

---

### TF-015 — Listagem de tarefas sem paginação

| Campo | Valor |
| --- | --- |
| Tipo | **R** |
| OWASP | A06 · API4 |
| CWE | CWE-770 |
| Severidade | **Baixa** |
| Arquivos | `backend/app/presentation/tasks.py`; `SqlAlchemyTaskRepository.list` |

**Impacto:** Usuário (ou conta comprometida) pode gerar respostas grandes e pressionar CPU/memória/SQLite.

**Correção:** Paginação cursor/limit obrigatória com teto.

---

## Itens verificados como adequados (não são achados)

| Controle | Resultado |
| --- | --- |
| IDOR em tarefas | **OK** — usuário B recebe `404` em GET/PATCH/DELETE da tarefa de A |
| Mass assignment | **OK** — `user_id`/`password_hash` → `422` |
| JWT `alg=none` / assinatura errada | **OK** — `401` |
| Login uniforme (usuário inexistente vs senha errada) | **OK** |
| CSRF cookie sem header | **OK** — mutação → `403`; com header → sucesso |
| Injeção LIKE via `q` | **OK** — `%`/`_` literais (`autoescape=True`) |
| XSS via `v-html` | **OK** — não utilizado |
| Segredos no bundle Vite | **OK** — sem segredos `VITE_*` sensíveis |
| CORS `*` | **OK** — rejeitado na validação de settings |
| Hash de senha | **OK** — Argon2; `password_hash` com `repr=False` |

### Não verificado nesta auditoria

- Comportamento completo de open redirect no browser real (marcado como **P**).
- Hardenização de host/OS, WAF, backups cifrados do SQLite, TLS end-to-end em deploy real.
- Varredura CVE completa do lock Python (`pip-audit` indisponível no PATH do ambiente; `uv` quebrado no host — venv aponta para `/usr/local/bin/python3` inexistente).
- Pentest autenticado via UI Playwright além dos testes E2E já existentes.

---

## Plano de remediação

### P0 — Imediato (antes de exposição pública)

1. **TF-001** ~~Rate limiting~~ — **concluído**.
2. **TF-002** ~~Revogação de sessão~~ — **concluído**.

### P1 — Alto

3. **TF-003** Desligar OpenAPI em produção.
4. **TF-006** Eliminar `access_token` do JSON no fluxo browser (ou unificar modelo de sessão).
5. **TF-004** Security headers + CSP no frontend de produção.
6. **TF-009** Logs de segurança sem vazamento de segredos.

### P2 — Importante

7. **TF-005** Mitigar enumeração (ou aceitar + rate limit documentado).
8. **TF-007** `COOKIE_SECURE` explícito / proxy TLS.
9. **TF-008** Allowlist de redirect.
10. **TF-011** Imagem/pipeline de frontend estático para “prod”.
11. **TF-010/TF-012** Atualizar Vitest + audit no CI.

### P3 — Hardening

12. **TF-013** Política de senha / denylist.
13. **TF-014** Claims `iss`/`aud`/`jti`.
14. **TF-015** Paginação.
15. Trusted Host, HSTS no edge, backup/cifra do SQLite, runbook de incidente.

---

## Proposta de testes automatizados (regressão)

```text
1. test_rate_limit_login_returns_429_after_threshold
2. test_logout_revokes_bearer_token
3. test_change_password_revokes_existing_tokens
4. test_openapi_disabled_in_production_settings
5. test_security_headers_present
6. test_login_browser_response_omits_access_token  # se TF-006 adotado
7. test_register_does_not_enumerate_emails          # se TF-005 adotado
8. test_redirect_query_rejects_external_targets      # frontend
9. test_cookie_secure_forced_in_production
10. Manter: test_crud_and_user_isolation, test_session_cookie_logout_and_csrf,
    test_unsigned_or_wrong_signature_tokens_are_rejected
```

---

## Diagnóstico geral

| Pergunta | Resposta |
| --- | --- |
| A autorização por recurso está sólida? | **Sim**, com testes. |
| A autenticação está sólida para internet pública? | **Não ainda** (rate limit + revogação). |
| A configuração está pronta para produção? | **Não** (docs, headers, modo Vite). |
| Injection/XSS estrutural? | **Baixo risco atual**, com boas práticas. |
| Próximo passo | Aprovar plano P0/P1; só então alterar código. |

---

## Próximos passos (aguardando aprovação)

Conforme solicitado, **nenhuma correção de código foi aplicada**. Após sua aprovação, a ordem sugerida de implementação é:

1. P0: rate limiting + revogação de token  
2. P1: docs off, headers, modelo de token no login, logging  
3. P2/P3 conforme prioridade de release  

Indique quais itens autoriza para implementação na próxima etapa.
