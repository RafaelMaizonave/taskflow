# Interface e recursos do TaskFlow

A interface segue o layout fornecido em https://washi-coal-84340722.figma.site/login e os componentes do pacote TaskFlow To-Do List App.zip. Logo, ilustração de autenticação e favicon são SVGs desse material. A fonte Inter é servida localmente; sua licença está em frontend/public/fonts/OFL.txt.

## Responsabilidades

- `frontend/src/components/layout/AppShell.vue`: navegação, busca global, resumo lateral e avisos internos de prazo.
- `frontend/src/views/`: autenticação, dashboard, tarefas e perfil. As telas usam os mesmos dados da conta.
- `frontend/src/components/tasks/`: cartões e formulário em drawer; lista e Kanban permitem editar e excluir tarefas. Na lista, o status é editado diretamente pela coluna; o quadro permite mover tarefas sem abrir o formulário.
- `frontend/src/stores/tasks.ts`: estado da conta, filtros, resumo e coordenação das operações persistidas. Respostas antigas são descartadas ao trocar de conta.
- `frontend/src/api/tasks.ts`: mapeamento explícito dos campos HTTP `titulo`, `descricao` e `data_criacao` para os nomes usados pela interface.
- `backend/app/domain/` e `application/`: entidades, contratos e regras de conclusão, autenticação, perfil e senha, independentes de FastAPI e SQLAlchemy.
- `backend/app/infrastructure/`: persistência, hash, tokens e migração SQLite. `presentation/` valida entrada e traduz erros para HTTP.

## Dados e migração

Na inicialização, o banco SQLite antigo é atualizado em uma transação, identificada por `PRAGMA user_version`. A migração converte `pending` em `backlog` e `completed` em `done`, mantendo `in_progress`, IDs, proprietários, títulos, descrições, senhas e datas de criação das tarefas.

Tarefas existentes recebem prioridade média, tags vazias, prazo vazio e posição derivada da ordenação anterior. `updated_at` começa na data de criação quando não existe histórico. A data de cadastro de usuários antigos e a data de conclusão de tarefas antigas ficam desconhecidas (`null`). Novos eventos recebem timestamps reais. A migração não altera o banco antes de a versão atualizada da aplicação ser iniciada. O downgrade de esquema não é automático; mantenha o backup habitual antes de atualizar um banco com dados importantes.

## Comportamento

Cadastro continua exigindo confirmação de senha e login separado. A sessão é mantida em cookie HttpOnly e restaurada pela API antes de resolver a navegação. Recarregar preserva o login enquanto a sessão estiver válida; acessar `/login` autenticado redireciona ao dashboard. Logout remove o cookie. Perfil permite editar nome e e-mail. A troca de senha exige a senha atual; informá-la incorretamente retorna 403 e permite tentar novamente. JWTs já emitidos continuam válidos até expirar, conforme a política atual.

Tarefas possuem prioridade baixa, média ou alta; prazo de calendário opcional; tags; e posição no quadro. Datas de prazo são comparadas com a data local do navegador. O sino reúne tarefas não concluídas vencidas ou com prazo nos próximos três dias. Não envia e-mail, push ou avisos enquanto a aplicação está fechada.

Dashboard, progresso e avisos são calculados a partir das tarefas retornadas pela API da conta. Busca considera título, descrição e tags. Filtros de status e prioridade funcionam em conjunto. Não há checkbox de conclusão. Na lista, clicar no status abre um menu com bordas, cantos arredondados e cores do sistema para escolher Backlog, Em andamento ou Concluída e salva imediatamente, sem abrir o formulário. O controle fica bloqueado enquanto salva e conserva o status confirmado se a operação falhar. O Kanban permite arrastar e reordenar cartões; o mesmo menu de status da lista oferece alternativa por teclado e em dispositivos de toque. A preferência de visualização não é persistida; a sessão permanece no cookie até sair ou expirar.

## Validação manual

1. Inicie a aplicação pelo procedimento do README e cadastre uma conta.
2. Crie tarefas com diferentes prioridades, tags e prazos. Confira resumo, busca, filtros e sino.
3. Alterne lista e quadro; mova uma tarefa e faça login novamente para verificar a persistência.
4. Edite nome e e-mail no perfil. Teste senha atual incorreta e depois uma troca válida.
5. Saia e entre com outra conta: tarefas e estatísticas devem estar vazias.
6. Repita em viewport móvel e navegue com teclado, incluindo abrir e fechar o drawer.

Os testes E2E usam Chromium desktop e mobile com API real e banco temporário, sem acessar o volume da aplicação em desenvolvimento. Emulação mobile não substitui validação em aparelho físico.

## Resultado da validação local

Em 15/10/2026, passaram 124 testes backend, 11 testes unitários Vue e 16 E2E de navegador (desktop/mobile), além de Ruff, ESLint, tipagem e build. A revisão visual confirmou a reprodução e a correção de contraste secundário. Os contêineres locais foram reconstruídos e ficaram saudáveis.

Antes de iniciar a versão atualizada, foi salvo um backup SQLite em `/app/data/backups/before-redesign-20261015.db` no volume do backend. A comparação após migração confirmou a preservação da conta e da tarefa existentes, incluindo hashes e conteúdo, com a conversão esperada dos status. O volume não foi apagado.

A edição rápida de status foi validada em desktop e mobile, incluindo bloqueio durante uma resposta pendente, falha controlada de PATCH sem mudança do status confirmado, nova tentativa, persistência após login e reabertura. O checkbox foi removido das duas visualizações. Nesta alteração, não houve mudanças no backend; a validação de integração usa os endpoints existentes.

O menu de status é renderizado fora da tabela para não ser cortado pelas bordas do painel. Permite navegar com setas, Home/End, escolher com Enter e fechar com Escape ou clique externo.

Lista e Kanban reutilizam `StatusQuickEdit.vue`, incluindo estilo, opções, teclado e bloqueio durante o salvamento.

Os filtros de status e prioridade usam `SelectMenu.vue`, o mesmo controle de menu utilizado pela edição rápida via `StatusQuickEdit.vue`. O componente compartilha bordas, cores, marcação da opção selecionada, teclado e posicionamento fora do contêiner; os filtros mantêm as opções para exibir todos os itens.

A sessão expira conforme `ACCESS_TOKEN_EXPIRE_MINUTES` (padrão 30 minutos), sem renovação automática. Nenhum token é armazenado em localStorage ou sessionStorage. A primeira entrada após esta atualização cria o cookie; sessões antigas em memória não podem ser recuperadas após já terem sido perdidas. Implementação de cookies na borda HTTP segue [a API de Response do FastAPI](https://fastapi.tiangolo.com/advanced/response-cookies/).
