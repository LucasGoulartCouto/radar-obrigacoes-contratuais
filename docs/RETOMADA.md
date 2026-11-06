# Ponto de retomada do Radar

Última conferência: **02/11/2026, America/Sao_Paulo**. Este arquivo é um checkpoint do trabalho, não uma transcrição do chat. Revalidar os fatos que podem mudar antes de agir.

**Retomada em 02/11/2026:** Git limpo em `a01b7b5`, idêntico ao PR #9; nove PRs abertos/sem merge e CI final #9 aprovada conferidos pelo conector. Nova branch `codex/revisao-retencoes`, base `codex/ia-local-estruturada`. Revisão offline explícita das duas retenções publicada no PR #10 em rascunho, mantendo fonte/prompt/interpretador V1 intactos e preparando os requisitos da integração assistida. Execução persistida/UI/recuperação continuam pendentes.

**Retomada autorizada em 01/11/2026:** Lucas pediu continuar o Radar. A pausa anterior foi encerrada por esse pedido; preservada a prioridade de organizar a documentação dos agentes antes de iniciar extração ou outra funcionalidade.

## Onde continuar

- Projeto local: `D:\Projetos\Git\desafio_jornadadados`.
- Repositório: [LucasGoulartCouto/radar-obrigacoes-contratuais](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais).
- Branch de trabalho: `codex/revisao-retencoes`, base `codex/ia-local-estruturada` em `a01b7b594c4bfefe1b47c67e2c2fb30b03c4ab25`. [PR #10](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/10) publicado em rascunho, snapshot funcional `7fd880a4b267cac6e40a3d82deb10a904b9b1246`; descrição mantém HEAD/CI finais após este fechamento documental. Snapshots V1/V2/restauração preservados no [PR #9](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/9), em rascunho; nenhum merge.
- Última versão funcional verificada: `8a8c8b9ef741dac8acfdfeaf3dabed91d2c766e8`. Atualizações posteriores deste checkpoint podem mudar o HEAD sem alterar a aplicação.
- A `main` ainda contém a documentação anterior à implementação. Abrir um clone na `main` não equivale a abrir a versão funcional mais recente.
- Na retomada, o HEAD local coincidiu com o HEAD remoto do PR #5. Havia somente a alteração pendente deste checkpoint. PRs #1–#5 conferidos pelo conector: todos abertos, sem merge e com as bases indicadas abaixo. Consultar Git/plataforma para mudanças posteriores.

## Estado e evidências

| Entrega | Situação observada | Referência |
|---|---|---|
| Fundação local | Implementada; PR aberto para revisão de Lucas | [PR #1](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/1), base `main` |
| Decisão do fluxo e casos sintéticos | ADR-002 aceito; oito casos de desenvolvimento; PR aberto | [PR #2](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/2), base `feat/fundacao-local` |
| Entrada documental | Implementada; PR aberto; nenhum PR integrado pelo agente | [PR #3](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/3), base `feat/regras-e-casos-sinteticos` |
| Candidatos e conferência | Levantamento manual com evidências, cálculo, confirmação separada e histórico; PR aberto para revisão de Lucas | [PR #4](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/4), base `feat/entrada-documental` |
| Agenda e cobertura | Referência explícita, filtros, origem e todos os contratos visíveis; PR aberto para revisão de Lucas | [PR #5](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/5), base `feat/candidatos-e-conferencia` |
| Documentação dos agentes | Mapa, seis guias, pontes e retomada preservada; PR aberto para revisão de Lucas | [PR #6](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/6), base `feat/agenda-e-cobertura` |
| Comparação de extração | Experimento offline, 20 casos/21 documentos, falhas medidas; sem integração do baseline | [PR #7](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/7), base `codex/docs-agentes` |
| IA local de desenvolvimento | Runtime/modelo provisório operaram; candidato com falhas, sem integração; PR em rascunho | [PR #8](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/8), base `codex/avaliacao-extracao` |
| Protocolo por linhas | 18/20 casos integrais, zero candidatos indevidos/impedimentos perdidos; duas retenções e integração pendentes | [PR #9](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/9), base `codex/ia-local`, em rascunho |
| Revisão de retenções | Duas retenções tratadas por decisões simuladas; três candidatos recuperados manualmente; extração automática permanece 18/20; 319 testes locais aprovados | [PR #10](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/10), base `codex/ia-local-estruturada`, em rascunho; CI final na descrição |
| Verificação da versão funcional | 165 testes locais aprovados e CI aprovada em Windows/Linux | [Validação da agenda](validacao-agenda.md) e [execução 41330174954](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/actions/runs/41330174954) |

Os PRs são encadeados. Depois de integrar um anterior, conferir a base e o diff do seguinte antes de integrá-lo. Check automático aprovado não representa revisão humana concluída. Não fazer merge por inferência de uma instrução genérica para continuar o desenvolvimento.

**Entrega funcional publicada:** candidatos e conferência concluídos no PR #4. O banco local foi migrado para 0003 após backup e comparação de todas as linhas anteriores; a demonstração no navegador criou candidatos, rejeitou confirmação sem declaração, registrou conferência simulada e preservou o resultado após recarregar. A CI do commit funcional e a [CI da atualização documental 7cc725f](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/actions/runs/41319321721) passaram nos dois sistemas.

**Critério de evidências concluído:** cada PR tem matriz por funcionalidade criada/alterada. AGENTS, modelo de PR e governança registram o critério; a [CI final do PR #4](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/actions/runs/41320755320) passou nos dois sistemas, com 123 nomes de testes aprovados em cada log. As descrições dos quatro PRs foram conferidas. Não repetir essa publicação.

**Agenda publicada e verificada:** implementação no PR #5, com **165 testes locais e CI aprovada em Windows/Linux** (42 testes novos). A descrição liga cada funcionalidade aos testes no commit auditado e aos registros manuais. A demonstração usou os três cadastros anteriores sem nova gravação: filtros vazios mantêm cobertura; referência 30/06/2027 mostra aviso ultrapassado e término hoje; recarregar retorna ao padrão e permite consultar origem. Wheel/arquivo fonte inspecionados; pacote instalado em segundo ambiente consultou três contratos e dois eventos válidos. Não houve migração. Os cinco PRs continuam abertos, sem merge e sem revisão real de Lucas comprovada.

**Fechamento da entrega anterior concluído:** atualização documental publicada no commit `e0ea2c8285bdbe7c17e99741d97e92910f3e263f`, com [CI final aprovada em Windows/Linux](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/actions/runs/41330479495). A descrição do PR #5 já aponta para essa execução. Não repetir essa publicação.

**Organização dos agentes publicada e validada:** inventário concluído; `AGENTS.md` passou a mapa com leitura por tarefa, e seis guias foram criados em `docs/agents/`. O harness mantém ponte no caminho antigo; este checkpoint conserva seu caminho e histórico. Fontes oficiais reabertas em 01/11/2026 e justificativa em [fontes e organização](agents/fontes-e-organizacao.md). Nenhuma skill/configuração/modelo ou regra de produto foi alterada.

**Fechamento anterior conferido:** PR #6 aberto no HEAD `0ac98d72bb3dd17c2625fc15dbb55a6f75fe82bd`, com [CI final aprovada](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/actions/runs/41354571169). Git local limpo antes de criar a nova branch. Não repetir a publicação da organização dos agentes.

**Comparação inicial concluída e publicada:** experimento offline por regras e avaliador isolados de interface/banco; desenvolvimento ampliado de 8 para 20 casos/21 documentos. [Comparação](comparacao-extracao.md) distingue resultados medidos dos mecanismos documentados de IA local/API. Nenhum fornecedor escolhido ou gasto assumido. Documentos/gabaritos visíveis não são avaliação reservada.

**Última ação comprovada:** protocolo/interpretador literal implementados; 272 testes completos passaram. Rodada V1 dos mesmos 20 casos concluída e preservada: 18 casos integrais, zero falhas/candidatos indevidos, todos os 11 impedimentos reconhecidos. Duas retenções extras (DEV-008/020) omitiram 3 candidatos válidos. [Validação](validacao-extracao-por-linhas.md) e [JSON](evidencias/ia-local-linhas-v1.json) identificam fontes e limites.

**Snapshots preservados:** V1 `fd37c91ca662e397b9d783cdeccc970be1b4aee8`; tentativa V2 `004e902ba3fd9e4deddb651dc976a15f896dc157`. V2 regrediu para 16/20 e foi rejeitada. Prompt V1 restaurado com hash exato da referência; modelo, interpretação/guardas e conjunto não foram trocados. Nenhuma mudança na UI/banco.

**Publicação de restauração comprovada:** commit `67921308345841b100e583db2cd4e21f5a6d33d2`, árvore `631d198cc253abc23968c8b251ad8f45c970382c` comparada ao índice local; Git sincronizado antes deste registro. **PR #9 publicado em rascunho:** código/rodadas/matriz ligados ao commit. Este fechamento documental pode gerar outro HEAD; conferir SHA/CI finais na descrição do PR antes de retomar. Não repetir publicação sem comparar Git/plataforma. Fonte ativa conferida contra todos os componentes da rodada V1; 273 testes completos, Ruff/formatação, lock/dependências e 43 arquivos/280 links locais aprovados. Não repetir as rodadas nem a publicação dos snapshots anteriores. **Próximo passo funcional:** tratar as duas retenções conservadoras (instrução ao assistente e condição ilustrativa) e preparar integração assistida com revisão/execução/recuperação, preservando bloqueios, histórico e rejeição de base desatualizada. Não declarar generalização, integração pronta, C20 completo ou seleção de produção. Revisão de Lucas continua separada dos checks.

## Decisões que devem orientar a próxima etapa

**Última entrega em 02/11/2026:** revisão restrita de contexto implementada conforme [ADR-012](adrs/012-revisao-restrita-de-retencoes.md). CLI executada sobre DEV-008/020, sem inferência nova: dois recibos preservam antes/depois e recuperam três candidatos por decisões simuladas do agente; zero confirmação/gravação na aplicação. 46 testes focados e 319 completos aprovados; Ruff/formatação, lock/dependências e links aprovados. Diagnóstico/execução da suíte documentados na [validação](validacao-revisao-retencoes.md). A referência automática continua 18/20. PR #10 publicado em rascunho no snapshot `7fd880a`, árvore remota idêntica ao índice local; Git sincronizado antes deste fechamento. Não repetir publicação sem comparar plataforma/Git. Conferir CI final na descrição do PR antes de retomar. **Próximo bloco funcional:** implementar execução persistida, revisão assistida na tela e recuperação explícita na aplicação local, seguindo o desenho da validação e preservando aditivo histórico, seleção, concorrência e confirmação separada. Não confundir recibo offline com execução persistida/C20; não atribuir a revisão simulada ao Lucas.

Consultar os documentos de origem, sem tratar este resumo como nova autorização:

- [AGENTS.md](../AGENTS.md): instruções de execução, limites e comandos.
- [PRD](PRD.md) e [SPEC](specs/001-primeiro-fluxo.md): requisitos, estados e cenários; distinguir detalhe proposto de decisão aceita.
- [ADR-002](adrs/002-proposta-limites-extracao-e-confirmacao.md): extração sugere com evidências, código calcula e pessoa confirma; ambiguidade, conflito ou aditivo bloqueiam confirmação.
- [ADR-006](adrs/006-entrada-e-revisoes-documentais.md): identidade do conjunto, preservação dos bytes e revisões, limites e aditivo conhecido.
- [ADR-007](adrs/007-levantamento-manual-e-conferencia.md): evidências literais, levantamento manual, correções e confirmação vinculada à revisão e à regra; localização literal não comprova significado.
- [ADR-008](adrs/008-agenda-e-cobertura-da-carteira.md): agenda de consulta, horizonte de 30 dias, filtros e cobertura independente; limitações do caminho manual.
- [Plano de entrega](plano-de-entrega.md): dependências e marcos seguintes.

Somente dados sintéticos. Publicação no repositório e PRs estão autorizados; isso não autoriza mensagens a fornecedores, posts, despesas de API ou hospedagem. IA local no desenvolvimento está decidida; planejamento e seleção da IA de produção ficam depois da aplicação concluída. A proposta de evolução para escala fica depois de validar o fluxo local.

## Como retomar depois de interrupção

O procedimento mantido está em [continuidade entre sessões](agents/continuidade.md). Reconciliar Git, arquivos e plataforma antes de repetir ações; atualizar este checkpoint após blocos coerentes e antes/depois de ações externas relevantes. Este título permanece para referências existentes.

## O que não é persistência do projeto

Consulte [o que persiste e o que precisa ser redescoberto](agents/continuidade.md#o-que-persiste-e-o-que-precisa-ser-redescoberto). Banco/backups não vêm com o clone; sessões e identificadores precisam ser conferidos. O checkpoint não captura automaticamente cada instante.

## Registro compacto de continuidade

**01/11/2026 — Entrada documental concluída.** A publicação foi interrompida por limite de uso durante a preparação da árvore remota. A retomada conferiu arquivos locais e estado remoto, concluiu o PR #3 e verificou sua CI; não havia PR #3 duplicado. Evidências na tabela acima. Não há bloqueio de publicação pendente dessa interrupção.

**01/11/2026 — Continuidade entre sessões.** Acrescentados este checkpoint e o protocolo em `AGENTS.md`. As decisões permanecem nos ADRs; este arquivo reúne o estado e aponta para as fontes. A próxima etapa funcional não foi iniciada durante essa organização.

**01/11/2026 — Candidatos e conferência publicados.** Lucas escolheu avançar para esta etapa. Publicados a branch e o PR #4; commit funcional e CI comprovados na tabela acima. Total de 123 testes locais, pacote instalado em segundo ambiente do projeto, migração preservando as linhas anteriores e demonstração de conferência simulada com evidências. A conferência é manual; não foi executada revisão humana real por Lucas. Antes de qualquer repetição da publicação deste checkpoint, comparar o HEAD remoto com o arquivo local.

**01/11/2026 — Evidências antes de avançar.** Lucas exigiu rastreabilidade por funcionalidade em cada PR destinado à main. A auditoria encontrou evidências existentes com descrição agregada; a matriz liga 36 comportamentos/verificações aos testes ou registros manuais, sem tratar integridade de gabarito como extração. As CIs dos quatro snapshots foram conferidas em Windows e Linux. Não houve mudança de regra de produto nem início da agenda. Antes de repetir operações de publicação, conferir o commit remoto e os blocos de evidência já existentes nas descrições dos PRs.

**01/11/2026 — Agenda e cobertura locais.** Após autorização para continuar, criada a branch `feat/agenda-e-cobertura` de `189962f`. Implementação/testes, matriz por funcionalidade e demonstração concluídos; publicação/CI remota ainda pendentes. A interface local está em execução com os novos módulos; conferir `.tools/runtime.json` antes de operar o processo, sem presumir PID antigo.

**01/11/2026 — Agenda publicada.** Criado o PR #5; árvore remota conferida com o índice local. CI do commit funcional passou nos dois sistemas. A tabela acima registra commit/evidência e a próxima etapa, preservando as limitações da extração e da revisão humana. O registro anterior descreve o ponto local anterior à publicação; não é uma pendência atual.

**01/11/2026 — Pausa e nova prioridade.** Lucas informou 9% de limite restante e solicitou parar até renovar. A próxima sessão deve começar pela documentação dos agentes, não pela extração. Consulta inicial à OpenAI registrada acima; reorganização, commit e publicação deste novo bloco ficaram para a retomada. Sem mudança na aplicação.

**01/11/2026 — Retomada e organização dos agentes concluída.** Pedido de continuação revogou a pausa. Git/PRs reconciliados; pendência do checkpoint preservada na branch própria. Publicados mapa e seis guias no PR #6; evidências documentais e CI inicial aprovadas. Este fechamento mantém a referência do HEAD/CI finais na descrição do PR, evitando atualização autorreferente. Descoberta automática em nova sessão e ganho de custo/qualidade não foram medidos; extração não iniciada.

**01/11/2026 — Experimento de extração publicado.** PR #7 com baseline offline e avaliador, 20 casos de desenvolvimento e gabaritos anteriores preservados. 208 testes locais e execução do método comprovados; matrizes e resultados finais de CI na descrição do PR. A precisão de candidatos foi 11/18 e cinco impedimentos passaram sem reconhecimento. Não houve IA, despesa, migração ou integração à agenda. Próxima rodada depende de ambiente/fornecedor, orçamento, critérios e avaliação reservada, sem tratar exemplos visíveis como independentes.

**01/11/2026 — IA local preparada e avaliada.** Lucas escolheu execução local e adiou planejamento/seleção de produção até a aplicação concluída. Runtime e candidato provisório operaram no computador; 242 testes passaram. A rodada V2 teve 19 candidatos indevidos e 3 respostas rejeitadas, preservadas no PR #8 em rascunho. Próximo bloco: revisar schema/prompt e bloqueios, sem integrar essa versão nem iniciar seleção de produção.

**01/11/2026 — Protocolo por linhas publicado.** PR #9 preserva referência V1 (18/20, sem candidatos indevidos ou impedimentos perdidos), tentativa V2 rejeitada por regressão e restauração da fonte exata de V1. 273 testes locais passaram; resultado final de CI vinculado no PR. A IA classifica linhas, o código interpreta literais/monta evidências; métricas são da combinação. Duas retenções extras permanecem em desenvolvimento conhecido, sem integração ou avaliação independente. Produção/seleção definitiva de modelo continuam depois da aplicação concluída.

## Mensagem curta para outra conversa

“Continue o Radar no projeto `D:\Projetos\Git\desafio_jornadadados`. Leia `AGENTS.md` e `docs/RETOMADA.md`, confira Git e PRs e retome a próxima ação do escopo vigente. Preserve o trabalho pendente e não faça merge sem minha revisão.”

Em outro computador, abrir o repositório e a branch funcional indicada acima antes de usar essa mensagem. Os arquivos precisam estar disponíveis na nova sessão.
