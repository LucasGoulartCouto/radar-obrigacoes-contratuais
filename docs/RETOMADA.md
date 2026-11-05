# Ponto de retomada do Radar

Última conferência: **01/11/2026, America/Sao_Paulo**. Este arquivo é um checkpoint do trabalho, não uma transcrição do chat. Revalidar os fatos que podem mudar antes de agir.

## Onde continuar

- Projeto local: `D:\Projetos\Git\desafio_jornadadados`.
- Repositório: [LucasGoulartCouto/radar-obrigacoes-contratuais](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais).
- Branch de trabalho observada: `feat/agenda-e-cobertura`, criada de `feat/candidatos-e-conferencia`, no commit `189962f64b2f3d2d0892e69fdae0fa5cff70c7ff`. A nova branch ainda não foi publicada.
- Última versão funcional verificada: `3d470fbdc986854583905544c61ec2800b80fc2b`. Atualizações posteriores deste checkpoint podem mudar o HEAD sem alterar a aplicação.
- A `main` ainda contém a documentação anterior à implementação. Abrir um clone na `main` não equivale a abrir a versão funcional mais recente.
- Nesta conferência, o código local coincidia com a versão publicada e não havia mudanças pendentes antes desta atualização documental. Consultar `git status` para o estado atual.

## Estado e evidências

