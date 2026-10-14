# TaskFlow

Aplicação de gerenciamento de tarefas com FastAPI e Vue 3, em desenvolvimento incremental. A aplicação possui cadastro, login, logout e gerenciamento de tarefas pela interface Vue, integrados ao backend FastAPI com SQLite. Clean Architecture separa domínio, casos de uso, infraestrutura e HTTP.

## 1. Preparar o Windows e o WSL

1. Instale o Ubuntu 24.04 no WSL 2.
2. Instale e inicie o Docker Desktop no Windows com o mecanismo WSL 2 habilitado.
3. Em **Settings → Resources → WSL Integration**, habilite a distribuição **Ubuntu-24.04** e aplique a alteração.
4. Abra o terminal Ubuntu e confira:

```bash
cat /etc/os-release
git --version
docker version
docker compose version
```

`docker version` deve mostrar Client e Server. Se não conectar ao daemon, confira se o Docker Desktop está aberto e a integração com a distribuição está ativa. Não instale outro daemon Docker dentro do Ubuntu se estiver usando Docker Desktop.

## 2. Colocar o projeto no diretório local

O caminho no Windows:

```text
\\wsl$\Ubuntu-24.04\home\rafael\projetos\taskflow
```

corresponde, dentro do Ubuntu, a:

```text
/home/rafael/projetos/taskflow
```

Execute no Ubuntu com o usuário `rafael`, mantendo o projeto no filesystem Linux para melhor desempenho:

```bash
mkdir -p /home/rafael/projetos
cd /home/rafael/projetos
git clone https://github.com/RafaelMaizonave/taskflow.git
cd taskflow
```

Se o diretório já existir, não repita o clone nem sobrescreva arquivos: confira `git status` e preserve alterações locais antes de atualizar.

Se você já abriu uma pasta vazia no editor, pode clonar diretamente nela:

```bash
cd /home/rafael/projetos/taskflow
git clone https://github.com/RafaelMaizonave/taskflow.git .
```

Use esse comando somente se a pasta estiver vazia e ainda não for um repositório Git. Para um clone existente sem alterações locais, atualize com:

```bash
cd /home/rafael/projetos/taskflow
git status
git pull --ff-only origin main
```

Não é necessário baixar ou extrair um pacote separado: os arquivos de configuração fazem parte do repositório.

## 3. Iniciar com Docker

Não é necessário instalar Python, Node ou uv no WSL para essa opção.

```bash
cd /home/rafael/projetos/taskflow
# Gere uma configuração local, sem sobrescrever um .env existente.
# O segredo é gravado no arquivo; não é exibido no terminal.
test -e .env || (umask 077; printf 'JWT_SECRET=%s\n' "$(openssl rand -hex 32)" > .env)
docker compose config --quiet
docker compose up --build -d --wait
docker compose ps
curl --fail http://localhost:5173/
curl --fail http://localhost:8000/health
```

Abra **http://localhost:5173** no navegador do Windows. Você será direcionado ao login. Clique em **Criar conta**, cadastre um e-mail e uma senha de 8 a 128 caracteres e, depois, faça login. O dashboard permite criar, editar, excluir e alterar o status das tarefas. Pesquisa e filtro são aplicados ao clicar em **Aplicar filtros**. Não há usuário ou senha padrão.

O token fica apenas em memória: atualizar a página exige novo login. Os dados das tarefas continuam no SQLite. Para testar o isolamento, crie uma tarefa, saia e entre com outra conta; ela não deve ver a tarefa anterior.

A porta é publicada apenas no loopback do host. Se estiver ocupada, encerre o serviço que a utiliza ou ajuste o mapeamento de porta no Compose.

```bash
# Acompanhar logs
docker compose logs -f frontend

# Parar e remover os contêineres desta configuração
docker compose down
```

O diretório `frontend/src` é montado como somente leitura para o contêiner: alterações feitas pelo editor no WSL acionam o Vite sem reinstalação. Alterações em dependências ou configurações exigem novo `docker compose up --build -d --wait frontend`.

