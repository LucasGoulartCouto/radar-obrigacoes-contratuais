# ADR-013 — Execução persistida e conferência assistida local

02/11/2026. **Decisão técnica implementada no escopo autorizado de integração de desenvolvimento.** Aplicam-se os ADRs [002](002-proposta-limites-extracao-e-confirmacao.md), [006](006-entrada-e-revisoes-documentais.md), [007](007-levantamento-manual-e-conferencia.md) e [012](012-revisao-restrita-de-retencoes.md). [Validação](../validacao-integracao-assistida.md) liga comportamentos a testes, migração e demonstração real com revisão simulada. Não é seleção de IA de produção.

## Fluxo e identidade

Separar **solicitar/executar**, **escolher resultado para conferência** e **confirmar**. Inferência não tem ferramentas de negócio. Usa o mesmo protocolo V1, modelo provisório fixado por digest e loopback, com validação de entrada/contexto e orçamento de 120 s compartilhado pelas requisições locais, sem retry automático. O timeout é de transporte; não é cancelamento garantido do cálculo no runtime. Entrada excessiva é rejeitada antes de reservar/enviar, sem truncamento.

Uma solicitação cria tentativa durável pendente; disputa atômica permite somente um executor mudar de pendente para em processamento. Rede ocorre fora da transação de escrita. Conclusão, falha ou interrupção ficam vinculadas ao contrato/revisão, versão do levantamento no início, hash dos documentos, método/prompt/interpretador/regra, modelo/digest, parâmetros e duração. Exceções/documentos não vão para logs técnicos. Falha não se transforma em vazio. Abstenção conserva bloqueio de leitura incompleta.

Resultado tardio de revisão antiga é preservado na tentativa, mas não pode ser selecionado. Se o levantamento mudou durante a execução, um resultado diferente exige nova tentativa; não substitui o atual. Nova tentativa idêntica pode reutilizar o levantamento selecionado e sua conferência, preservando a tentativa adicional. Alteração de contexto no mesmo resultado selecionado exige justificativa, outra versão e reconferência.

## Seleção e confirmação

Selecionar compara revisão documental, levantamento e método dentro da escrita. Diferença na mesma base exige justificativa. O método selecionado é `ASSISTED_LOCAL_LINES_V1`; a tabela física histórica `manual_analyses` passa a abrigar ambos os métodos sem renomear/perder registros. A migração aditiva 0004 identifica os registros anteriores como `MANUAL_V1` e acrescenta tentativas e sinalização de aditivo textual.

A proposta é reconstruída pelo código a partir de todas as linhas/classificações, nunca de fatos normalizados editáveis do modelo ou gabarito. Evidências recebem documento/hash/normalizador/posição/linhas. Datas são calculadas por `AVISO_CORRIDOS_V1`, sem mudança semântica. O recibo de contexto do ADR-012 é guardado com antes/depois e responsável simulado; não é convertido silenciosamente em método manual.

Confirmar é outra operação: revalida execução, método, origem, interpretação, decisões de contexto e regra, compara payload/fingerprint e grava conferência/eventos/recibo/histórico atomicamente. Vazio exige segunda declaração. Selecionar outro resultado não reativa conferência antiga; reenviar recibo não muda a seleção atual. Métodos/regras desatualizados deixam de compor a agenda. Versionar alterações semânticas continua obrigatório.

## Aditivos e recuperação

Papel de aditivo no histórico continua bloqueado. Declaração textual afirmativa reconhecida pelas guardas do interpretador também é preservada como conhecimento do contrato na reserva da tentativa, independentemente de sucesso da IA. Retirar ou mudar o papel do arquivo não apaga esse conhecimento. Não há mecanismo para liberar/consolidar aditivo neste recorte. O reconhecimento é limitado às formas suportadas; não prova ausência de outros aditivos.

Tentativa pendente/em processamento após interrupção é exibida, sem inferência em recarregamento. Operador encerra explicitamente o registro incompleto e solicita nova tentativa, preservando a anterior. Isso não cancela um cálculo ainda em execução no runtime. Conclusão posterior de tentativa encerrada é rejeitada, sem selecionar resultado. Se a persistência final falhar, a tentativa continua incompleta e recuperável; não inventar resultado vazio.

Uma tentativa não selecionada, inclusive falha, não desfaz uma conferência válida da mesma base. Sem levantamento selecionado, a última tentativa da revisão atual determina andamento/falha/resultado aguardando escolha. Esta regra evita substituir um resultado conferido por uma tentativa exploratória sem decisão explícita.

## Cobertura e limites

Alinhar a projeção aos seis grupos da SPEC: bloqueado, falha, aguardando análise, revisão pendente, conferido com eventos e conferido sem eventos. Falta de documentos é detalhe de aguardando análise, permanecendo explícita na carteira e na entrada documental. A enumeração antiga mantém alias para compatibilidade, sem duplicar a contagem. Consulta de carteira continua uma única leitura de metadados, sem carregar textos; filtros não alteram cobertura. Aditivo conhecido tem precedência sobre falha.

Interface oferece texto completo/contexto, candidatos, histórico de tentativas, encerramento explícito e revisão restrita de contexto. Ambiente sem modelo configurado mantém o caminho manual. Identidades são personagens de simulação, sem autenticação/assinatura. Não há worker distribuído, cancelamento de inferência, benchmark de escala, avaliação reservada ou revisão real de Lucas. Cada capacidade precisa de evidência própria; CI verde não valida qualidade semântica geral.

**Correção de implementação em 04/11/2026:** as leituras também comparam o método registrado na execução selecionada ao método atual. Migração 0005 acrescenta a referência da análise à execução como metadado, sem reescrever payloads anteriores. Uma nova tentativa com método diferente não reaproveita conferência antiga só por propor as mesmas datas. [Regressões, atualização com preservação de dados e limites](../validacao-validade-do-metodo.md). É aplicação das invariantes acima, sem alteração da regra de datas, do prompt ou do interpretador.

Fontes primárias reabertas em 02/11/2026: [SQLAlchemy — transações de sessão](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#framing-out-a-begin-commit-rollback-block), [Ollama — saída estruturada](https://docs.ollama.com/capabilities/structured-outputs) e [Streamlit — status](https://docs.streamlit.io/develop/api-reference/status/st.status). As fontes orientam mecanismos; testes/demonstrações identificam o alcance executado.
