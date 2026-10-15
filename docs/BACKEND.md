# API: autenticação e tarefas

## Responsabilidades e direção das dependências

- `domain`: usuário e tarefa como dataclasses, status como Enum e erros de negócio. Não importa FastAPI, Pydantic ou SQLAlchemy.
- `application`: serviços de autenticação e tarefas e contratos `Protocol`. Coordena autorização e transações, sem conhecer HTTP ou o engine.
- `infrastructure`: implementações SQLAlchemy, Argon2 e JWT. Converte models persistidos em entidades do domínio.
- `presentation`: valida entrada com Pydantic, obtém dependências e traduz erros para HTTP. O usuário autenticado vem do token, nunca do JSON da tarefa.
- `main.py`: compõe a aplicação, registra routers/handlers e inicializa/libera o banco no ciclo de vida.

Os contratos existem para separar regras de negócio de mecanismos externos que precisam ser substituídos nos testes. Não há repository genérico, service locator ou container externo. Os serviços controlam commit/rollback usando os métodos explícitos do repository; a sessão continua limitada à requisição.

## Autenticação

| Método | Endpoint | Resultado |
| --- | --- | --- |
| POST | `/api/v1/auth/register` | 201 com `id`, `email`, `name` e `created_at`; 409 para e-mail duplicado |
| POST | `/api/v1/auth/login` | 200 com `access_token`, `token_type` e `expires_in` em segundos; emite cookie HttpOnly |
| POST | `/api/v1/auth/logout` | 204; remove o cookie de sessão |
| GET | `/api/v1/auth/me` | 200 com `id`, `email`, `name` e `created_at`; requer cookie de sessão ou Bearer |
| PATCH | `/api/v1/auth/me` | Atualiza `name` e/ou `email`; 409 para e-mail duplicado |
| POST | `/api/v1/auth/change-password` | 204 sem corpo; 403 quando a senha atual estiver incorreta |

Cadastro e login recebem JSON:

```json
{
  "email": "pessoa@example.com",
  "password": "senha-local-de-exemplo"
}
```

O cadastro aceita também `name`, opcional, com até 100 caracteres; na ausência, o nome fica vazio. O login recebe somente e-mail e senha. A senha deve ter de 8 a 128 caracteres; campos adicionais são rejeitados com 422. E-mails são normalizados e a unicidade é garantida pelo SQLite, inclusive quando duas requisições tentam cadastrar o mesmo endereço. A senha é armazenada exclusivamente como hash Argon2; o hash não faz parte das respostas públicas.

O perfil aceita `name` de 1 a 100 caracteres após remover espaços e/ou `email` válido. Objeto vazio e campos nulos são rejeitados. `created_at` registra a criação de contas novas; contas anteriores à migração retornam `null`, pois essa data não era armazenada.

A troca de senha recebe `{"current_password": "senha-atual", "password": "nova-senha"}` e exige cookie de sessão ou Bearer. Senha atual incorreta retorna 403 sem encerrar a sessão; ausência ou invalidade do token continua retornando 401. A alteração não revoga JWTs já emitidos.

Tokens usam HS256 com segredo externo, `sub` como ID textual e datas `iat`/`exp`. A validação exige assinatura, algoritmo e claims válidas e verifica que o usuário ainda existe. Login com usuário desconhecido também executa verificação Argon2 para reduzir diferenças de tempo observáveis. Isso não substitui rate limiting.

A aplicação retorna 401 com `WWW-Authenticate: Bearer` quando a autenticação falha. Erros de validação retornam 422 sem ecoar os valores recebidos, evitando expor senhas ou tokens na resposta.

## Tarefas

Todas as rotas requerem:

```text
Authorization: Bearer <access_token>
```

| Método | Endpoint | Resultado |
| --- | --- | --- |
| POST | `/api/v1/tasks` | 201 com a tarefa criada |
| GET | `/api/v1/tasks` | 200 com lista de tarefas do usuário |
| GET | `/api/v1/tasks/{id}` | 200 com a tarefa ou 404 |
| PATCH | `/api/v1/tasks/{id}` | 200 com a tarefa atualizada ou 404 |
| DELETE | `/api/v1/tasks/{id}` | 204 sem corpo ou 404 |

Exemplo de criação:

```json
{
  "titulo": "Revisar documentação",
  "descricao": "Conferir os comandos de execução local",
  "status": "backlog",
  "priority": "high",
  "due_date": "2026-11-01",
  "tags": ["documentação"]
}
```

