# Validação da IA local

01/11/2026. Base: `40a69cde2351b435dcbb37b3a61fdf741d8c7473`. [Decisão](adrs/010-ia-local-no-desenvolvimento.md) e [operação](ia-local.md). Commit/CI finais devem ser vinculados na descrição do PR. Não há integração à aplicação nesta entrega.

## Operação real observada

- Hardware consultado: cerca de 28 GB de RAM e NVIDIA RTX 3050 Laptop com 4 GB de VRAM. Sem runtime disponível nos caminhos/portas inicialmente conferidos.
- Pacote Ollama 0.40.13 baixado da release oficial; SHA-256 comparado antes de extrair/executar. Pesos do Qwen3 4B Instruct Q4 baixados pelo runtime; digest completo conferido com o modelo carregável local.
- Servidor iniciado em processo identificado, somente em 127.0.0.1:11435. Log confirmou nuvem desabilitada e seleção da GPU NVIDIA via Vulkan. Não foi instalado/atualizado driver ou serviço do Windows.
- `Preparar-IA-Local.ps1` executado para reutilizar runtime/modelo já preparados, sem criar servidor duplicado ou repetir download. Download/extrair iniciais foram feitos por comandos de preparo nesta sessão; o caminho de primeira instalação desse script ainda não foi exercitado em uma máquina limpa.
- Smoke real com prompt V1 em DEV-001 e DEV-020 encontrou omissão da regra de aviso e uso de exemplo como término. O prompt foi esclarecido, sem trocar modelo; V2 passou no caso simples. Essas amostras pertencem ao desenvolvimento e foram usadas para ajuste.
- Rodada real de 20 casos executada por `Avaliar-IA-Local.ps1`, sem chamar API externa: 20 requisições locais de inferência e 2 de metadados. [Relatório preservado](evidencias/ia-local-v2.json), com hashes do método/avaliador/entradas conferidos antes de versionar.
- Resultado: 6/20 correspondências integrais, 3 falhas técnicas, 23 fatos corretos/11 indevidos/6 omitidos; 11 candidatos corretos/19 indevidos/2 omitidos. Dos 11 casos com impedimento anotado, 9 retornaram sem reconhecer o bloqueio e 2 foram rejeitados. Não recomendar integração desta versão à aplicação.
- Falhas reais rejeitadas: DEV-004 e DEV-019 por citação não literal; DEV-011 por data inválida. As respostas inválidas não viraram análise vazia. O JSON guarda código da falha, sem o corpo bruto da resposta.
- Mediana de extração mais pontuação: 11,180 s/caso; máximo 16,875 s nesta rodada. Não é tempo de revisão humana, capacidade sob carga ou benchmark de produção.
- A primeira saída dos scripts apresentou acentuação incorreta no Windows PowerShell 5.1; os arquivos passaram a UTF-8 com BOM e a reutilização foi reexecutada com texto correto. A falha do experimento produz saída de erro e preserva JSON; o wrapper agora informa o destino antes de iniciar e recusa destino existente/diretório ausente antes de qualquer inferência.

## Testes por comportamento

Testes em [test_local_ai.py](../tests/unit/test_local_ai.py), com transporte simulado e sem dependência de modelo/rede na CI:

| Comportamento | Evidência |
|---|---|
| Apenas loopback literal, sem credenciais/caminhos | `test_endpoint_rejects_nonliteral_loopback_and_extra_parts`, 8 variantes |
| Documentos/schema, sem gabarito ou ferramentas | `test_local_success_sends_only_documents_schema_and_no_actions` |
| Corte, modelo diferente, contexto não verificado e solicitação de ferramenta | `test_truncation_different_model_unverified_context_and_tools_fail`, 7 variantes |
| Datas inválidas ou não normalizadas | `test_invalid_or_nonnormalized_dates_fail`, 5 variantes |
| Evidência literal e campos extras | `test_nonliteral_evidence_and_extra_confirmation_are_rejected` |
| Antecedência sem coerção | `test_invalid_notice_days_are_not_coerced`, 4 variantes |
| Vazio e abstenção distintos, sem confirmação | `test_empty_and_abstention_are_distinct_and_neither_confirms` |
| Excesso de entrada sem truncar/enviar | `test_oversized_prompt_fails_without_sending_or_losing_observation` |
| Versão, formato local e digest | `test_model_digest_format_and_runtime_version_are_checked` |
| Timeout sem vazio ou mensagem documental no relatório | `test_timeout_does_not_turn_into_empty_or_store_document_message` |
| Envelope inválido/limite de resposta | `test_http_bounds_and_invalid_response_are_rejected`, 3 variantes |
| Redirect não seguido | `test_http_rejects_redirects_without_reading_or_following_target` |

Os dois scripts também passaram pela análise de sintaxe. Destino existente e diretório ausente foram testados no wrapper: ambos rejeitados antes de qualquer geração; hash do relatório e contagem de gerações permaneceram iguais.

Os 50 testes focados iniciais passaram; adicionadas três variantes de limite/envelope, totalizando 34 casos novos da fronteira local. **242 testes passaram na regressão completa**, com Ruff, formatação, lock/dependências e 41 arquivos/269 links locais aprovados. A CI remota será vinculada ao HEAD final no PR. O avaliador compartilhado passou a distinguir hash do método de hash do avaliador e não atribui custo/contagem zero a um callback desconhecido. O runner local registra sua contagem de requisições HTTP, sem afirmar ausência de chamadas quando houve inferência local.

A evidência real não representa avaliação independente: os 20 casos são desenvolvimento visível, com ajuste do prompt no caso simples. O método local teve precisão de candidatos 11/30 (36,7%), abaixo de 11/18 (61,1%) do baseline por regras no mesmo conjunto. Essa observação não compara famílias de modelos nem autoriza adotar qualquer um dos dois métodos. Não declarar revisão independente, conjunto reservado, qualidade de produção ou C20 completo. Dados, anotações e ajuste foram feitos nesta sessão pelo próprio agente; revisão humana real de Lucas não foi executada.
