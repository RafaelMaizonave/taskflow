# Plano de implementação

Issues preparadas para RafaelMaizonave/taskflow. Os arquivos em `issues/` são os corpos prontos para publicação; sua existência não significa que as issues foram criadas no GitHub.

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

Estrutura recomendada para a próxima etapa:

```text
backend/app/
├── domain/          # Entidades, status e erros de negócio
├── application/     # Casos de uso e ports específicos com Protocol
├── infrastructure/  # SQLAlchemy, configuração, Argon2 e JWT
├── presentation/    # Routers, schemas Pydantic e tradução de erros
└── main.py          # Inicialização e composição
```

A estrutura inicial já separa os pacotes domain, application, infrastructure e presentation. As implementações serão adicionadas nas próximas etapas. Evitar repositories genéricos, interfaces artificiais e containers de dependência externos. SOLID deve preservar responsabilidades coesas e contratos pequenos, sem criar camadas sem função. SQLite e criação inicial de tabelas atendem ao escopo; migrações ficam como melhoria documentada. Tokens ficam apenas em memória. Atualizações e consultas filtram sempre pelo usuário autenticado.

A etapa inicial não implementa endpoints, banco, autenticação ou CRUD. Testes de comportamento e Docker serão adicionados nas entregas correspondentes. Não considerar o produto pronto com base apenas nos checks desta estrutura.