O backend responde em http://localhost:8000/health com `{"status":"ok"}` e publica Swagger em http://localhost:8000/docs. O health check executa uma consulta ao SQLite; falhas de conexão retornam 503 sem expor detalhes internos.

O SQLite fica no volume nomeado `taskflow-data`, em `/app/data/taskflow.db`. `docker compose down` preserva esse volume; `docker compose down -v` apaga os dados. O serviço `backend-quality` é uma ferramenta separada de verificação.

O Compose lê `JWT_SECRET` do `.env` na raiz. Segredo ausente, vazio ou menor que 32 caracteres impede a inicialização. Se já existir `.env`, confira sua configuração sem divulgar seu conteúdo. Não execute `docker compose config` sem `--quiet` ao compartilhar logs, pois a saída resolvida pode conter segredos.

## 4. Testar com Docker

Na raiz do projeto, execute:

```bash
# Backend: instalação congelada na imagem e verificações de qualidade
docker compose run --build --rm backend-quality
docker compose run --rm backend-quality uv run ruff format --check .
docker compose run --rm backend-quality uv run pytest -q

# Frontend: lint, tipos, testes unitários e build
docker compose run --rm frontend npm run lint
docker compose run --rm frontend npm run typecheck
docker compose run --rm frontend npm run test:unit
docker compose run --rm frontend npm run build

# E2E: imagem com Chromium e dependências Linux
docker compose run --build --rm e2e
```

Os serviços de ferramentas são ativados explicitamente; não ficam executando com o frontend. A imagem E2E é separada e contém Node, Python, uv e Chromium para testar o frontend contra a API real. O teste E2E compila a aplicação, inicia Uvicorn na porta interna 18765 com SQLite temporário e abre preview na porta 4173. Não depende dos serviços de desenvolvimento; o banco temporário é removido ao encerrar.

Vitest testa a sessão em memória e o formulário de tarefas. Playwright testa a aplicação compilada em Chromium com configurações desktop e mobile: cadastro, confirmação de senha, login inválido/válido, CRUD, filtros, cancelamento da exclusão, logout e perda da sessão ao recarregar. O cenário de 401 usa uma falha controlada na resposta de tarefas para verificar a limpeza da sessão; o fluxo principal usa a API real. A emulação mobile não substitui testes em aparelho físico.

O backend usa Pytest e HTTPX com bancos temporários isolados. Os testes cobrem configuração, restrições e persistência SQLite, sessões, health check, CORS e um servidor Uvicorn real com reinicialização. Cadastro, duplicidade, login, tokens inválidos/expirados, CRUD, filtros e isolamento entre usuários também são cobertos.

## 5. Executar sem Docker

Requer Python 3.12, uv (validado com 0.12.23), Node.js 24 e npm 11.

```bash
cd /home/rafael/projetos/taskflow/backend
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
# Somente se backend/.env ainda não existir:
test -e .env || (umask 077; printf 'JWT_SECRET=%s\nCORS_ORIGINS=["http://localhost:5173"]\n' "$(openssl rand -hex 32)" > .env)
uv run uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000

# Em outro terminal:
cd /home/rafael/projetos/taskflow/frontend
npm ci
npm run lint
npm run typecheck
npm run test:unit
npx playwright install --with-deps chromium
npm run test:e2e
npm run dev
```

A instalação de dependências Linux do navegador pode solicitar sudo. Se houver Chromium instalado, é possível selecionar seu executável:

```bash
PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/chromium npm run test:e2e
```

## Configuração e segurança

Os testes geram configuração isolada e não exigem segredos reais. O backend executado manualmente lê `backend/.env`; o Compose lê `.env` na raiz. `frontend/.env.example` documenta `VITE_API_BASE_URL`, cujo padrão é `/api/v1`. O Vite encaminha `/api` para o backend: no Compose, `API_PROXY_TARGET=http://backend:8000`; na execução manual, o padrão é `http://127.0.0.1:8000`. `API_PROXY_TARGET` é lido do processo que inicia Vite, não do arquivo `.env`. Variáveis VITE são públicas e nunca devem conter segredos.

