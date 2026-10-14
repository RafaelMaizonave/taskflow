# Diretrizes do projeto

- Escrever mensagens de commit em português. Prefixos convencionais como `feat:`, `fix:`, `test:`, `docs:` e `chore:` são permitidos; o assunto deve descrever a mudança concreta em português.
- Não executar commits, pushes ou publicações sem autorização do usuário para a entrega correspondente.
- Priorizar código simples, legível, consistente e alinhado à arquitetura e às convenções existentes. Evitar abstrações artificiais, duplicação e dependências sem necessidade prática.
- Usar comentários apenas para explicar decisões, restrições ou comportamentos não óbvios. Evitar comentários que apenas repitam o código, frases genéricas e relatos do processo de geração.
- Não incluir referências a assistentes, prompts ou geração automática em comentários, mensagens de commit ou documentação técnica quando não forem relevantes ao funcionamento ou à manutenção do projeto. Preservar avisos de licença, atribuições obrigatórias e informações de procedência exigidas.
- Não inserir afirmações falsas de autoria ou de desenvolvimento exclusivamente humano.
- Não deixar implementações incompletas disfarçadas de funcionalidades prontas. Documentar limitações reais e pendências concretas; não afirmar que testes ou funcionalidades foram verificados sem executá-los.
- Manter nomes, tratamento de erros, tipagem e organização coerentes entre módulos. Revisar a entrega para remover código morto, placeholders desnecessários e inconsistências.
- Desenvolver em etapas pequenas e verificáveis, respeitando o escopo aprovado e informando validações e limitações de cada entrega.

## Arquitetura e práticas Python

- Seguir Clean Architecture: domínio e casos de uso não devem importar FastAPI, SQLAlchemy ou detalhes de transporte. Adaptadores HTTP e de persistência dependem dos contratos internos; a composição das dependências fica na borda da aplicação.
- Aplicar SOLID de forma proporcional: responsabilidades coesas (SRP), extensão em pontos de variação reais (OCP), contratos respeitados pelas implementações (LSP), contratos pequenos (ISP) e dependências voltadas às abstrações internas (DIP).
- Definir ports com `typing.Protocol` quando necessários para separar casos de uso de persistência, hash de senha e emissão/validação de tokens. Evitar interfaces genéricas, factories e hierarquias sem finalidade concreta.
- Usar entidades e objetos de valor Python simples, com `dataclass` e `Enum` quando úteis. Manter schemas Pydantic na borda HTTP e models SQLAlchemy na infraestrutura, com mapeamentos explícitos e pequenos.
- Usar injeção de dependências do FastAPI apenas na composição HTTP; passar dependências explicitamente aos casos de uso. Não usar service locator ou container externo.
- Encapsular consultas nos repositories, inclusive filtros por proprietário. Casos de uso coordenam autorização e transações por contrato pequeno; a infraestrutura implementa commit e rollback. Não adicionar Unit of Work genérico sem necessidade.
- Seguir PEP 8, PEP 257 e anotações de tipos modernas. Usar Ruff, `pyproject.toml`, lockfiles e configuração validada via Pydantic Settings na infraestrutura.
- Usar context managers para recursos, exceções específicas de domínio/aplicação e tradução para HTTP na borda. Evitar capturas amplas que ocultem falhas e nunca registrar segredos.
- Manter SQLAlchemy síncrono no escopo atual. Não introduzir `async` para operações bloqueantes sem estratégia de execução apropriada.
- Priorizar testes de integração dos endpoints e testes unitários de regras de negócio relevantes. Preferir fixtures isoladas e parametrização do pytest; não criar testes que apenas reproduzam a implementação.
- Propor novos padrões apenas quando resolverem um problema concreto do escopo, explicando benefícios, custo e alternativa mais simples.

## Encerramento de cada tarefa

- Executar testes unitários e end-to-end pertinentes ao comportamento entregue, além dos checks de qualidade. Não substituir E2E por uma simples requisição HTTP quando houver uma interface navegável.
- Quando uma camada ainda não tiver comportamento implementado, declarar a ausência de testes aplicáveis em vez de criar testes artificiais ou informar uma execução sem testes como sucesso.
- Explicar resumidamente o que mudou, a responsabilidade dos módulos, decisões e alternativas relevantes, como validar e limitações. Fornecer contexto suficiente para o usuário explicar o código posteriormente.
