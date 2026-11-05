# ADR-008 — Agenda de consulta e cobertura da carteira

01/11/2026 · Implementação no escopo autorizado por Lucas, sujeita à revisão do PR. Detalha a agenda prevista no PRD/SPEC; não altera a regra AVISO_CORRIDOS_V1 nem autoriza comunicação externa.

## Contexto

O caminho manual já registra candidatos, calcula aviso e confirma uma base explícita. A próxima tarefa é decidir quais datas merecem atenção e quais contratos continuam pendentes. Uma lista vazia após aplicar um filtro não pode ser apresentada como carteira conferida.

## Decisão

- Criar uma projeção de consulta, separada das operações de escrita. Uma única instrução SELECT com junções externas lê os metadados de todos os contratos, a revisão/levantamento selecionados, a conferência e os eventos associados. Não carregar bytes, referências textuais ou payloads de análise de toda a carteira.
- Publicar na agenda somente eventos de análise atual, revisão atual e regra atual, com conferência, sem impedimento/aditivo conhecido e com quantidade de eventos consistente com o levantamento. Conferência inconsistente fica pendente; não publicar um subconjunto. Histórico anterior não é apagado.
- Mostrar todos os contratos em situações exclusivas e com próximo passo: aguardando documentos, aguardando análise, revisão pendente, bloqueado, conferido com eventos e conferido sem eventos no recorte. A soma sempre corresponde ao total registrado nessa leitura.
- Manter a cobertura independente dos filtros da agenda. Filtros vazios e referência apagada não ocultam os contratos. Erro de consulta produz indisponibilidade explícita, sem inventar cobertura zero.
- Usar referência de simulação editável, inicialmente 01/05/2027 para reproduzir os exemplos. Ela é estado da interface, sem gravar ou alterar confirmações. Nova sessão retorna ao padrão. Não usar implicitamente o relógio da máquina.
- Aplicar a classificação de datas existente: anterior à referência, hoje, dias 1 a 30 inclusive e depois do horizonte. Horizonte fixo de 30 dias; filtro inicial inclui os três primeiros. Datas passadas permanecem acessíveis. Filtrar também por término ou aviso, mantendo eventos de tipos diferentes na mesma data.
- Ordenar por data, nome do contrato e identificadores/tipo como desempate estável. Exibir dias até a data, sem declarar descumprimento, quitação ou ação realizada.
- Permitir consultar a origem de um evento exibido, carregando somente o levantamento escolhido e revalidando a base antes de mostrar a evidência. A leitura não é uma atualização em tempo real: uma mudança externa exige nova interação/atualização, e a consulta de origem sinaliza mudança ocorrida depois da projeção.

## Alternativas e consequências

Consultar cada contrato por chamadas separadas reutilizaria os serviços anteriores, mas criaria várias leituras e poderia combinar instantes diferentes na cobertura e nos eventos. Uma tabela adicional de agenda exigiria sincronização e invalidação duplicadas. A projeção única evita ambas nesta base local, sem nova migração.

A consulta usa as junções e subconsulta EXISTS documentadas pelo [SQLAlchemy](https://docs.sqlalchemy.org/en/21/core/selectable.html); o teste verifica a instrução efetivamente executada, sem tratar documentação como prova de execução. A interface usa a [entrada de data do Streamlit](https://docs.streamlit.io/develop/api-reference/widgets/st.date_input).

A projeção carrega os metadados completos da carteira em memória. Ainda não foram medidos volume máximo, tempo sob carga ou necessidade de paginação. Logs técnicos registram contagens e duração, sem nome de contrato ou texto documental. Essa instrumentação não representa uma meta de desempenho validada.

As seis situações desta entrega descrevem o caminho manual atual. Não existe execução de extrator nem estado persistido de falha de análise; C20 completo, que exige essas situações futuras, continua pendente. Falha de leitura da carteira é erro da consulta, sem ser convertida em análise vazia.

## Evidências

[Validação e matriz por funcionalidade da agenda](../validacao-agenda.md). A revisão real de Lucas continua distinta dos testes e da demonstração com a conferência simulada anterior.
