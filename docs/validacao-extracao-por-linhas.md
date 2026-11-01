# Validação da extração por linhas

01/11/2026. Base: `2ecc473b9b40aaa3c06982788989f8e90413c820`; decisão no [ADR-011](adrs/011-classificacao-de-linhas-e-interpretacao-literal.md). Commit e CI finais serão vinculados no PR. Mesmo Ollama 0.40.13, Qwen3 4B Instruct Q4 e digest da rodada V2; nenhuma escolha de produção.

## O que mudou e como foi verificado

Testes novos em [test_literal_extraction.py](../tests/unit/test_literal_extraction.py) e [test_line_local_ai.py](../tests/unit/test_line_local_ai.py). A regressão completa executou **272 testes aprovados**, incluindo os 242 anteriores; Ruff, formatação e lock/dependências aprovados.

| Comportamento | Cenário/resultado esperado | Evidência |
|---|---|---|
| Gramática literal | Dias sem unidade, úteis, meses, número negativo/fracionário e extenso divergente bloqueiam; não são convertidos | `test_invalid_literals_are_blocked_instead_of_coerced`, 6 variantes |
| Valores expressos e cálculo existente | Zero, sinal positivo e extenso concordante preservados; bissexto usa cálculo do domínio existente | `test_literal_zero_positive_sign_and_same_written_number_are_supported` |
| Âncora | Outro evento ou ausência de término explícito impedem candidatos | `test_other_anchor_and_missing_end_date_block_without_partial_events` |
| Conflitos | Datas/antecedências concorrentes preservadas e bloqueadas; intervalos mantêm linhas vazias | `test_date_conflict_preserves_facts_and_literal_span_including_empty_lines`, `test_conflicting_rules_in_combined_lines_are_blocked` |
| Data impossível | Pendência explícita em vez de valor normalizado falso | `test_impossible_date_is_domain_blocker_instead_of_normalized_fake_date` |
| Aditivo | Papel declarado ou declaração afirmativa não pode ser removido por label/abstenção; negação não é declaração | `test_declared_amendment_cannot_be_hidden_by_context_label_or_abstention`, `test_explicit_amendment_is_guarded_without_treating_negation_as_declaration` |
| Suporte/contexto | Exemplo e pagamento não são término; label contexto/ausência sem suporte não libera; prefixo de metadado com condição literal é retido | Três testes de ilustração, linha relevante e prefixo de metadado |
| Cobertura de linhas | Exigir exatamente as linhas não vazias, sem origem duplicada/ausente ou chave JSON repetida; preservar numeração original | Testes de origem/cobertura/chaves duplicadas nos dois arquivos |
| Repetição de regra | Aviso idêntico não duplica candidato e conserva registro da fonte adicional | `test_repeated_notice_keeps_one_candidate_and_additional_source_record` |
| Schema e entrada múltipla | Schema no decoder e no prompt, sem valores/eventos de saída; aditivo completo cabe sem truncar | `test_dynamic_schema_requires_all_nonempty_lines_and_is_grounded_in_prompt`, `test_existing_multidocument_case_fits_without_truncating_sources` |
| Proveniência | Código monta citação da origem; observação separa classificação e normalização | `test_evidence_is_assembled_from_source_and_observation_separates_model_and_code` |
| Continuidade da rodada | Progresso, hashes e contagens registrados; interrupção não vira conclusão e impede repetição silenciosa | Testes de rodada completa e interrompida no runner |

A primeira checagem de estilo encontrou nomes de variável ambíguos; corrigidos. A expansão inicial do schema ultrapassou o orçamento de contexto do caso com dois documentos; schema passou a compartilhar o enum por referência local, com teste explícito da entrada completa. Limite não foi aumentado nem texto truncado.

## Operação real

Smoke com quatro casos: DEV-001, DEV-002 e DEV-004 corresponderam ao gabarito; DEV-020 preservou o término real como fato e reteve a publicação por guarda conservadora após classificação do exemplo como condição. Não houve falha técnica nesses quatro casos.

Rodada V1 real de 20 casos concluída por `Avaliar-IA-Local.ps1 -Metodo linhas`; [JSON completo](evidencias/ia-local-linhas-v1.json) preservado e estado parcial marcado como concluído. Fontes/componentes e catálogo conferidos; nenhuma mudança de fonte durante a rodada.

Resultado V1: 18/20 correspondências integrais, 0 falhas técnicas, 29 fatos corretos/0 indevidos/0 omitidos; 10 candidatos corretos/0 indevidos/3 omitidos. Todos os 11 casos com impedimento tiveram bloqueio reconhecido. DEV-008 e DEV-020 receberam retenção extra `unsupported_scope`, omitindo respectivamente 2 e 1 candidatos. O primeiro foi classificado como unsupported pelo modelo; no segundo, a guarda reteve uma condição de exemplo classificada como término. Não remover as guardas para esconder essas retenções.

Mediana V1 4,924 s/caso, máximo 8,027 s, extração + pontuação. V2 anterior tinha 19 candidatos indevidos e 3 falhas; esta é melhora da combinação de classificação/interpretação neste desenvolvimento, sem avaliação independente.

**Próximo ajuste do bloco:** preservar o snapshot V1 e esclarecer no prompt o papel de pedidos ao assistente e condições ilustrativas. Rodada posterior terá prompt versionado, sem mudança de modelo, gabarito ou guardas.

## Limites

As 20 anotações continuam visíveis e usadas no desenvolvimento; sem avaliação reservada ou revisão humana independente. O modelo não foi trocado. Citações agora são montadas pelo código, portanto a ausência de citação literal inválida não mede a capacidade da IA de transcrever uma fonte. A taxa representa o fluxo combinado, não o modelo sozinho.

Gramática limitada a formatos/âncoras explícitos; datas por extenso, duração em palavras fora do suporte, conteúdo multilinha ou contexto ambíguo podem gerar retenção. Reconhecimento lexical e classificação de todas as linhas não provam completude semântica. A aplicação permanece manual; sem migração, confirmação automática ou C20 completo.
