# ADR-003 — Aplicação local com módulos separados

**Status: aceito como direcionamento de arquitetura por Lucas.** Origem: “vamos considerar a aplicação local com módulos bem separados conforme sua sugestão”. Este aceite define a forma da aplicação; não aprova automaticamente bibliotecas, versões ou serviços pagos.

## Contexto

O primeiro fluxo atende um único negócio fictício e precisa registrar documentos, conferir extrações e manter uma agenda interna. O projeto será desenvolvido e demonstrado no Windows. Lucas informou disponibilidade superior a 10 horas por semana; orçamento de IA continua em aberto.

Precisamos conseguir explicar as responsabilidades e verificar as regras sem depender das telas.

## Alternativas consideradas

1. Aplicação local com telas, regras e acesso a dados concentrados no mesmo código: teria uma estrutura inicial menor, mas dificultaria testar regras independentemente e substituir o extrator ou a interface.
2. Aplicação local única com módulos por responsabilidade: mantém uma execução simples e permite separar domínio, casos de uso, armazenamento e telas.
3. Aplicação hospedada com serviços separados: acrescentaria implantação, comunicação entre componentes e operação antes de termos uma necessidade comprovada para isso.

## Decisão

Adotar a alternativa 2 como base: uma aplicação local, com um ponto de inicialização, dados locais e módulos separados por responsabilidade. A interface poderá abrir no navegador do próprio computador. A seleção concreta de ferramentas foi aceita posteriormente e está registrada no [ADR-004](004-proposta-tecnologias-locais.md).

As regras do negócio não dependerão da interface, do banco ou do fornecedor de extração. Os casos de uso coordenarão as operações; os componentes externos serão conectados na inicialização.

## Consequências

- A primeira entrega não exige hospedagem ou uma API pública.
- O computador precisa ter o ambiente do projeto preparado para executar a demonstração.
- Uso de IA continua uma decisão separada. Aplicação local não define se um eventual modelo executará no computador ou por API.
- A estrutura precisa ser praticável: criaremos fronteiras para responsabilidades reais, sem um serviço ou uma abstração para cada função.
- Identificação de revisor local não deve ser apresentada como autenticação de produção.

## Quando rever

Se surgirem requisitos de acesso remoto, vários usuários simultâneos, integrações externas ou capacidade além da execução local, registrar uma nova decisão e validar seus efeitos sobre identidade, concorrência, armazenamento e operação.

Relacionados: [arquitetura](../arquitetura.md), [PRD](../PRD.md) e [plano de entrega](../plano-de-entrega.md).
