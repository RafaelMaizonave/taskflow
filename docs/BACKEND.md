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
| POST | `/api/v1/auth/register` | 201 com `id` e `email`; 409 para e-mail duplicado |
| POST | `/api/v1/auth/login` | 200 com `access_token`, `token_type` e `expires_in` em segundos |
| GET | `/api/v1/auth/me` | 200 com `id` e `email`; requer Bearer |

Cadastro e login recebem JSON:

```json
{
  "email": "pessoa@example.com",
  "password": "senha-local-de-exemplo"
}
```

A senha deve ter de 8 a 128 caracteres; campos adicionais são rejeitados com 422. E-mails são normalizados e a unicidade é garantida pelo SQLite, inclusive quando duas requisições tentam cadastrar o mesmo endereço. A senha é armazenada exclusivamente como hash Argon2; o hash não faz parte das respostas públicas.

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
  "status": "pending"
}
```

- Título: obrigatório, de 1 a 200 caracteres após remover espaços nas extremidades.
- Descrição: opcional na criação, padrão vazio, máximo de 10.000 caracteres.
- Status: `pending`, `in_progress` ou `completed`; padrão `pending`.
- `id`, `user_id` e `data_criacao` são definidos pelo servidor e não são aceitos na entrada.
- `PATCH` altera apenas os campos enviados. Objeto vazio e valores nulos são rejeitados com 422; descrição vazia é permitida.
- A resposta inclui `id`, `titulo`, `descricao`, `status`, `data_criacao` em UTC e `user_id`.

Filtros podem ser combinados:

```text
GET /api/v1/tasks?status=in_progress&q=documenta
```

`q` faz busca literal por trecho do título: `%` e `_` não são tratados como curingas. A comparação sem distinção de caixa segue o `lower()` nativo do SQLite, que tem limitações para letras fora de ASCII. A ordenação é por criação decrescente, com ID como desempate. Paginação não faz parte deste incremento.

## Isolamento entre usuários

A consulta de tarefas inclui ID e proprietário. Listagem, consulta, atualização e exclusão ficam restritas ao usuário do token. Uma tarefa de outro usuário responde 404, da mesma forma que uma inexistente; não há distinção que revele sua existência.

## Validação manual no Swagger

1. Inicie os serviços conforme o README e acesse `http://localhost:8000/docs`.
2. Cadastre um usuário com `POST /api/v1/auth/register`.
3. Faça login e copie somente o valor de `access_token`.
4. Clique em **Authorize**, informe o token no esquema Bearer e confirme.
5. Execute `/auth/me`, crie uma tarefa, liste, filtre, atualize e exclua.
6. Cadastre e faça login com um segundo usuário. Tente consultar ou alterar uma tarefa ainda existente do primeiro usuário: deve retornar 404.

O frontend agora disponibiliza cadastro, login e dashboard para exercitar os mesmos endpoints, conforme as issues #6 e #7. Não há logout no backend, refresh token ou revogação de JWT nesta versão.

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

Ainda são necessários, para uma implantação de produção, rate limiting, recuperação de senha, política de revogação/renovação de tokens e migrações de esquema. `create_all` não atualiza tabelas existentes. O build Docker deste ambiente teve bloqueio de DNS; a configuração não deve ser confundida com execução validada em contêiner.

Resultado local desta entrega: 106 testes backend aprovados, além de Ruff e formatação. Frontend: 5 unitários e 6 E2E aprovados, com lint e build. O aviso existente de depreciação Starlette/HTTPX permanece sem falhas. As issues #3, #4, #6 e #7 foram entregues em commits separados em main.
