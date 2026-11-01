# Plano de entrega — proposta para o primeiro fluxo

31/10/2026 · Disponibilidade informada: mais de 10 horas por semana. Ainda não há estimativa validada de esforço nem orçamento definido. As janelas do [planejamento inicial](planejamento-inicial.md) são provisórias.

## Marcos e ordem de dependência

| Marco | Trabalho | Evidência para concluir |
|---|---|---|
| M0 — Discovery e recorte | Case, tarefa principal, medos e exclusões | Recorte aceito no ADR-001; hipóteses e limites da simulação identificados |
| M1 — Regras e decisão técnica | Revisar PRD/SPEC, definir limites e orçamento de eventual IA | Responsabilidades e bloqueios aceitos no ADR-002, ferramentas nos ADRs 003/004; limites e demais detalhes ainda a concluir |
| M2 — Fundação do projeto | Inicializar Git, organizar branches/PR, configurar validações e contexto do agente | Proteção e bloqueio de integração efetivamente verificados; regras não apenas declaradas em arquivo |
| M3 — Caminho determinístico | Registro, revisões, evidências, cadastro manual de candidatos e cálculo | Tarefa simples concluída sem extrator automático; cenários de datas e revisão verificados |
| M4 — Extração avaliada | Construir alternativa simples e experimentar IA se fizer sentido | Comparação de omissões, falsos positivos, qualidade dos campos, esforço e custo no conjunto definido |
| M5 — Fluxo completo | Integrar extração escolhida, conferência, agenda e cobertura | Cenários críticos e mudança de revisão funcionam sem esconder pendências |
| M6 — Entrega reproduzível | Instalação limpa, README, demonstração, limitações e materiais públicos | Outra execução reproduzida; cartão e rascunhos de publicação preparados para revisão |
| M7 — Proposta futura de evolução | Definir cenário de crescimento, medir a base local e comparar alternativas | Proposta de arquitetura, custos, migração e verificação conforme o plano de evolução; implementação não assumida no prazo inicial |

M3 é um passo de engenharia para verificar regras e formar uma comparação; não representa desistir da extração automática. M4 decide como implementá-la com evidências. Publicações e comunicações externas não serão executadas sem instrução explícita de Lucas.

**Atualização da fundação em 01/11/2026:** ambiente, cadastro, migração, backup e harness verificados. A publicação concluiu os controles de M2: PR aberto, CI aprovada em Windows/Linux e principal protegida, incluindo prova negativa de bloqueio. A revisão humana do PR continua pendente. Regras de datas e cadastro iniciam parte de M3; evidências documentais e conferência ainda não estão prontas. Veja os registros de [fundação](validacao-fundacao.md) e [publicação](validacao-publicacao.md).

**Avanço de regras e casos em 01/11/2026:** Lucas aceitou o ADR-002. Foram preparados [oito casos de desenvolvimento](../tests/fixtures/contracts/README.md), nove documentos e gabarito com evidências. Nessa entrega, os limites ainda eram propostas; os limites da entrada foram aplicados na etapa seguinte. Não há avaliação reservada nem extrator implementado.

**Avanço da entrada documental em 01/11/2026:** limites de recebimento adotados no ADR-006, originais preservados, revisões e reenvio implementados, migração do banco local com backup e verificação de envio/download pela interface. Veja a [validação documental](validacao-entrada-documental.md). Candidatos, conferência, confirmação e agenda continuam como próximas entregas; limites de processamento e orçamento do extrator ainda estão abertos.

**Avanço do caminho manual em 01/11/2026:** candidatos com evidências, cálculo, confirmação separada, resultado vazio e correção justificada foram implementados conforme [ADR-007](adrs/007-levantamento-manual-e-conferencia.md). A [validação](validacao-conferencia-manual.md) registra 123 testes locais e conferência simulada no navegador. A lista atual só mostra eventos de base válida; agenda temporal completa, extrator e sua avaliação continuam pendentes. A revisão de Lucas dos PRs também continua pendente.

**Avanço da agenda em 01/11/2026:** agenda temporal com referência explícita, filtros, origem e cobertura independente implementada conforme [ADR-008](adrs/008-agenda-e-cobertura-da-carteira.md). A [matriz da entrega](validacao-agenda.md) relaciona funcionalidades a testes e demonstração. O caminho manual agora chega à agenda; extração e seus estados de execução continuam pendentes, sem C20 completo comprovado. O próximo bloco é preparar a comparação de alternativas de extração e definir avaliação/orçamento antes de qualquer API paga. Revisão dos PRs por Lucas e evolução para escala permanecem separadas.

**Comparação inicial de extração em 01/11/2026:** [experimento offline](comparacao-extracao.md), com 20 casos de desenvolvimento/21 documentos e medição do baseline por regras. Sete candidatos indevidos e cinco impedimentos perdidos impedem recomendar sua integração. Avaliador/testes não equivalem a extrator integrado; IA, conjunto reservado, fornecedor, orçamento e estados de recuperação continuam pendentes. Decisão técnica no [ADR-009](adrs/009-experimento-offline-de-extracao.md).

## Primeiras unidades de trabalho depois de fechar a proposta técnica

Antes das funcionalidades, a fundação deverá validar a combinação de ferramentas aceita no [ADR-004](adrs/004-proposta-tecnologias-locais.md): instalação isolada, formulário local, migração, transação interrompida, submissão repetida e backup/restauração. Essa verificação não é uma demonstração de extração de contratos.

1. Definir o formato dos casos sintéticos e respostas esperadas com referências ao texto.
2. Criar exemplos de contrato simples, ausência de unidade, conflito, aditivo e análise vazia.
3. Implementar a regra de datas e a distinção entre candidato e confirmação.
4. Registrar contrato/revisão/execução sem duplicar eventos.
5. Construir a tela mínima de conferência com evidência próxima do campo.
6. Publicar a agenda somente a partir de confirmações válidas.
7. Integrar extração, mantendo os mesmos critérios de validação.
8. Verificar invalidação, falha, recuperação e cobertura da carteira.

Cada unidade deverá apontar para requisito, cenário de aceitação, mudança pequena e evidência de verificação. O agente poderá preparar e executar o trabalho combinado; Lucas decidirá mudanças relevantes de produto e risco.

## Roteiro proposto de demonstração

1. Exibir o case e a data de referência da simulação.
2. Registrar um contrato simples e ver os campos candidatos com evidência.
3. Mostrar que a agenda ainda não trata a sugestão como confirmação.
4. Conferir e confirmar; explicar o cálculo da data de aviso.
5. Abrir um caso ambíguo e mostrar a pendência sem uma data inventada.
6. Alterar a base de um contrato confirmado e mostrar a reconferência e o histórico.
7. Mostrar uma falha e a visão de cobertura, com todos os contratos contabilizados.

## O que foi feito nesta etapa

O case, o recorte, o direcionamento e as ferramentas foram aceitos. A fundação foi implementada com 34 testes locais aprovados, scripts, PR público, CI executada nos dois sistemas e proteção da principal verificada. A [proposta futura de evolução](evolucao-arquitetural.md) permanece planejada. Produto documental completo e conjunto de avaliação da extração ainda não foram entregues; testes de fundação não são prova dessas etapas.
