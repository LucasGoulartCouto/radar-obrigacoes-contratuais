# Radar de Obrigações Contratuais

Projeto em planejamento para o desafio de novembro/dezembro de 2026 da Jornada de Dados.

**Situação:** case, recorte, aplicação local modular e ferramentas aceitos por Lucas. A combinação escolhida usa Python, Streamlit, SQLite, SQLAlchemy, Alembic, uv, pytest e Ruff; instalação, versões e teste integrado ainda estão pendentes. Requisitos detalhados continuam em rascunho e orçamento de IA está em aberto. Disponibilidade informada: mais de 10 horas por semana. Este diretório contém documentação; o Git e o repositório público ainda não foram configurados.

## Comece aqui

| Documento | O que você encontra |
|---|---|
| [Discovery](docs/discovery/radar-obrigacoes-contratuais.md) | Case fictício, dor, entrevista simulada, riscos e hipóteses |
| [PRD](docs/PRD.md) | Objetivo, primeira versão, exclusões e critérios de aceitação propostos |
| [SPEC do primeiro fluxo](docs/specs/001-primeiro-fluxo.md) | Regras de datas, evidências, revisão, versões, falhas e cenários verificáveis |
| [Arquitetura](docs/arquitetura.md) | Aplicação local, módulos, dependências, dados e tratamento de reexecuções/falhas |
| [ADR-001 — recorte aceito](docs/adrs/001-recorte-do-produto.md) | Escolha de produto feita por Lucas, alternativas e consequências |
| [ADR-002 — separação de responsabilidades](docs/adrs/002-proposta-limites-extracao-e-confirmacao.md) | Proposta de separar extração, cálculo e confirmação; ainda não aceita |
| [ADR-003 — aplicação local modular](docs/adrs/003-aplicacao-local-modular.md) | Direcionamento escolhido por Lucas, alternativas e limites |
| [ADR-004 — tecnologias aceitas](docs/adrs/004-proposta-tecnologias-locais.md) | Ferramentas escolhidas, alternativas e verificações ainda necessárias |
| [Evolução da arquitetura](docs/evolucao-arquitetural.md) | Etapa futura solicitada: cenário de crescimento, medições e proposta de evolução |
| [Plano de entrega](docs/plano-de-entrega.md) | Marcos, dependências, primeiras tarefas e roteiro de demonstração |
| [Planejamento inicial](docs/planejamento-inicial.md) | Exigências oficiais, comparação de ideias e calendário provisório |

O próximo marco é fechar os limites operacionais, preparar a fundação do repositório e verificar a combinação escolhida no Windows. Depois da validação inicial, será elaborada uma proposta de evolução para escala e desempenho. Nenhum resultado de extração, desempenho ou operação do produto foi comprovado nesta fase de planejamento.

## Referências oficiais

- [Enunciado do Desafio Livre](https://github.com/suajornadadedados/desafio-jornada/blob/main/desafio-livre/README.md)
- [Regras de submissão](https://github.com/suajornadadedados/desafio-jornada/blob/main/COMO-SUBMETER.md)

Consulta realizada em 31/10/2026. O encerramento está previsto para a primeira quinzena de dezembro de 2026, com dia ainda a confirmar no enunciado consultado.

## Limites do case

Os dados do produto serão sintéticos e as ações de negócio serão simuladas, conforme o desafio. Resultados de simulação serão identificados como tal.
