# Evolução da arquitetura — escala e desempenho

Registro de intenção em 01/11/2026.

**Atualização de 05/11/2026: M7 preparada para revisão.** Lucas solicitou executar a etapa e escolheu cenários hipotéticos com premissas explícitas. A [proposta M7](m7-proposta.md), o [baseline medido](validacao-m7.md), os [custos](m7-custos.md) e o [ADR-014 proposto](adrs/014-evolucao-condicional-para-uso-compartilhado.md) atendem ao plano abaixo. Não há implantação, orçamento aprovado ou escolha definitiva de IA.

## Plano original de 01/11/2026

As seções seguintes preservam os critérios de entrada e entrega originais. A ausência de cenário/metas descrita ali é histórica: o estudo atual usa hipóteses expressamente escolhidas por Lucas, sem convertê-las em demanda real.

## 1. Objetivo da etapa

Depois de validar o primeiro fluxo local, propor uma evolução que sustente um cenário de crescimento definido. A proposta deverá explicar o que muda, por que muda, que problema medido ou requisito novo atende e quais custos e responsabilidades acrescenta.

O escopo solicitado é elaborar a proposta. Implantação, serviços pagos e ampliação funcional exigirão decisões próprias. Não assumimos que a evolução será implementada dentro do prazo do desafio.

## 2. Informações necessárias antes de desenhar a evolução

- Quantidade de contratos e documentos acumulados, tamanho dos textos e volume de novas análises por período.
- Número de pessoas e operações simultâneas, distinguindo leitura, processamento e confirmação.
- Metas de tempo de resposta para consulta, conferência e conclusão de uma análise.
- Necessidade de acesso remoto, disponibilidade, recuperação e continuidade do processamento.
- Requisitos de identidade, autorização, isolamento e histórico caso o uso deixe de ser individual/local.
- Limites de custo de processamento, armazenamento, eventual IA e operação.

Esses valores ainda não estão definidos. Não vamos inventar capacidade ou metas para justificar uma tecnologia previamente escolhida.

## 3. Medições a preparar na versão inicial

Registrar duração e resultado por etapa, volume/tamanho das entradas e contexto da execução. Para a avaliação futura, medir consultas e confirmações, processamento, consumo de recursos, falhas e comportamento sob repetição/concorrência. Se houver IA, separar sua latência e custo dos demais componentes.

O experimento deverá informar máquina/ambiente, versões, conjunto sintético, concorrência, repetições, condições de cache e método de medição. Uma execução rápida isolada não sustentará uma promessa de capacidade.

## 4. Entregáveis futuros

1. Cenário de crescimento e metas não funcionais, diferenciando necessidades reais do case de hipóteses de exercício.
2. Linha de base da versão local e identificação dos limites relevantes.
3. Comparação de alternativas por componente, incluindo manter e otimizar o desenho atual quando atender às metas.
4. Desenho da arquitetura proposta, fluxo de dados e impacto sobre as regras já verificadas.
5. Plano de migração, custos, observabilidade, recuperação e reversão.
6. Plano de testes de carga e correção com critérios para aceitar ou rejeitar a evolução.
7. ADRs das decisões, com alternativas descartadas e consequências.

## 5. Regras que precisam sobreviver à evolução

Preservar origem e versões dos documentos, confirmação ligada à base atual, cálculo verificável, histórico e pendências visíveis. Aumentar capacidade não pode permitir confirmação desatualizada, duplicar eventos ou transformar falha de processamento em resultado vazio.

O desenho modular atual deve ajudar a testar essas regras independentemente da interface e do armazenamento. Isso não garante migração automática: os comportamentos de cada novo componente precisarão ser verificados.

Relacionados: [arquitetura atual](arquitetura.md), [decisão de ferramentas](adrs/004-proposta-tecnologias-locais.md), [SPEC](specs/001-primeiro-fluxo.md) e [plano de entrega](plano-de-entrega.md).
