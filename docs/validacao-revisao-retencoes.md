# Validação da revisão de retenções e preparação da integração

02/11/2026. Base `a01b7b594c4bfefe1b47c67e2c2fb30b03c4ab25`, branch `codex/revisao-retencoes`. [ADR-012](adrs/012-revisao-restrita-de-retencoes.md). SHA/CI finais serão vinculados no PR deste bloco; não presumir publicação ou CI antes da conferência remota.

## Resultado executado

Reutilizadas as observações reais da [rodada V1](evidencias/ia-local-linhas-v1.json), com componentes/catálogo/documentos conferidos por hash. Nenhuma inferência nova. Os 20 resultados originais foram reconstruídos na suíte, mantendo fatos e códigos de bloqueio sem decisões. A referência automática continua **18/20**, com duas retenções.

A CLI de revisão foi executada separadamente para os dois casos abaixo, com declaração e justificativas **simuladas pelo agente**, sem revisão real de Lucas. Os fatos permanecem iguais aos originais; somente o tratamento da retenção é manual. Nenhum evento foi confirmado ou gravado no banco.

| Caso | Antes | Decisão simulada | Candidatos após revisão |
|---|---|---|---|
| DEV-008 | Dois fatos válidos, `unsupported_scope`, zero candidatos | Instrução ao assistente não é condição contratual | Término 30/06/2027; aviso 31/05/2027 |
| DEV-020 | Término real válido, `unsupported_scope`, zero candidatos | A data anterior está sob marcador de exemplo | Somente término 31/08/2027; exemplo 30/06 excluído |

Planos e recibos completos:

- DEV-008: [plano](evidencias/revisao-retencao-dev-008-plano.json) e [recibo](evidencias/revisao-retencao-dev-008.json).
- DEV-020: [plano](evidencias/revisao-retencao-dev-020-plano.json) e [recibo](evidencias/revisao-retencao-dev-020.json).

Os recibos identificam responsável simulado, instante UTC, hash da rodada, origem/labels completos, antes/depois e decisões. `confirmed=false`, `integrated_with_application=false`, `new_inference_requests=0`. Não somar os três candidatos recuperados manualmente aos acertos automáticos. Não houve troca de modelo, alteração de prompt/interpretador V1, API paga, migração ou operação na UI.

## Matriz por comportamento

| Comportamento | Cenário e resultado esperado | Teste/evidência |
|---|---|---|
| Revisão das duas retenções | Somente fatos já validados tornam-se candidatos, mantendo resultado bruto e label original | `test_review_releases_only_existing_facts_and_preserves_raw_retention`, dois casos |
| Decisão explícita | Declaração sozinha não resolve; exigir responsável, justificativa e decisão localizada | Testes de declaração/responsável/decisão em [test_extraction_review.py](../tests/unit/test_extraction_review.py) |
| Base desatualizada | Texto, papel, labels, aditivo ou versão alterados invalidam plano; caso/relatório também são comparados | `test_any_change_in_reviewed_base_invalidates_the_decision`, cinco variantes; `test_receipt_plan_is_bound_to_case_and_report` |
| Bloqueios preservados | Unidade, conflito, aditivo, data, âncora e número inválidos não podem ser dispensados como contexto | `test_domain_blockers_cannot_be_dismissed_by_context_review`, sete casos; teste de aditivo histórico |
| Texto misto/escopo | Prefixo de instrução não esconde número/condição; marcador de outro documento não libera exemplo; abstenção exige nova análise | Testes de texto misto, marcador e abstenção |
| Resolução parcial | Linha não resolvida continua bloqueada e sua própria evidência é exibida | `test_partial_resolution_keeps_the_unresolved_line_as_blocker_evidence` |
| Regressão da referência | Vinte observações preservam fatos e códigos de bloqueio sem revisão | `test_all_twenty_saved_observations_preserve_blockers_without_decisions` |
| Origem completa | Rejeitar linhas omitidas/desordenadas, componente/catálogo/documentos divergentes e tentativa falha/duplicada | Testes de origem e loader nos dois arquivos de teste |
| CLI/arquivo | Inspecionar/revisar sem confirmar ou inferir; repetição preserva recibo e parcial; plano inválido não grava | [test_retention_review.py](../tests/integration/test_retention_review.py) |
| Falha ao serializar | Resultado não serializável não cria recibo | `test_receipt_serialization_failure_does_not_create_result` |
| Execução real offline | Rodada preservada + plano explícito produzem recibos dos dois casos | Planos/recibos e comandos desta página |

