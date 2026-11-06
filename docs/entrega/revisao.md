# Roteiro de revisão da entrega

04/11/2026. Preparado pelo agente para Lucas revisar o escopo atual de desenvolvimento. Referência inspecionada: `0ecf88246e0ac64f2c70fee885ea34e4f1831666`, PR #12; aplicação herdada do PR #11. Não registra aprovação humana, avaliação independente ou conclusão global da SPEC. Nenhuma inferência, instalação ou execução local da suíte foi repetida para produzir este documento.

## O que conferir primeiro

1. Abrir o [cartão](galeria/lucasgoulartcouto/README.md) e os [textos](publicacoes.md): conferir autoria e se as afirmações representam o projeto que Lucas quer apresentar. Os dois links de posts estão vazios; os materiais continuam rascunhos.
2. Ler a [situação da entrega](situacao.md), o [registro da integração](../validacao-integracao-assistida.md) e a [reprodução](../validacao-reproducao.md). A reprodução ocorreu nesta máquina, reutilizando Python/runtime; as conferências com personagens foram realizadas pelo agente.
3. Revisar os comportamentos abaixo e decidir se as limitações do recorte são aceitáveis para esta entrega. Anotar ajustes concretos antes de escolher outro bloco funcional ou de produção.

## Critérios e alcance da evidência

Os nomes identificam testes existentes, cujas asserções foram inspecionadas no snapshot de referência. A CI consultada comprova execução da suíte nesse snapshot, não valida o significado de qualquer contrato. Testes com classificador simulado ou observações salvas não são novas inferências. A coluna final delimita o que cada evidência permite concluir.

