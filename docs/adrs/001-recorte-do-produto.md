# ADR-001 — Focar em renovações e avisos prévios

Data: 31/10/2026.

**Status: aceito por Lucas para o case e o recorte de produto.** Fonte da decisão: após a apresentação do case da Agência Prisma e da recomendação de começar por renovações e avisos prévios em contratos de serviços com fornecedores, Lucas respondeu: “ok vamos fazer sua recomendação”.

## Contexto

O Desafio Livre pede problema concreto, decisões registradas, uso explícito de agente e arquitetura explicada, com dados sintéticos e efeitos de negócio simulados. Lucas escolheu Radar de Obrigações Contratuais e um case criado do zero. Precisávamos de uma primeira tarefa demonstrável antes de selecionar tecnologias.

## Alternativas consideradas

1. Outras ideias iniciais: fechamento de vendas, conciliação financeira ou conferência de fretes. Lucas preferiu o Radar.
2. Radar abrangente para qualquer obrigação contratual: ampliaria tipos de documentos, condições e critérios de correção antes de validar o primeiro fluxo.
3. Radar focado em renovações e avisos prévios de contratos de serviços com fornecedores: permite definir eventos, evidências, cálculos e situações de revisão dentro de um recorte menor.

## Decisão

Adotar a alternativa 3 no case fictício da Agência Prisma. O produto apoiará a conferência administrativa de marcos e prazos; o usuário continuará responsável pela decisão simulada sobre continuidade do fornecedor.

## Consequências aceitas para o recorte

- A primeira versão não será um gestor universal de contratos.
- Outros tipos de obrigação não definirão o escopo inicial.
- Origem das informações, cálculo verificável e revisão de ambiguidades passam a ser centrais para demonstrar valor.
- Adoção de IA, arquitetura, tecnologias e metas detalhadas ainda precisam de decisões próprias; este aceite não as aprova automaticamente.

## Quando revisar

Reabrir o recorte se o discovery mostrar que a tarefa escolhida não gera uma demonstração útil ou que não conseguimos especificar seus casos críticos dentro do esforço disponível. Registrar uma decisão sucessora, preservando esta escolha e suas razões.

Documentos relacionados: [discovery](../discovery/radar-obrigacoes-contratuais.md), [PRD](../PRD.md) e [SPEC](../specs/001-primeiro-fluxo.md).
