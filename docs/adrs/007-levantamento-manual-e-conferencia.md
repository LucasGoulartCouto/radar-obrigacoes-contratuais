# ADR-007 — Levantamento manual e conferência vinculada à base

01/11/2026 · **Implementado no escopo escolhido por Lucas: avançar para candidatos e conferência.** O ADR-002 continua definindo a separação entre sugestão, cálculo e confirmação.

## Decisão

Começar pelo levantamento manual referenciado (`MANUAL_V1`): o operador informa os campos e seleciona trechos do texto de referência. O código valida a localização literal e calcula o aviso pela regra `AVISO_CORRIDOS_V1`. Salvar esse levantamento cria candidatos pendentes; a confirmação é uma operação distinta.

A localização verifica documento, normalizador, linhas e citação literal. **Ela não prova que o trecho sustenta o valor informado.** A conferência deve avaliar o significado, o contexto e a cobertura do texto completo. O primeiro método não extrai cláusulas nem detecta automaticamente conflitos ou aditivos ocultos. Impedimentos identificados pelo operador são registrados com motivo e evidência; unidade ou referência de aviso não suportada também bloqueiam confirmação. Aditivo conhecido continua bloqueado.

## Base e identidade

- `document_version` identifica a revisão documental e `analysis_version` identifica o levantamento selecionado; ambos são separados da edição do nome do cadastro.
- Cada levantamento é imutável e registra revisão documental, dados informados, evidências com identificador do documento/hash/linhas, método, regra, operador e instante.
- Novo resultado diferente na mesma revisão exige justificativa da correção, preserva o anterior e demanda nova conferência. A justificativa não substitui evidência.
- Resultado idêntico para a mesma revisão e regra reutiliza o levantamento atual e conserva a conferência existente. Repetir uma operação reutiliza o recibo, sem novos eventos de negócio.
- A confirmação compara revisão, levantamento e regra exibidos com a base atual dentro da escrita. Revalida os campos e as citações, exige declaração explícita de conferência e rejeita impedimentos.
- Resultado vazio exige uma segunda declaração sobre a ausência de eventos no recorte. Não é falha técnica nem uma afirmação de ausência de toda obrigação contratual.

## Persistência e invalidação

A migração `0003_reviews` cria levantamentos, conferências e eventos confirmados e acrescenta o contador do levantamento ao cadastro. Conferência, eventos, recibo e histórico são gravados na mesma transação. Uma falha desfaz todo o conjunto.

A visão atual consulta apenas eventos cujo levantamento, revisão documental e versão de regra ainda coincidem com os do contrato. Alterar documento ou selecionar resultado diferente faz os eventos anteriores desaparecerem dessa visão, mantendo-os acessíveis no histórico. Não apagar o histórico nem reativar um resultado antigo por reenvio de recibo.

A versão da regra é explícita: ao mudar sua implementação ou interpretação, atualizar a versão e verificar a reconferência. O sistema não detecta uma alteração de código que mantenha indevidamente a mesma identificação de regra. Esse controle depende dos testes e da disciplina de alteração.

## Interface e limites

A interface mostra candidatos, campos e evidências antes da ação separada de confirmação. Corrigir o levantamento gera outro registro; não altera o anterior. A atualização explícita dos documentos também atualiza os rascunhos da conferência para evitar ações sobre uma base antiga. Texto de origem e justificativas são exibidos como dados.

O responsável informado é um personagem da simulação. Não há autenticação, assinatura nem revisão independente comprovada. O agente realizou a demonstração com os personagens Rafael e Marina; isso não significa que Lucas ou outra pessoa já revisou os resultados ou os PRs.

Esta entrega inclui a lista de eventos conferidos da base atual. Agenda temporal com referência/horizonte, filtros e cobertura completa das execuções de análise são etapas seguintes. Não há chamada de IA, custo de API ou comunicação com fornecedores.

## Alternativas e consequências

Confirmar na mesma ação de cadastro reduziria cliques, mas eliminaria a distinção aceita entre sugestão e decisão. Editar um resultado confirmado no lugar dificultaria reconstruir a origem. Apagar eventos ao mudar a base perderia o histórico. Por isso usamos registros imutáveis, operação separada e seleção da base atual na consulta.

O custo é manter versões e exigir nova conferência após mudanças relevantes. Este baseline permite comparar futuramente o esforço e os erros de uma extração automática com um fluxo manual rastreável.

Evidências: [validação da conferência](../validacao-conferencia-manual.md). Referências consultadas em 01/11/2026: [SQLAlchemy — transações de sessão](https://docs.sqlalchemy.org/en/21/orm/session_basics.html#framing-out-a-begin-commit-rollback-block) e [Streamlit — entrada de datas](https://docs.streamlit.io/develop/api-reference/widgets/st.date_input).