| Critério da SPEC | Evidência existente | Alcance para revisão |
|---|---|---|
| C01 — datas e confirmação separada | [test_extractions.py](../../tests/integration/test_extractions.py): `test_reservation_execution_selection_and_confirmation_are_separate`; [reprodução](../validacao-reproducao.md) | Fluxo automatizado com classificador simulado e DEV-001 com modelo real, seleção e confirmação simulada separadas |
| C02 — bissexto | [test_dates.py](../../tests/unit/test_dates.py): `test_reference_dates_from_spec` | Aritmética 01/03/2028 − 1 = 29/02/2028; a unidade foi fornecida ao código, não extraída nesse teste |
| C03 — não bissexto | Mesmo teste parametrizado em [test_dates.py](../../tests/unit/test_dates.py) | Aritmética 01/03/2027 − 1 = 28/02/2027, sem demonstração real dedicada deste fluxo |
| C04 — prazo zero | `test_reference_dates_from_spec`; [test_agenda.py](../../tests/integration/test_agenda.py): `test_confirmed_notices_reach_all_four_temporal_groups_and_keep_equal_dates_separate` | Zero preserva dois tipos de evento na mesma data; integração usa levantamento manual |
| C05 — unidade indefinida | [test_literal_extraction.py](../../tests/unit/test_literal_extraction.py): `test_invalid_literals_are_blocked_instead_of_coerced`; [test_reviews.py](../../tests/integration/test_reviews.py): `test_blocked_result_cannot_be_confirmed` | Interpretação literal bloqueia “30 dias”; confirmação rejeita levantamento bloqueado, sem presumir convenção |
| C06 — âncora sem data | [test_literal_extraction.py](../../tests/unit/test_literal_extraction.py): `test_other_anchor_and_missing_end_date_block_without_partial_events` | Interpretação de linhas fornecidas bloqueia âncora não suportada; não é reconhecimento geral de eventos |
| C07 — conflito/data impossível | [test_literal_extraction.py](../../tests/unit/test_literal_extraction.py): `test_date_conflict_preserves_facts_and_literal_span_including_empty_lines`, `test_impossible_date_is_domain_blocker_instead_of_normalized_fake_date` | Guarda/interpretação conservam origem e impedem candidatos aptos nos textos exercitados |
| C08 — envio idêntico | [test_documents.py](../../tests/integration/test_documents.py): `test_equivalent_set_keeps_revision_but_preserves_every_received_variant`; [test_reviews.py](../../tests/integration/test_reviews.py): `test_repeated_requests_and_equivalent_result_do_not_duplicate_or_invalidate` | Reenvio e resultado equivalente preservam revisão/conferência sem eventos duplicados |
| C09 — mesmo documento em outro cadastro | [test_documents.py](../../tests/integration/test_documents.py): `test_same_file_in_another_contract_is_separate_and_receipts_cannot_cross` | Persistência mantém contratos separados; recibo não cruza cadastros |
| C10 — aditivo | [test_extractions.py](../../tests/integration/test_extractions.py): `test_textual_amendment_remains_known_after_document_removal`, `test_amendment_identified_before_a_failed_inference_remains_blocked` | Papel histórico e formas textuais reconhecidas mantêm bloqueio; não comprova detecção de todo aditivo ou precedência jurídica |
| C11 — mudança documental | [test_extractions.py](../../tests/integration/test_extractions.py): `test_confirmed_source_change_removes_only_current_events`; [test_agenda.py](../../tests/integration/test_agenda.py): `test_changed_base_disappears_from_agenda_without_hiding_contract_or_deleting_history` | Testes de fluxo conservam histórico e retiram apenas eventos atuais desatualizados |
| C12 — tela antiga | [test_reviews.py](../../tests/integration/test_reviews.py): `test_document_change_invalidates_and_cannot_be_confirmed_from_old_screen` | Operação nova sobre a base antiga é rejeitada; replay de recibo não reativa eventos antigos |
| C13 — falha/interrupção/formato | [test_extractions.py](../../tests/integration/test_extractions.py): `test_failure_has_coverage_and_does_not_log_document_or_become_empty`, `test_incomplete_attempt_needs_explicit_interrupt_and_cannot_execute_again`, `test_invalid_output_coverage_fails_instead_of_persisting_empty`; [reprodução](../validacao-reproducao.md) | Falhas injetadas e recuperação explícita; encerrar registro não garante cancelamento do cálculo no runtime |
| C14 — resultado vazio | [test_extractions.py](../../tests/integration/test_extractions.py): `test_empty_result_requires_separate_empty_acknowledgment`; [test_reviews.py](../../tests/integration/test_reviews.py): `test_empty_requires_separate_declaration_and_is_not_a_failure` | Segunda declaração obrigatória; simulação não comprova ausência de outras obrigações no texto |
| C15 — localização e suporte semântico | [test_reviews.py](../../tests/unit/test_reviews.py): `test_invalid_evidence_is_rejected`, `test_evidence_location_does_not_prove_semantic_support` | **Limite explícito:** citação inexistente é rejeitada; citação literal sem sustentar o campo pode passar no levantamento manual. A conferência deve detectar o desacordo; não há avaliação semântica independente comprovada |
| C16 — instrução no documento | [test_local_classifier.py](../../tests/unit/test_local_classifier.py): `test_classifier_validates_without_network_and_returns_classifications_without_actions`; [demonstração DEV-008](../validacao-integracao-assistida.md) | Payload sem ferramentas/ações e retenção revisada na tela; DEV-008 permaneceu sem confirmação. Não é prova geral de resistência a instruções maliciosas |
| C17 — persistência parcial | [test_extractions.py](../../tests/integration/test_extractions.py): `test_confirm_failure_rolls_back_review_and_all_events`; [test_reviews.py](../../tests/integration/test_reviews.py): `test_confirmation_failure_rolls_back_review_events_receipt_and_audit` | Falha injetada reverte gravação de conferência/eventos; teste manual permite nova tentativa sem publicação parcial |
| C18 — limite de entrada | [test_documents.py](../../tests/unit/test_documents.py): `test_limits_count_raw_utf8_bytes_at_the_inclusive_boundary`; [test_extractions.py](../../tests/integration/test_extractions.py): `test_excess_input_is_rejected_before_reserving_or_sending` | Limite de recebimento e orçamento de contexto exercitados; excesso não vira truncamento silencioso |
| C19 — quatro grupos temporais | [test_agenda.py](../../tests/integration/test_agenda.py): `test_confirmed_notices_reach_all_four_temporal_groups_and_keep_equal_dates_separate`; [validação histórica](../validacao-agenda.md) | Integração de eventos confirmados por caminho manual, com os quatro limites da referência |
| C20 — seis situações de cobertura | [test_agenda.py](../../tests/integration/test_agenda.py): `test_mixed_portfolio_counts_every_contract_once_and_only_emits_current_reviewed_events` | Carteira mista com seis contratos, falha simulada e levantamentos manuais. Demonstração com modelo real mostrou duas situações; **não declarar C20 completo por essa demonstração** |
| C21 — resultado diferente na mesma base | [test_reviews.py](../../tests/integration/test_reviews.py): `test_new_result_invalidates_current_events_but_preserves_history`; [test_extractions.py](../../tests/integration/test_extractions.py): `test_context_review_is_persisted_and_requires_reconfirmation` | Seleção/correção diferentes demandam reconferência e preservam o anterior. Não houve demonstração de duas inferências reais divergentes na mesma base |
| C22 — número inválido/divergente | [test_literal_extraction.py](../../tests/unit/test_literal_extraction.py): `test_invalid_literals_are_blocked_instead_of_coerced` | Números negativos, fracionários e divergentes por extenso bloqueiam nos textos parametrizados |