**Verificação concluída: 46 testes focados e 319 testes completos aprovados**, Ruff/formatação, lock/dependências e 45 arquivos/295 links locais aprovados. O primeiro teste de bloqueio apontava equivocadamente DEV-005, que é válido; corrigido para os casos com impedimento existentes. O diretório temporário padrão não permitiu criar arquivos; os testes focados usaram diretório novo dentro de `.tools/test-temp/`. A primeira suíte completa ficou bloqueada ao abrir o socket interno do AppTest/asyncio na execução restrita; diagnóstico por faulthandler confirmou a pilha em `socket.accept`. A tentativa foi interrompida, sem alterar a aplicação. Nova execução com os recursos locais necessários e diretório temporário próprio aprovou os 319 testes em 27,56 s. Não foi necessário alterar testes ou código de tela. CI remota ainda pendente nesta preparação; resultado final será ligado no PR.

## Reproduzir a simulação

Ambiente do projeto preparado conforme README. Para inspecionar a origem, execute:

```powershell
uv run --locked python -m radar_contratos.infrastructure.experiments.retention_review --report docs/evidencias/ia-local-linhas-v1.json --catalog tests/fixtures/contracts/development/cases.json --case-id DEV-008
```

Revise o texto completo e o plano versionado, sem atribuir sua declaração ao Lucas. Para reproduzir a **simulação já preparada**, use o plano e um destino novo:

```powershell
uv run --locked python -m radar_contratos.infrastructure.experiments.retention_review --report docs/evidencias/ia-local-linhas-v1.json --catalog tests/fixtures/contracts/development/cases.json --case-id DEV-008 --plan docs/evidencias/revisao-retencao-dev-008-plano.json --output .tools/recibo-dev-008-nova-simulacao.json
```

Para DEV-020, substitua o ID e os caminhos correspondentes. CLI não invoca Ollama. Arquivo existente é rejeitado; não apague recibos para repetir silenciosamente a operação. Revisão rejeitada encerra com código 1 e mensagem sem texto documental. O modo de inspeção exibe hashes, sem conteúdo do documento em log.

## Próximo bloco: integração assistida na aplicação local

Este desenho prepara a implementação; **os comportamentos abaixo ainda não foram implementados/verificados**. Trata da aplicação de desenvolvimento, não de planejamento/seleção de IA de produção.

1. Persistir tentativa antes de inferir, ligada a contrato, revisão documental, método/prompt/interpretador, regra e hash do conjunto. Preservar execução anterior; sessão de tela não é fonte de verdade.
2. Executar inferência fora da transação de escrita. Rejeitar entrada excessiva antes de iniciar, conservar falha/interrupção explicitamente e não converter abstenção/falha em resultado vazio.
3. Na conclusão, comparar a revisão exibida com a atual dentro da escrita. Resultado de base antiga fica no histórico e não substitui a seleção vigente. Evitar que reenvio de recibo ou término tardio de tentativa antiga reative eventos.
4. Exibir origem/contexto, classificações, pendências e correções na conferência. Persistir o recibo da revisão de contexto com a execução; consultar o histórico real de aditivos, sem aceitar a declaração offline como substituto.
5. Selecionar resultado com justificativa quando diferente na mesma base, preservando antes/depois e demandando reconferência. Reutilizar resultado idêntico sem duplicar eventos; identificar método assistido, sem disfarçá-lo de levantamento manual.
6. Manter confirmação separada e atômica, comparando revisão, seleção e regra. Em mudança de documento/seleção/regra, remover eventos somente da visão atual e preservar histórico.
7. Tornar tentativa interrompida identificável e recuperável por nova tentativa explícita, sem retry infinito. Testar concorrência, interrupção, falha de persistência, migração preservando linhas e carteira nas seis situações antes de alegar C20 completo.

Não há aprovação independente, avaliação reservada, tempo humano medido, autenticação ou generalização comprovada. A aplicação pública permanece no caminho manual; a revisão offline não atualiza a agenda.
