# PRD — Radar de Obrigações Contratuais

Versão 0.5 · 01/11/2026 · Requisitos detalhados em revisão de produto.

**Estado verificado em 02/11/2026:** a [integração assistida local](validacao-integracao-assistida.md) e a [reprodução em ambiente/banco novos](validacao-reproducao.md) foram exercitadas. As seções de progresso anteriores abaixo descrevem seus snapshots históricos; não são a pendência atual do extrator. Os requisitos propostos continuam separados dos aceites de Lucas e dos limites de validação independente.

**Decisões aceitas por Lucas:** construir o case fictício da Agência Prisma com foco em renovações e avisos prévios em contratos de serviços com fornecedores; separar sugestão com evidências, cálculo por código e confirmação humana, com bloqueio por unidade ambígua, conflito ou aditivo, conforme ADR-002. Os demais detalhes, limites e metas deste documento são propostas. Ainda não houve validação com usuários reais.

**Arquitetura e ferramentas aceitas:** aplicação local modular e ferramentas dos ADRs 003/004. A [fundação](validacao-fundacao.md), a [entrada documental](validacao-entrada-documental.md), o [fluxo manual de conferência](validacao-conferencia-manual.md) e a [agenda com cobertura](validacao-agenda.md) foram implementados. Este PRD continua descrevendo o produto completo: extração automática e estados de execução do extrator ainda não foram implementados. A [proposta posterior de evolução](evolucao-arquitetural.md) permanece planejada.

## 1. Problema e resultado pretendido

No case fictício, a Agência Prisma copia datas de contratos para uma planilha. A diretora Marina Costa precisa decidir sobre fornecedores antes dos prazos previstos, enquanto Rafael Lima, analista administrativo, prepara os dados e confere alterações.

O Radar deverá ajudar Rafael a responder: **quais contratos merecem atenção, qual informação sustenta essa prioridade e quais análises ainda estão incompletas?** A hipótese de valor é reduzir trabalho de conferência e tornar omissões mais visíveis. Economia de tempo e redução de perdas ainda não foram medidas.

Uma data de término e uma data-limite de aviso são eventos diferentes. Acompanhá-las não determina se a agência deve cancelar, se houve descumprimento ou se uma manifestação teria validade jurídica.

## 2. Primeira tarefa que queremos demonstrar

Com uma data de referência de simulação explícita, Rafael registra um pequeno conjunto de contratos sintéticos, analisa os candidatos encontrados, confere as evidências e consulta os itens confirmados que exigem atenção nos próximos 30 dias. Na mesma visão, identifica os contratos com falha, ambiguidade ou revisão pendente.

O resultado não pode apresentar a carteira inteira como conferida quando há contratos pendentes. Marina decide o que fazer com os fornecedores fora do sistema; o projeto apenas simula esse contexto.

## 3. Escopo proposto

| Incluído | Limite da primeira versão |
|---|---|
| Cadastro de contratos e documentos | Um negócio fictício; texto UTF-8 sintético; documentos identificados por contrato e versão |
| Leitura de marcos do ciclo informado | Data explícita de término e, quando houver, aviso de não renovação vinculado a esse término |
| Extração com evidências | Campos candidatos com trechos e origem; método de extração ainda a escolher |
| Cálculo verificável | Subtração de quantidade inteira não negativa de dias corridos de uma data explícita, conforme convenção do case |
| Revisão humana | Conferir, corrigir com evidência, confirmar, rejeitar ou manter pendência; registrar autoria e motivo |
| Agenda interna | Somente eventos confirmados da revisão atual; data de referência e horizonte visíveis |
| Cobertura e histórico | Todos os contratos registrados continuam visíveis, inclusive os que não produziram candidatos |
| Reanálise | Repetição sem duplicações e invalidação de confirmação quando a base revisada mudar |
| Aditivos e textos não suportados | Detectar/registrar sua presença no conjunto declarado e manter a análise pendente; consolidação de efeitos fora da versão inicial |

Ficam fora: documentos reais, PDF/OCR, pagamentos e outras famílias de obrigação, parecer jurídico, regras legais de contagem, dias úteis, consolidação automática de aditivos, ciclos futuros inferidos, assinatura, cancelamento e comunicações externas. Hospedagem pública e operação de várias empresas não são requisitos desta primeira versão.

## 4. Requisitos e critérios de aceitação

| ID | Requisito | Critério verificável |
|---|---|---|
| RF-01 | Registrar a base documental | Cada documento pertence a um contrato e a uma revisão identificada; repetição idêntica não cria novo evento de negócio |
| RF-02 | Preservar a evidência | Cada campo extraído aponta para texto verificável na revisão analisada; citação inexistente impede confirmação |
| RF-03 | Calcular datas pelo case | Exemplo com término 30/06/2027 e antecedência de 30 dias corridos resulta em 31/05/2027, com entradas e regra exibidas |
| RF-04 | Expor incerteza e limites | Unidade ausente, conflito, evento desconhecido, aditivo ou falha produzem pendência visível, sem data confirmada para o caso |
| RF-05 | Conferir antes de publicar | Nenhum candidato entra automaticamente na agenda; confirmação exige base atual, dados válidos e registro de revisão |
| RF-06 | Tratar alterações | Nova revisão, mudança de regra ou seleção de resultado diferente torna a confirmação anterior desatualizada; o contrato aparece para reconferência |
| RF-07 | Mostrar agenda e cobertura | Eventos confirmados são separados de pendências; contratos sem candidato e contratos com falha têm situações distintas |
| RF-08 | Repetir e recuperar | Repetição de entrada não duplica contrato/evento; execução interrompida permanece identificável e pode ser refeita |
| RF-09 | Explicar o histórico | É possível reconstruir origem, regra, método, revisão humana e substituição de cada resultado |
| RF-10 | Respeitar o contexto de simulação | Documentos não comandam ferramentas; não há integração para enviar avisos, assinar ou movimentar valores |