`backend/.env.example` documenta `DATABASE_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` e `CORS_ORIGINS`. Essas variáveis já são validadas na inicialização, incluindo algoritmo HS256, duração entre 1 e 1440 minutos e origens HTTP explícitas, sem wildcard ou caminho. O segredo está vazio no exemplo de propósito e é obrigatório. Nunca versione `.env`.

Os Dockerfiles usam lockfiles para instalar dependências. `.dockerignore` exclui arquivos locais, segredos e dependências do host do contexto de build. As imagens são destinadas ao desenvolvimento e testes; não representam uma implantação de produção.

## Arquitetura e decisões

```text
backend/app/
├── domain/          # Entidades e regras independentes de frameworks
├── application/     # Casos de uso e contratos pequenos
├── infrastructure/  # Banco, configuração, Argon2 e JWT
└── presentation/    # HTTP, schemas e tradução de erros
backend/tests/
frontend/src/{api,components,router,stores,types,views}
frontend/e2e/
.github/workflows/ci.yml
docs/issues/
```

O domínio define os status permitidos sem importar frameworks. A infraestrutura implementa configuração e persistência; apresentação fornece health e dependência de sessão; `main.py` compõe a aplicação e seu ciclo de vida. Os casos de uso de autenticação e tarefas dependem de contratos pequenos para repositórios, senhas e tokens. Dependências de código apontam para domínio e aplicação. SQLAlchemy é síncrono. SOLID é aplicado com contratos específicos, evitando repositories genéricos e containers externos.

Vue usa Composition API, Router e Pinia. Tailwind cuida dos estilos. Ruff, ESLint e TypeScript verificam qualidade; Vitest e Playwright verificam comportamentos. O CI está configurado para essas verificações; sua execução remota precisa ser conferida no GitHub após publicação dos arquivos.

## Próximas entregas e limitações

Veja [o plano e os critérios das issues](docs/PLAN.md). As próximas etapas incluem revisão da cobertura, revisão final de segurança e validação Docker completa.

Tokens são mantidos apenas em memória: recarregar a página exigirá novo login. Logout local não revoga JWT já emitido. Para produção, avaliar cookies HttpOnly/Secure, proteção CSRF, revogação e rotação de tokens, rate limiting, recuperação de senha, migrações e observabilidade.

## Validação desta entrega

- Compose validado com `docker compose config --quiet`.
- Aplicação validada fora do Docker: backend com 106 testes unitários, integração e E2E de servidor real aprovados; frontend com build, 5 testes unitários e 6 E2E aprovados.
- Build das imagens neste ambiente em nuvem bloqueado por resolução DNS/rede ao instalar dependências, inclusive ao testar a rede do host. A inicialização e os testes dentro dos contêineres permanecem sem validação; devem ser executados no WSL com os comandos acima.
- Nenhuma instalação ou execução no WSL do usuário foi realizada remotamente.

## Persistência e ciclo de vida do backend

Na inicialização, a aplicação valida configurações, cria o diretório do banco e as tabelas ausentes. Na finalização, libera o engine. Cada requisição que depende do banco recebe uma sessão própria, fechada ao terminar; commits e rollbacks são coordenados pelos serviços de aplicação. Sessões não executam commit automaticamente.

`users` possui e-mail único e hash de senha. `tasks` possui título obrigatório de até 200 caracteres, descrição, status restrito, data de criação gerada em UTC e chave estrangeira para usuário. A integridade referencial é habilitada em toda conexão SQLite; exclusão de usuário remove suas tarefas. Datas são gravadas como UTC; SQLite não preserva informação de fuso no tipo datetime, e as respostas HTTP explicitam UTC na serialização.

`create_all` permite reinicializações sem apagar dados, mas não migra tabelas existentes. Evolução de esquema exigirá migrações. Os endpoints de autenticação e tarefas são documentados abaixo. Não há migrações automáticas de esquema.

## Contratos do backend

Consulte [autenticação, tarefas e decisões de arquitetura](docs/BACKEND.md) para os contratos REST e o passo a passo de validação no Swagger.
