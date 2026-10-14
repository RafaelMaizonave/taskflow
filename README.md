# TaskFlow

Aplicação de gerenciamento de tarefas com FastAPI e Vue 3, em desenvolvimento incremental. A versão atual entrega a estrutura de Clean Architecture, ferramentas de qualidade e uma página inicial Vue executável. **Cadastro, login, API, banco e CRUD ainda não foram implementados.**

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
docker compose config --quiet
docker compose up --build -d --wait frontend
docker compose ps
curl --fail http://localhost:5173/
```

Abra **http://localhost:5173** no navegador do Windows. Deve aparecer a página inicial do TaskFlow, informando que autenticação e tarefas serão implementadas nas próximas etapas.

A porta é publicada apenas no loopback do host. Se estiver ocupada, encerre o serviço que a utiliza ou ajuste o mapeamento de porta no Compose.

```bash
# Acompanhar logs
docker compose logs -f frontend

# Parar e remover os contêineres desta configuração
docker compose down
```

O diretório `frontend/src` é montado como somente leitura para o contêiner: alterações feitas pelo editor no WSL acionam o Vite sem reinstalação. Alterações em dependências ou configurações exigem novo `docker compose up --build -d --wait frontend`.

Não há servidor backend nas portas 8000 ou `/docs` nesta etapa. O serviço `backend-quality` é uma ferramenta de verificação, não uma API. Persistência SQLite por volume será adicionada junto da implementação do banco.

## 4. Testar com Docker

Na raiz do projeto, execute:

```bash
# Backend: instalação congelada na imagem e verificações de qualidade
docker compose run --build --rm backend-quality
docker compose run --rm backend-quality uv run ruff format --check .

# Frontend: lint, tipos, testes unitários e build
docker compose run --rm frontend npm run lint
docker compose run --rm frontend npm run typecheck
docker compose run --rm frontend npm run test:unit
docker compose run --rm frontend npm run build

# E2E: imagem com Chromium e dependências Linux
docker compose run --build --rm e2e
```

Os serviços de ferramentas são ativados explicitamente; não ficam executando com o frontend. A imagem E2E é separada para manter a imagem de desenvolvimento menor. O teste E2E compila a aplicação e abre seu próprio preview interno na porta 4173; não depende do frontend em 5173.

Vitest testa o componente inicial isolado em jsdom. Playwright testa a página compilada em Chromium com configurações desktop e mobile, incluindo título, conteúdo, erros de execução e largura da página. Não são testes de autenticação ou CRUD. A emulação mobile não substitui testes em aparelho físico.

O backend ainda não possui comportamento testável: os testes Pytest e HTTPX serão adicionados com os casos de uso e endpoints. Uma execução sem testes não será considerada uma validação bem-sucedida.

## 5. Executar sem Docker

Requer Python 3.12, uv (validado com 0.12.23), Node.js 24 e npm 11.

```bash
cd /home/rafael/projetos/taskflow/backend
uv sync --locked
uv run ruff check .
uv run ruff format --check .

cd ../frontend
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

A página inicial e os testes atuais não exigem `.env`. `frontend/.env.example` documenta `VITE_API_BASE_URL`; variáveis VITE são públicas e nunca devem conter segredos.

`backend/.env.example` documenta `DATABASE_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` e `CORS_ORIGINS` para a próxima etapa. Essas variáveis ainda não são consumidas. O segredo está vazio de propósito e deverá ser obrigatório ao implementar autenticação. Nunca versione `.env`.

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

As responsabilidades descritas para o backend orientam os próximos incrementos; os pacotes ainda estão vazios. Dependências de código apontarão para domínio e aplicação. FastAPI fará a composição das dependências na borda; SQLAlchemy será síncrono. SOLID será aplicado com contratos específicos, evitando repositories genéricos e containers externos.

Vue usa Composition API, Router e Pinia. Tailwind cuida dos estilos. Ruff, ESLint e TypeScript verificam qualidade; Vitest e Playwright verificam comportamentos. O CI está configurado para essas verificações; sua execução remota precisa ser conferida no GitHub após publicação dos arquivos.

## Próximas entregas e limitações

Veja [o plano e os critérios das issues](docs/PLAN.md). As próximas etapas incluem `/health`, `/docs`, `/api/v1/auth`, `/api/v1/tasks`, testes com banco isolado, dashboard e persistência SQLite por volume.

Tokens serão mantidos apenas em memória: recarregar a página exigirá novo login. Logout local não revoga JWT já emitido. Para produção, avaliar cookies HttpOnly/Secure, proteção CSRF, revogação e rotação de tokens, rate limiting, recuperação de senha, migrações e observabilidade.

## Validação desta entrega

- Compose validado com `docker compose config --quiet`.
- Aplicação validada fora do Docker: build, 2 testes unitários e 2 E2E aprovados.
- Build das imagens neste ambiente em nuvem bloqueado por resolução DNS/rede ao instalar dependências, inclusive ao testar a rede do host. A inicialização e os testes dentro dos contêineres permanecem sem validação; devem ser executados no WSL com os comandos acima.
- Nenhuma instalação ou execução no WSL do usuário foi realizada remotamente.
