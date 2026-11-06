# Validação do experimento offline de extração

01/11/2026. Base: `0ac98d72bb3dd17c2625fc15dbb55a6f75fe82bd`. Método experimental `REGEX_EXPERIMENT_V1`; decisão no [ADR-009](adrs/009-experimento-offline-de-extracao.md). Commit final/execução remota devem ser vinculados na descrição do PR; resultados locais não são CI remota.

## Evidência por comportamento

Todos os testes novos ficam em [test_extraction_experiment.py](../tests/unit/test_extraction_experiment.py); integridade das anotações em [test_synthetic_cases.py](../tests/unit/test_synthetic_cases.py).

| Comportamento | Cenário/resultado esperado | Teste ou execução |
|---|---|---|
| Campos/evidências e cálculo isolados | Cláusulas explícitas geram término/aviso com origem; nenhuma confirmação | `test_rules_extract_sources_calculate_but_never_confirm`; execução offline no JSON |
| Bloqueios suportados | Unidade indefinida, conflito, aditivo declarado, data impossível, antecedência negativa/fracionária retiram todos os candidatos | `test_known_blockers_remove_all_proposed_events`, 6 casos |
| Vazio distinto de abstenção | Ausência de match não comprova análise vazia | `test_no_match_is_abstention_instead_of_verified_empty` |
| Separação do gabarito | Extrator recebe documentos, não expectativas/ID de caso; mudar ID de citação não muda valor | `test_rules_do_not_read_case_ids_filenames_or_answers` e `test_extractor_only_receives_documents_and_report_fingerprints_inputs` |
| Falha semântica mensurada | Data em exemplo tem citação literal e é falso positivo; vigência real omitida | `test_literal_quote_without_semantic_support_is_not_a_true_positive` e DEV-020 no relatório |
| Impedimento não suportado visível | Aditivo só no conteúdo não reconhecido resulta em bloqueio perdido e candidatos indevidos | `test_unsupported_blocker_is_visible_as_miss_and_false_event`; não é correção do extrator |
| Evidência inválida, repetida ou sem suporte | Citação inexistente não é acerto, duplicatas viram FP e bloqueio em trecho alheio é erro | `test_invalid_quote_and_duplicate_predictions_cannot_inflate_correctness` e `test_blocker_with_literal_but_unrelated_quote_is_not_supported` |
| Erros/timeout | Falha não é vazio, omissões permanecem no denominador, mensagem documental não entra no relatório | `test_technical_failures_keep_denominators_and_are_not_empty` e `test_timeout_is_failure_and_preserves_expected_event_denominator` |
| Normalização/escopo | Preservar linhas vazias com BOM/CRLF; rejeitar caminho fora do conjunto | `test_loading_validates_reference_normalization_and_rejects_path_escape` |
| Independência da avaliação | CLI recusa split reservado e identifica relatório como desenvolvimento | `test_evaluation_refuses_reserved_split` e teste de hashes |
| Execução reproduzível | CLI escreve JSON uma vez; não sobrescreve evidência existente | `test_cli_outputs_report_without_overwriting_previous_evidence` |
| Ampliação dos dados | 20 casos/21 documentos com anotações localizadas e datas coerentes; suporta término sem aviso | Dois testes de integridade do catálogo, sendo um parametrizado em 20 casos; `test_annotated_cases_match_manual_rules_without_claiming_extraction` em 20 casos de entrada manual |

## Execução e regressões

Oito gabaritos anteriores comparados semanticamente ao JSON da base e preservados. Doze novos casos ampliam dias úteis/meses, âncora desconhecida, número inválido/divergente, aditivo no conteúdo, distratores e citação sem suporte. Todos os casos continuam visíveis e não representam avaliação reservada.

Os **76 testes focados passaram** (19 do experimento, 21 de integridade e 36 do levantamento manual). Ruff e formatação passaram. **208 testes passaram** na regressão completa, incluindo integração e interface; 38 arquivos/252 links locais verificados. Consistência do lock e dependências aprovadas. Os checks da CI remota ainda precisam ser vinculados ao commit do PR.

A primeira execução focada encontrou uma chamada de teste sem o argumento opcional de bloqueios; ajustada a construção de `Proposal` para aceitar bloqueios vazios. Três testes não conseguiram criar a pasta temporária padrão do ambiente; a repetição usou diretório novo dentro de `.tools/test-temp/`, sem ocultar a falha nem alterar regras do produto. A primeira regressão completa encontrou 11 falhas e 197 aprovações: o teste de mapeamento manual só tratava os dois IDs bloqueados antigos e pressupunha aviso em todo término. O teste passou a usar impedimentos anotados e aviso opcional; nenhuma regra da aplicação foi alterada para fazê-lo passar. O caso de unidade indefinida continua exercitando a validação de unidade. Os 76 testes pertinentes passaram após as correções. A execução completa usa bancos e sessões de teste, sem acessar o banco de operação.

O [JSON da execução](evidencias/extracao-regras-v1.json) registra 20 casos, 11 correspondências integrais, 2 abstenções, 5 casos com impedimento perdido e 7 candidatos indevidos. Nenhum evento foi gravado ou confirmado. Hash do módulo/conjunto/documentos conferido antes de versionar o relatório. Tempos são de uma execução local e incluem pontuação; não medem esforço humano, carga ou latência de IA.

## Limites comprovados e pendências

Não houve IA, API, gasto de API, integração à interface, mudança de esquema, migração do banco ou alteração da regra de cálculo. Falhas de saída e timeout foram injetadas apenas no avaliador; não implementam recuperação persistida nem estado de falha de análise na carteira. C20 completo continua pendente.

Correspondência estrita ao gabarito identifica estas regressões conhecidas; uma citação alternativa correta exigirá adjudicação humana, sem alterar automaticamente o gabarito para favorecer um método. A anotação foi feita pelo próprio agente em desenvolvimento e precisa de revisão humana; não houve avaliador/revisor independente. Não foram medidos modelo local, API hospedada, resistência geral a prompt injection, esforço manual ou comparação antes/depois de revisão.