## Lacunas que precisam de decisão

- **Qualidade semântica:** referência automática de 18/20 em desenvolvimento conhecido, antes de correções; não é taxa esperada em documentos novos. Se for exigida avaliação reservada, combinar critérios/protocolo e referências independentes antes de ajustar o método com esses exemplos.
- **Conferência manual:** decidir se o limite de C15 é aceitável para a apresentação do protótipo. Nome informado, declaração e histórico não autenticam a pessoa nem comprovam que leu o texto. Corrigir esse limite exige escopo próprio, sem atribuir identidade real às simulações.
- **Alcance da reprodução e demonstração:** outra pessoa/máquina, pesos recém-instalados e demonstração real dos seis grupos continuam sem comprovação. Vídeo não produzido; o [roteiro de demonstração](roteiro-demonstracao.md) é material para uma execução futura.
- **Produção/escala:** autenticação, assinatura, cancelamento do runtime, desempenho sob carga e escolha definitiva da IA não foram entregues. O [ADR-010](../adrs/010-ia-local-no-desenvolvimento.md) adia planejamento/seleção de produção; este roteiro não inicia M7 ou altera essa decisão.

## Revisar a cadeia de PRs

Na consulta de 04/11/2026, os 12 PRs estavam abertos, sem merge e com CI bem-sucedida nos HEADs registrados. O PR #12 estava em rascunho, sem submissões de revisão ou comentários de revisão registrados. O [snapshot remoto](../evidencias/retomada-2026-11-04.json) preserva branches, SHAs e execuções consultadas; não garante estado futuro. Os comentários gerais dos 12 PRs e as regras atuais de proteção da principal não foram auditados neste bloco.

Para revisar as dependências, seguir #1 → #12: fundação, regras/casos, documentos, conferência, agenda, guias, comparação offline, IA local, protocolo por linhas, retenções, integração assistida e materiais. Os PRs #7–#10 conservam experimentos e regressões; ler os limites antes de interpretar o resultado final. Cada descrição contém a evidência de sua versão.

Depois de cada integração que Lucas autorizar, reconferir base, diff e CI do próximo PR, conforme [governança](../governanca-repositorio.md). Uma CI antiga não certifica a versão retargetada. Nenhum merge ou mudança de base foi executado para preparar este roteiro.

## Registrar a decisão de Lucas

Os itens permanecem abertos; o agente não os marcou como aprovados:

- [ ] Revisar os limites, as evidências e os PRs e indicar eventuais correções.
- [ ] Conferir autoria e afirmações do cartão/textos.
- [ ] Escolher se alguma lacuna exige outro bloco de desenvolvimento ou demonstração.
- [ ] Se desejar publicar, indicar os canais e autorizar o envio; só depois registrar URLs reais e preparar a submissão autorizada.

Este roteiro não solicita autorização genérica para merge, posts ou produção. A próxima ação depende das decisões de Lucas acima; tarefas rotineiras de verificação/correção no escopo atual continuam autorizadas.

## Conferência deste bloco documental

Inspecionados os testes citados e confirmada a existência de 31 funções referenciadas. Os 22 resultados esperados da tabela da SPEC foram comparados com o snapshot `0ecf882` e permaneceram idênticos. Aplicação, scripts, dependências e testes também permaneceram iguais. `check_docs.py` aprovou 55 arquivos/421 referências locais, e `git diff --check` passou. Essas verificações conferem a documentação e sua rastreabilidade; não são nova execução da suíte ou aprovação semântica dos cenários. A descrição do PR #12 identifica o HEAD e a CI finais após a publicação deste bloco.
