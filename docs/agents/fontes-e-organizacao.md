# Fontes e responsabilidades da documentação dos agentes

Consulta às fontes oficiais em **01/11/2026**. Revalide informações que possam mudar antes de alterar configuração ou comportamento das ferramentas.

## Fundamentos oficiais e escolhas locais

| Fonte oficial | Orientação usada | Aplicação no Radar |
|---|---|---|
| [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | Instruções globais e do projeto formam cadeia por diretório; overrides e limites de tamanho influenciam a descoberta. | Manter mapa na raiz. Links comuns não carregam destinos automaticamente; consultar rotas pertinentes. |
| [Rethinking skills and prompts](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) | Revisar instruções redundantes e direcionar leitura conforme a tarefa. | Encurtar entrada, preservar limites essenciais e avaliar o mapa em tarefas do Radar. O artigo trata de modelo específico e não prova ganho neste projeto. |
| [Build skills](https://learn.chatgpt.com/docs/build-skills) | Skills têm `SKILL.md`, metadados e conteúdo carregado conforme uso. | Guias nesta pasta são documentação. Criar skill apenas com workflow reutilizável concreto; não converter todos os guias em skills. |

`docs/agents/`, os nomes e a divisão abaixo são escolhas locais. Não são estrutura obrigatória da OpenAI. Não alteramos modelo, configuração global, mecanismos de descoberta, permissões ou orçamento.

## Responsabilidade de cada arquivo

| Arquivo | Responsabilidade | Consultar quando |
|---|---|---|
| [AGENTS.md](../../AGENTS.md) | Entrada curta, limites essenciais e mapa de leitura | Início de sessão e seleção da rota |
| [Fluxo de trabalho](fluxo-de-trabalho.md) | Preparação, fronteiras de código e conclusão de blocos | Implementação/correção |
| [Qualidade e evidências](qualidade-e-evidencias.md) | Checks, critérios de evidência e publicação | Teste, revisão ou PR |
| [Segurança e limites](seguranca-e-limites.md) | Lembretes dos invariantes com links às decisões | Mudança em fluxo documental, cálculo, persistência ou integração |
| [Continuidade](continuidade.md) | Protocolo de retomada e persistência | Retomada, interrupção e ações externas |
| [Harness](harness.md) | Ferramenta usada, mecanismos existentes e direção humana | Alterar ferramentas ou explicar colaboração |
| [Checkpoint](../RETOMADA.md) | Estado, pendências, próxima ação e evidências | Toda retomada e fim de bloco coerente |
| Este arquivo | Fontes, justificativa e inventário | Revisar instruções e organização |

PRD/SPEC/ADRs continuam responsáveis por requisitos e decisões; registros `validacao-*.md` e a matriz de evidências guardam resultados. Não mover esses documentos para a pasta dos agentes. A [governança](../governanca-repositorio.md) mantém controles e histórico de publicação.

## Migração e compatibilidade

A entrada anterior reunia produto, invariantes, comandos e revisão. Esses pontos foram redistribuídos nos guias acima; limites essenciais continuam visíveis na raiz. O conteúdo de `docs/agent-harness.md` passou para [harness](harness.md); o caminho antigo mantém uma ponte. O checkpoint continua em `docs/RETOMADA.md`, com títulos antigos de continuidade preservados como ponte para o procedimento. Referências históricas a commits continuam válidas e não são reescritas.

Não foram criadas skills, instruções aninhadas `AGENTS.md`, hooks ou configurações adicionais. Esta pasta não cria subagentes nem uma nova política de precedência.

## Como avaliar futuras alterações

Confira diff e preservação dos limites anteriores, rode o verificador de links e percorra tarefas representativas partindo do mapa. O [registro desta reorganização](../validacao-documentacao-agentes.md) separa essas verificações da descoberta automática numa sessão nova. Só afirme melhora de tempo, custo ou qualidade após medir com tarefas comparáveis; reduzir o arquivo de entrada, sozinho, não prova esse resultado.