- Título: obrigatório, de 1 a 200 caracteres após remover espaços nas extremidades.
- Descrição: opcional na criação, padrão vazio, máximo de 10.000 caracteres.
- Status: `backlog`, `in_progress` ou `done`; padrão `backlog`.
- Prioridade (`priority`): `low`, `medium` ou `high`; padrão `medium`.
- Prazo (`due_date`): data ISO `YYYY-MM-DD` ou `null`; padrão `null`.
- Tags (`tags`): até 10 textos de 1 a 40 caracteres após remover espaços; duplicatas são removidas mantendo a ordem. Padrão: lista vazia.
- Posição (`position`): inteiro de 0 a 2³¹ − 1. Quando omitida na criação, recebe a posição seguinte na coluna daquele usuário; o `PATCH` persiste a posição enviada.
- `id`, `user_id` e `data_criacao` são definidos pelo servidor e não são aceitos na entrada.
- `PATCH` altera apenas os campos enviados. Objeto vazio e valores nulos são rejeitados com 422, exceto `due_date: null`, que remove o prazo. Descrição e lista de tags vazias são permitidas.
- A resposta inclui `id`, `titulo`, `descricao`, `status`, `data_criacao` em UTC, `user_id`, `priority`, `due_date`, `tags`, `position`, `updated_at` e `completed_at`.
- `updated_at` acompanha alterações. Ao entrar em `done`, a aplicação registra `completed_at`; ao reabrir, limpa essa data. Edições de uma tarefa que continua concluída preservam sua data de conclusão. Esses timestamps são definidos pelo servidor.

Filtros podem ser combinados:

```text
GET /api/v1/tasks?status=in_progress&q=documenta
```

`q` faz busca literal por trecho do título ou descrição: `%` e `_` não são tratados como curingas. A comparação sem distinção de caixa segue o `lower()` nativo do SQLite, que tem limitações para letras fora de ASCII. A ordenação é por `position` crescente, com ID decrescente como desempate. Paginação não faz parte deste incremento.

## Isolamento entre usuários

A consulta de tarefas inclui ID e proprietário. Listagem, consulta, atualização e exclusão ficam restritas ao usuário do token. Uma tarefa de outro usuário responde 404, da mesma forma que uma inexistente; não há distinção que revele sua existência.

## Validação manual no Swagger

1. Inicie os serviços conforme o README e acesse `http://localhost:8000/docs`.
2. Cadastre um usuário com `POST /api/v1/auth/register`.
3. Faça login e copie somente o valor de `access_token`.
4. Clique em **Authorize**, informe o token no esquema Bearer e confirme.
5. Execute `/auth/me`, crie uma tarefa, liste, filtre, atualize e exclua.
6. Cadastre e faça login com um segundo usuário. Tente consultar ou alterar uma tarefa ainda existente do primeiro usuário: deve retornar 404.

O frontend disponibiliza cadastro, login, dashboard, lista/Kanban e perfil para exercitar os mesmos endpoints. Logout remove o cookie HttpOnly. Não há refresh token nem revogação de JWT já emitido nesta versão.

## Migração do banco

Na inicialização, `infrastructure/database/migrations.py` verifica `PRAGMA user_version`. Bancos novos recebem o esquema atual; bancos legados sem versão são migrados para a versão 1 em transação SQLite explícita. A tabela de tarefas é reconstruída para substituir a restrição dos status: `pending` vira `backlog`, `completed` vira `done` e `in_progress` permanece.

A migração preserva IDs, proprietários, títulos, descrições, datas de criação, e-mails e hashes. Inicializa prioridade como `medium`, tags vazias, prazo nulo e posições determinísticas por usuário e coluna. `updated_at` começa com `data_criacao`, único marco temporal disponível; `completed_at` legado e `created_at` de usuários legados ficam nulos, sem inventar datas históricas. A execução é idempotente; uma falha reverte alterações de esquema e dados. Versões futuras e esquemas intermediários não reconhecidos são recusados.

## Testes e limites

Execute em `backend`:

```bash
uv run pytest tests/unit -q
uv run pytest tests/integration -q
uv run pytest tests/e2e -q
uv run ruff check .
uv run ruff format --check .
```

Os testes usam SQLite temporário, separado do banco de desenvolvimento. Integração cobre os endpoints e a persistência reais; E2E inicia Uvicorn como processo e usa HTTP real. O frontend mantém seus próprios testes unitários e E2E em navegador.

Ainda são necessários, para uma implantação de produção, rate limiting, recuperação de senha e política de revogação/renovação de tokens. Não há paginação nesta versão.

Os testes cobrem também migração com preservação dos dados, idempotência e rollback em falha, campos novos das tarefas, transições de conclusão, edição de perfil e troca de senha. O aviso de depreciação Starlette/HTTPX permanece sem falhas. A validação desta entrega usa a imagem Docker `taskflow-backend-quality`; o E2E navegável pertence à suíte do frontend.

## Sessão do navegador

O cookie `taskflow_session` tem path `/api/v1`, HttpOnly, SameSite=Strict, Secure quando a requisição usa HTTPS e Max-Age igual à duração do JWT. Login e leitura de sessão usam Cache-Control=no-store. A API mantém suporte a Bearer, com precedência sobre cookie quando Authorization estiver presente. Operações autenticadas por cookie que alteram dados, incluindo logout, exigem X-Requested-With: XMLHttpRequest; a política CORS permite esse cabeçalho e credenciais apenas para origens explicitamente configuradas. O frontend usa o proxy de mesma origem no desenvolvimento.