Regras completas e cenários: [SPEC do primeiro fluxo](specs/001-primeiro-fluxo.md).

## 5. Medição e critérios de entrega

As metas abaixo são propostas de aceitação, não resultados alcançados.

| Medição | Como vamos avaliar | Critério proposto |
|---|---|---|
| Correção das regras determinísticas | Casos esperados de cálculo, elegibilidade e mudança de revisão | Todos os cenários obrigatórios da SPEC devem passar antes da demonstração |
| Rastreabilidade | Verificação dos campos confirmados e do vínculo com a base revisada | Nenhum evento confirmado sem evidências, revisão atual e histórico |
| Cobertura | Contagem de contratos por situação em cada etapa | A soma das situações exclusivas deve fechar com o total registrado |
| Extração automática | Eventos encontrados, falsos positivos, omissões e campos corretos, antes da revisão | Relatar numeradores, denominadores e resultados por tipo; limiar para adoção de IA será definido após o experimento inicial e antes da avaliação reservada |
| Efeito da revisão | Comparação entre extração inicial e resultado conferido | Correções humanas identificadas separadamente dos acertos automáticos |
| Esforço de uso | Tarefa manual simulada e tarefa com o Radar no mesmo conjunto | Medir tempo/correções se houver condições comparáveis; nenhuma promessa de ganho antecipado |
| Reprodutibilidade | Execução a partir de instalação limpa e dados sintéticos versionados | Outra pessoa consegue repetir o roteiro seguindo o README |

Plano inicial de avaliação: 30 casos sintéticos, sendo 20 de desenvolvimento e 10 reservados para avaliação. Tamanho e distribuição ainda serão ajustados ao esforço. As respostas esperadas serão justificadas independentemente do extrator. O conjunto reservado não será usado para ajustar regras ou prompts; se for inspecionado para ajuste, deixa de ser reservado e precisará ser substituído.

**Material inicial em 01/11/2026:** [oito casos de desenvolvimento e nove documentos](../tests/fixtures/contracts/README.md), com gabarito e citações literais. Nenhum caso reservado foi preparado nesta entrega. Os testes de integridade desse conjunto não medem qualidade de extração nem verificam o fluxo documental completo.

**Experimento inicial em 01/11/2026:** desenvolvimento ampliado para 20 casos/21 documentos; [baseline offline medido](comparacao-extracao.md), com falhas explícitas e sem recomendação de integração. Nenhum caso reservado ou execução de IA nesta etapa. Limiar de adoção, fornecedor e orçamento continuam sujeitos à decisão de Lucas.

## 6. Condições não funcionais

- Preservar documentos e resultados anteriores sem sobrescrever silenciosamente a origem da revisão.
- Identificar execução, contrato, revisão, método de extração e versão da regra nas operações relevantes.
- Registrar tempos por etapa e tamanho/volume das entradas para apoiar o diagnóstico e a futura proposta de evolução; metas definitivas de desempenho ainda não foram fixadas.
- Exibir erros de forma útil e manter detalhes técnicos fora do fluxo principal do usuário.
- Limitar tamanho das entradas e tentativas de processamento; limites concretos serão fechados antes da implementação.
- Não truncar documentos silenciosamente. Entrada não processada integralmente deve permanecer incompleta.
- Manter credenciais fora do repositório; nenhum segredo pode integrar o contexto enviado a um extrator.
- Registrar o usuário/revisor do cenário sem alegar autenticação ou auditoria inviolável que ainda não tenham sido implementadas.

Os [limites operacionais da entrada](decisoes-primeiro-fluxo.md) foram implementados com rejeição explícita de tamanho e quantidade. O [registro documental](validacao-entrada-documental.md) distingue origem/versionamento das funcionalidades ainda futuras. Prazo de processamento, política de tentativas e orçamento continuam em aberto para a integração do extrator.

## 7. Prioridade e exclusões em caso de prazo apertado

O fluxo de registro → evidência → cálculo → revisão → agenda é a prioridade. Podem ser reduzidos: quantidade de cenários, filtros, exportações, acabamento visual e adoção de IA. Permanecem necessários: pendências visíveis, cálculo correto, vínculo com a revisão atual e separação entre sugestão e confirmação.

Disponibilidade informada por Lucas: **mais de 10 horas por semana**. Orçamento, limite superior de esforço e objetivo prioritário do desafio ainda precisam ser definidos. O calendário do [planejamento](planejamento-inicial.md) permanece provisório.

## 8. Questões ainda abertas

1. Qual será o orçamento para uma eventual API de IA? Hospedagem não é requisito da base local escolhida.
2. A interface escolhida atende ao futuro fluxo de revisão documental, além do cadastro já verificado?
3. Uma extração com IA melhora o resultado ou o esforço de revisão em relação à alternativa simples?
4. Quais limites de entrada e tempo de execução fazem sentido no ambiente escolhido?
5. Quais metas de extração serão exigidas depois do experimento inicial?

O histórico de escolha do recorte está no [ADR-001](adrs/001-recorte-do-produto.md). A [arquitetura](arquitetura.md) distingue escolhas aceitas de detalhes e verificações ainda pendentes.