| Entrega | Situação observada | Referência |
|---|---|---|
| Fundação local | Implementada; PR aberto para revisão de Lucas | [PR #1](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/1), base `main` |
| Decisão do fluxo e casos sintéticos | ADR-002 aceito; oito casos de desenvolvimento; PR aberto | [PR #2](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/2), base `feat/fundacao-local` |
| Entrada documental | Implementada; PR aberto; nenhum PR integrado pelo agente | [PR #3](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/3), base `feat/regras-e-casos-sinteticos` |
| Candidatos e conferência | Levantamento manual com evidências, cálculo, confirmação separada e histórico; PR aberto para revisão de Lucas | [PR #4](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/4), base `feat/entrada-documental` |
| Verificação da versão funcional | 123 testes locais aprovados e CI aprovada em Windows/Linux | [Validação da conferência](validacao-conferencia-manual.md) e [execução 41318794275](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/actions/runs/41318794275) |

Os PRs são encadeados. Depois de integrar um anterior, conferir a base e o diff do seguinte antes de integrá-lo. Check automático aprovado não representa revisão humana concluída. Não fazer merge por inferência de uma instrução genérica para continuar o desenvolvimento.

**Entrega funcional publicada:** candidatos e conferência concluídos no PR #4. O banco local foi migrado para 0003 após backup e comparação de todas as linhas anteriores; a demonstração no navegador criou candidatos, rejeitou confirmação sem declaração, registrou conferência simulada e preservou o resultado após recarregar. A CI do commit funcional e a [CI da atualização documental 7cc725f](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/actions/runs/41319321721) passaram nos dois sistemas.

**Critério de evidências concluído:** cada PR tem matriz por funcionalidade criada/alterada. AGENTS, modelo de PR e governança registram o critério; a [CI final do PR #4](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/actions/runs/41320755320) passou nos dois sistemas, com 123 nomes de testes aprovados em cada log. As descrições dos quatro PRs foram conferidas. Não repetir essa publicação.

**Em andamento, autorizado por Lucas:** agenda temporal e cobertura implementadas localmente. **165 testes locais passaram** (42 novos), incluindo leitura única de metadados, quatro grupos, filtros, referência vazia, invalidação/histórico, erro de consulta e origem desatualizada. A demonstração no navegador usou os três cadastros anteriores sem nova gravação: filtros vazios mantêm cobertura; referência 30/06/2027 mostra aviso ultrapassado e término hoje; recarregar retorna ao padrão e permite consultar origem. Evidência na [validação da agenda](validacao-agenda.md), com matriz por funcionalidade. Wheel/arquivo fonte inspecionados; pacote instalado em segundo ambiente consultou três contratos e dois eventos válidos. Não houve migração. Próxima ação: conferir links/diff, publicar esta branch e abrir PR dependente do #4, verificar CI e atualizar este registro com a referência publicada. Não fazer merge. O extrator automático continua pendente de avaliação, fornecedor e orçamento.

## Decisões que devem orientar a próxima etapa

Consultar os documentos de origem, sem tratar este resumo como nova autorização:

- [AGENTS.md](../AGENTS.md): instruções de execução, limites e comandos.
- [PRD](PRD.md) e [SPEC](specs/001-primeiro-fluxo.md): requisitos, estados e cenários; distinguir detalhe proposto de decisão aceita.
- [ADR-002](adrs/002-proposta-limites-extracao-e-confirmacao.md): extração sugere com evidências, código calcula e pessoa confirma; ambiguidade, conflito ou aditivo bloqueiam confirmação.
- [ADR-006](adrs/006-entrada-e-revisoes-documentais.md): identidade do conjunto, preservação dos bytes e revisões, limites e aditivo conhecido.
- [ADR-007](adrs/007-levantamento-manual-e-conferencia.md): evidências literais, levantamento manual, correções e confirmação vinculada à revisão e à regra; localização literal não comprova significado.
- [ADR-008](adrs/008-agenda-e-cobertura-da-carteira.md): agenda de consulta, horizonte de 30 dias, filtros e cobertura independente; limitações do caminho manual.
- [Plano de entrega](plano-de-entrega.md): dependências e marcos seguintes.

Somente dados sintéticos. Publicação no repositório e PRs estão autorizados; isso não autoriza mensagens a fornecedores, posts, despesas de API ou hospedagem. Fornecedor e orçamento de IA continuam em aberto. A proposta de evolução para escala fica depois de validar o fluxo local.

## Como retomar depois de interrupção

1. Confirmar a pasta e ler `AGENTS.md` e este arquivo. Um chat novo pode não ter o histórico da conversa anterior.
2. Ler `git status --short --branch`, `git log -5 --oneline` e o diff relevante. Preservar mudanças não concluídas; não trocar de branch, restaurar ou descartar arquivos para obter um estado aparentemente limpo.
3. Conferir o estado remoto dos PRs e da branch antes de publicar. Se uma operação foi interrompida, verificar seu efeito antes de repeti-la: branch, commit ou PR podem já existir mesmo sem uma resposta visível.
4. Identificar a última ação comprovada, a ação pendente e a verificação necessária. Se faltar confirmação do resultado, registrar **não verificado** e investigar; não presumir sucesso ou falha.
5. Executar apenas o trabalho seguinte do escopo vigente. Repetir testes quando houver mudança de código, falha ou dúvida concreta; mudanças somente documentais exigem links e diff, sem alegar nova execução dos testes da aplicação.
6. Atualizar este checkpoint após um bloco coerente e antes/depois de ações externas relevantes. Registrar brevemente ação, estado, próximo passo e referência da evidência. Não deixar essa atualização apenas para o final de uma tarefa longa.

O estado do checkpoint pode ficar uma ação atrás se a interrupção acontecer durante uma ferramenta. Por isso a retomada sempre reconcilia arquivo, Git e plataforma antes de repetir ações. Este procedimento reduz perda de contexto; não garante captura de cada instante.

## O que não é persistência do projeto

- O histórico e os resumos do chat ajudam, mas não são o único registro de trabalho.
- Variáveis de ferramentas, identificadores de abas, sessões de terminal e conexões autenticadas podem desaparecer. Redescobri-los quando necessário; não reutilizar handles ou PIDs antigos sem conferir.
- `.tools/` contém preparação de publicação, runtime e verificações locais. Pode ajudar no mesmo computador, mas está fora do Git e não é requisito para entender ou reconstruir o projeto.
- `.venv/`, `.uv-cache/`, `dist/` e `var/` ficam fora do Git. O banco e seus backups precisam ser preservados separadamente se o computador mudar; clonar o repositório não os recupera.
- Nunca registrar credenciais, tokens, cookies ou conteúdo sensível neste arquivo.

## Registro compacto de continuidade

**01/11/2026 — Entrada documental concluída.** A publicação foi interrompida por limite de uso durante a preparação da árvore remota. A retomada conferiu arquivos locais e estado remoto, concluiu o PR #3 e verificou sua CI; não havia PR #3 duplicado. Evidências na tabela acima. Não há bloqueio de publicação pendente dessa interrupção.

**01/11/2026 — Continuidade entre sessões.** Acrescentados este checkpoint e o protocolo em `AGENTS.md`. As decisões permanecem nos ADRs; este arquivo reúne o estado e aponta para as fontes. A próxima etapa funcional não foi iniciada durante essa organização.

**01/11/2026 — Candidatos e conferência publicados.** Lucas escolheu avançar para esta etapa. Publicados a branch e o PR #4; commit funcional e CI comprovados na tabela acima. Total de 123 testes locais, pacote instalado em segundo ambiente do projeto, migração preservando as linhas anteriores e demonstração de conferência simulada com evidências. A conferência é manual; não foi executada revisão humana real por Lucas. Antes de qualquer repetição da publicação deste checkpoint, comparar o HEAD remoto com o arquivo local.

**01/11/2026 — Evidências antes de avançar.** Lucas exigiu rastreabilidade por funcionalidade em cada PR destinado à main. A auditoria encontrou evidências existentes com descrição agregada; a matriz liga 36 comportamentos/verificações aos testes ou registros manuais, sem tratar integridade de gabarito como extração. As CIs dos quatro snapshots foram conferidas em Windows e Linux. Não houve mudança de regra de produto nem início da agenda. Antes de repetir operações de publicação, conferir o commit remoto e os blocos de evidência já existentes nas descrições dos PRs.

**01/11/2026 — Agenda e cobertura locais.** Após autorização para continuar, criada a branch `feat/agenda-e-cobertura` de `189962f`. Implementação/testes, matriz por funcionalidade e demonstração concluídos; publicação/CI remota ainda pendentes. A interface local está em execução com os novos módulos; conferir `.tools/runtime.json` antes de operar o processo, sem presumir PID antigo.

## Mensagem curta para outra conversa

“Continue o Radar no projeto `D:\Projetos\Git\desafio_jornadadados`. Leia `AGENTS.md` e `docs/RETOMADA.md`, confira Git e PRs e retome a próxima ação do escopo vigente. Preserve o trabalho pendente e não faça merge sem minha revisão.”

Em outro computador, abrir o repositório e a branch funcional indicada acima antes de usar essa mensagem. Os arquivos precisam estar disponíveis na nova sessão.
