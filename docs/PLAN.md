# Plano de implementação

Issues cadastradas em https://github.com/RafaelMaizonave/taskflow/issues. Os arquivos em `issues/` documentam os critérios de aceite. As issues #1, #2, #3, #4, #6 e #7 foram implementadas e entregues em commits separados em main. As issues #5, #8 e #9 foram consolidadas localmente com testes de integração, isolamento no navegador e validação Docker de persistência. Permanecem abertas no GitHub até a entrega e a confirmação do CI remoto.

| Ordem | Entrega | Dependências |
| --- | --- | --- |
| 01 | [Configurar a estrutura inicial e ferramentas](issues/01.md) | Nenhuma |
| 02 | [Implementar a base FastAPI e persistência SQLite](issues/02.md) | 01 |
| 03 | [Implementar cadastro e autenticação JWT](issues/03.md) | 02 |
| 04 | [Implementar CRUD de tarefas com isolamento por usuário](issues/04.md) | 03 |
| 05 | [Cobrir autenticação e tarefas com testes de integração](issues/05.md) | 04 |
| 06 | [Implementar login e cadastro no Vue](issues/06.md) | 03 |
| 07 | [Implementar dashboard responsivo de tarefas](issues/07.md) | 04, 06 |
| 08 | [Entregar Docker Compose e persistência](issues/08.md) | 05, 07 |
| 09 | [Finalizar documentação e validar a entrega](issues/09.md) | 08 |

## Sequência sugerida em três dias

- Dia 1: base, autenticação e tarefas (01–04), com verificações de integração durante o desenvolvimento.
- Dia 2: consolidar testes e implementar frontend (05–07).
- Dia 3: Docker, CI completo, documentação e validação integrada (08–09).

## Decisões

Clean Architecture e SOLID orientam a implementação. O fluxo HTTP será router → caso de uso → port → adaptador de persistência. A direção das dependências de código aponta para domínio e aplicação; esses módulos não importam FastAPI nem SQLAlchemy. SQLAlchemy permanece síncrono, com sessão por requisição e transações coordenadas pelos casos de uso através de um contrato pequeno.

Estrutura implementada:

```text
backend/app/
├── domain/          # Entidades, status e erros de negócio
├── application/     # Casos de uso e ports específicos com Protocol
├── infrastructure/  # SQLAlchemy, configuração, Argon2 e JWT
├── presentation/    # Routers, schemas Pydantic e tradução de erros
└── main.py          # Inicialização e composição
```

A estrutura inicial já separa os pacotes domain, application, infrastructure e presentation. Autenticação e CRUD estão implementados no backend; frontend autenticado está implementado e integrado à API. Evitar repositories genéricos, interfaces artificiais e containers de dependência externos. SOLID deve preservar responsabilidades coesas e contratos pequenos, sem criar camadas sem função. SQLite e criação inicial de tabelas atendem ao escopo; migrações ficam como melhoria documentada. Tokens ficam apenas em memória. Atualizações e consultas filtram sempre pelo usuário autenticado.

O backend possui endpoints, banco, autenticação e CRUD com testes de comportamento. A interface permite cadastro, login e gerenciamento de tarefas. Docker foi validado localmente, incluindo recriação do backend com persistência. `make test-infra` / `scripts/validate_compose.py` repetem essa verificação em um projeto isolado e integram o CI. Consulte [DEVELOPMENT.md](DEVELOPMENT.md) e [TESTING.md](TESTING.md) para o fluxo local e limitações.
