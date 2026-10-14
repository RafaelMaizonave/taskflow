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

Routers → Services → Repositories → Database. SQLAlchemy síncrono, sessões por requisição e transações controladas pelos services. Sem repositories genéricos ou interfaces artificiais. SQLite e criação inicial de tabelas atendem ao escopo; migrações ficam como melhoria documentada. Tokens ficam apenas em memória. Atualizações e consultas filtram sempre pelo usuário autenticado.

A etapa inicial não implementa endpoints, banco, autenticação ou CRUD. Testes de comportamento e Docker serão adicionados nas entregas correspondentes. Não considerar o produto pronto com base apenas nos checks desta estrutura.
