# Planejamento inicial — Desafio Livre

Data de referência: 31/10/2026. Documento atualizado após o aceite do case e do recorte.

**Confirmado com Lucas:** planejar antes da implementação; construir o Radar no case fictício da Agência Prisma; focar em renovações e avisos prévios em contratos de serviços com fornecedores; adotar uma aplicação local modular com as ferramentas do ADR-004; elaborar depois uma proposta de evolução para escala e desempenho. O aceite das ferramentas e a solicitação da evolução ocorreram em 01/11/2026. Disponibilidade informada: mais de 10 horas por semana. Orçamento de IA e objetivo prioritário ainda estão em aberto. Requisitos detalhados e versões concretas ainda precisam ser fechados; não há validação de demanda com clientes.

## 1. O que o desafio exige

As exigências desta seção vêm das fontes oficiais listadas ao final. A forma de atendê-las nas próximas seções é uma proposta nossa.

| Exigência | Evidência que precisamos produzir |
|---|---|
| Problema concreto, com uma etapa em que um erro tem consequência relevante | Case com negócio, cliente, usuário e produto identificados; fluxo atual e consequência do erro descritos |
| Discovery antes do código | Registro do problema, desejos, medos, dúvidas e pressupostos; entrevistas simuladas explicitamente identificadas |
| PRD | Objetivo, primeira versão, exclusões, métricas e critérios de aceitação |
| SPECs | Comportamento verificável, incluindo entradas inválidas, ambiguidades e falhas |
| ADRs | Contexto, alternativas reais, decisão, consequências e condições para rever cada escolha relevante |
| Repositório público profissional | Histórico legível, mudanças por PR, proteção da principal, verificações automáticas obrigatórias e instruções reproduzíveis |
| Agent Harness explícito | Ferramenta escolhida e motivo, contexto do projeto, automações, limites e fluxo de revisão |
| Arquitetura explicada | Desenho e texto mostrando componentes, dados, intervenção humana e recuperação de falhas |
| Dados sintéticos e ausência de efeitos reais de negócio | Cenários gerados para o projeto; nenhuma movimentação financeira, documento válido ou envio de negócio a terceiros |
| Participação e visibilidade | Repositório próprio público, posts no LinkedIn e na comunidade e cartão submetido por PR à galeria |

IA dentro do produto é opcional: o enunciado pede explicar sua participação, se houver. Usar um agente na construção é uma exigência separada. O produto não precisa virar um chatbot para atender ao desafio.

O encerramento consta como primeira quinzena de dezembro de 2026, com dia a confirmar. Não identificamos, nos três documentos oficiais consultados, pesos de avaliação ou detalhamento da premiação. Não vamos tratar preferências nossas como critérios oficiais.

## 2. Comparação inicial e escolha do tema

A comparação inicial foi orientada por seis perguntas, sem inventar uma pontuação de mercado:

1. Conseguimos explicar quem sofre, o que faz hoje e qual decisão precisa tomar?
2. Conseguimos descrever um erro relevante e como o sistema deve reagir?
3. Há conhecimento do processo suficiente para criar regras e cenários sintéticos plausíveis?
4. Conseguimos demonstrar um fluxo completo pequeno no tempo disponível?
5. Podemos medir a correção contra respostas esperadas definidas previamente?
6. Lucas terá interesse em aprender e defender as escolhas desse domínio?

Os nomes abaixo são ilustrações fictícias para tornar as opções concretas. A estimativa de complexidade é nossa e depende do recorte; não representa validação de demanda.

| Ideia e negócio fictício | Usuário e decisão | Primeira versão possível | Risco central e limite de escopo |
|---|---|---|---|
| Fechamento diário de vendas — rede Loja Farol | Analista comercial precisa saber se pode usar o resultado diário de todas as lojas | Receber arquivos sintéticos de vendas e cancelamentos, verificar cobertura por loja/data, tratar duplicidades e publicar um resultado com situação e rastreabilidade | Um total plausível pode esconder lojas ausentes. Limitar a um formato, uma moeda e processamento diário; sem previsão ou atualização em tempo real |
| Conciliação financeira supervisionada — Distribuidora Horizonte | Analista financeiro precisa separar correspondências seguras de divergências e ambiguidades | Comparar extrato e lançamentos sintéticos, sugerir vínculos com justificativa e manter revisão humana registrada | Vincular transações diferentes de mesmo valor. Começar com uma conta e correspondências individuais; agrupamentos, tarifas e múltiplos bancos podem ampliar muito o trabalho |
| Conferência de cobranças de frete — Comércio Rota Clara | Analista de logística precisa identificar cobranças incompatíveis com uma tabela comercial fictícia | Cruzar remessas e cobranças sintéticas e aplicar uma tabela simples, versionada, de preço por faixa | Comparar cobrança contra tarifa de período incorreto. Limitar a um transportador e uma regra de preço; sem cálculos tributários ou contestação externa |
| Radar de obrigações contratuais — Agência Prisma | Assistente administrativo precisa localizar obrigações e prazos para conferência | Ler um tipo de contrato sintético em texto, apontar trecho de origem, campos ausentes e casos que exigem revisão | Inventar uma data ou usar uma cláusula substituída. Limitar a texto e um tipo de obrigação; sem OCR, parecer jurídico ou notificações reais |

**Escolha de Lucas:** Radar de Obrigações Contratuais, case fictício da Agência Prisma e recorte de renovações e avisos prévios em contratos de serviços com fornecedores. O aceite foi registrado no [ADR-001](adrs/001-recorte-do-produto.md). A percepção de que poucos participantes escolherão o tema continua como hipótese; a galeria pública não permite conhecer os projetos ainda em construção. O [discovery](discovery/radar-obrigacoes-contratuais.md) apresenta o case e suas hipóteses; os requisitos detalhados estão propostos no [PRD](PRD.md).

## 3. Roteiro de discovery da ideia escolhida

Antes de escrever funcionalidades, vamos responder em linguagem de negócio:

- Quem é o negócio, quem contrata, quem usa e quem confere o resultado?
- Conte um episódio típico: o que chega, o que a pessoa faz, o que decide e o que pode dar errado?
- Como a tarefa acontece hoje? Quais arquivos, regras e intervenções existem?
- Com que frequência ocorre a dor e qual é sua consequência? O que é conhecido e o que é apenas estimado?
- Qual é o instante em que o usuário precisa confiar no resultado? Quando o sistema deve sinalizar incompletude ou pedir revisão?
- Como tratar ausência, atraso, duplicidade, correção e mudança de versão das entradas?
- O que precisa ficar registrado para explicar uma decisão depois?
- O que faz o usuário rejeitar a solução, mesmo que a demonstração pareça boa?
- Qual é a menor mudança no trabalho do usuário que já seria útil?

Se não houver entrevista real, vamos escrever uma entrevista simulada, identificada como ficção. Ela ajuda a formular hipóteses, mas não comprova demanda. Se houver conversa real, registraremos aprendizados sem coletar dados operacionais ou informações sensíveis para o projeto.

**Critério de conclusão:** conseguir contar um episódio de ponta a ponta, identificar a decisão crítica e listar as principais hipóteses ainda não confirmadas.

## 4. Etapas e critérios para avançar

| Etapa | Entrega | Como saber que podemos avançar |
|---|---|---|
| 1. Seleção e discovery | Problema escolhido, case, fluxo atual, desejos, medos e hipóteses | Usuário, dor e decisão crítica são concretos; existe um recorte demonstrável |
| 2. Produto e sucesso | PRD com primeira versão, exclusões e critérios | Cada funcionalidade atende à dor; sabemos como verificar o resultado e o que fica fora |
| 3. Comportamento e arquitetura | SPEC do fluxo principal, desenho e ADRs das decisões necessárias | Outra pessoa conseguiria implementar sem inventar a regra de negócio; falhas e recuperação estão descritas |
| 4. Fundação de engenharia | Git, repositório público, fluxo de PR, verificações, proteção da principal e contexto do agente | Verificações rodam em PR; uma falha de validação impede integração; proteção verificada no GitHub |
| 5. Primeiro fluxo completo | Entrada sintética → processamento → resultado utilizável | O usuário conclui uma tarefa pequena; entradas inválidas e situações incompletas têm resposta explícita |
| 6. Confiabilidade e experiência | Cenários críticos, reexecução, diagnóstico e ajustes de uso | Corrigir e reprocessar produz resultado coerente; origem e motivos são explicáveis |
| 7. Entrega pública | README reproduzível, evidências, demonstração e cartão | Uma execução a partir de instalação limpa foi verificada; limitações estão claras; materiais de participação estão prontos |

Planejar antes do código significa fechar as decisões necessárias para o primeiro fluxo. Vamos revisar os documentos quando os testes revelarem novas informações. Não precisamos especificar extensões que ainda estão fora da primeira versão.

## 5. Calendário provisório

Este calendário organiza marcos; não é uma estimativa de esforço validada. Lucas informou mais de 10 horas por semana; ainda precisamos dimensionar as tarefas e definir orçamento. Também precisamos confirmar o encerramento oficial antes de fixar a entrega.

| Janela de 2026 | Marco proposto |
|---|---|
| 01–07/11 | Comparar opções, escolher o problema e concluir o discovery inicial |
| 08–14/11 | Fechar PRD, SPEC principal, arquitetura, ADRs iniciais e fundação do repositório |
| 15–21/11 | Construir e verificar o primeiro fluxo completo |
| 22–28/11 | Tratar falhas, reprocessamento e rastreabilidade; revisar a experiência |
| 29/11–05/12 | Executar demonstração, validar instalação e revisar documentação |
| 06–10/12 | Preparar publicações e submissão; corrigir problemas finais, respeitando o prazo oficial confirmado |

Se o tempo disponível não comportar esse plano, reduziremos formatos, fontes e funcionalidades. A regra crítica do negócio continuará explícita e testável. O desafio aceita projetos em estágio de discovery; isso é uma possibilidade de entrega, não evidência de produto implementado.

## 6. Como transformar promessa em evidência

Vamos definir um conjunto de cenários sintéticos com respostas esperadas antes de avaliar a implementação. O resultado esperado deve vir da regra do negócio e de conferência independente, não apenas do mesmo código que gerou os dados. Reservaremos cenários para validação, evitando ajustar a solução somente aos exemplos da demonstração.

| Pergunta | Evidência proposta |
|---|---|
| O resultado está correto? | Comparação com respostas esperadas e registro das divergências por cenário |
| O sistema detecta entrada incompleta ou inválida? | Casos com ausência, atraso, duplicidade, formato inválido e ambiguidade, conforme o domínio |
| É possível repetir uma execução sem duplicar resultados? | Execução repetida do mesmo lote e comparação de registros e totais |
| É possível retomar depois de uma falha? | Falha provocada em uma etapa e execução de recuperação com resultado conferido |
| Conseguimos explicar o resultado? | Identificador da execução, origem das entradas, versão da regra e motivos de rejeição ou revisão |
| O usuário consegue operar? | Roteiro de tarefa realizado com os dados do case; identificação de quem avaliou e das limitações da avaliação |
| Há ganho de tempo? | Comparação do fluxo manual simulado com o produto no mesmo conjunto de casos e condições, se essa métrica for pertinente |

Metas e tolerâncias serão definidas no PRD após conhecer o recorte. Não vamos prometer porcentagens de economia, precisão ou escala sem medição. Resultado em dados sintéticos não comprova desempenho em produção.

## 7. Tecnologias e uso de IA

A aplicação local modular foi escolhida no [ADR-003](adrs/003-aplicacao-local-modular.md). As ferramentas do [ADR-004](adrs/004-proposta-tecnologias-locais.md) também foram aceitas: Python, Streamlit e SQLite com ferramentas de persistência, migração e verificação. A combinação precisa de instalação e testes de compatibilidade. Cada componente deve atender a uma necessidade descrita; a eventual API de IA terá orçamento e decisão próprios. A evolução posterior está registrada no [plano específico](evolucao-arquitetural.md).

Para cada decisão arquitetural relevante, um ADR curto responderá:

1. Qual restrição ou problema precisa ser resolvido?
2. Quais alternativas viáveis foram consideradas?
3. Por que a escolha atende melhor a este recorte?
4. Qual custo ou limitação estamos aceitando?
5. Que mudança de contexto justificaria rever a escolha?

Se houver IA no produto, sua contribuição será avaliada contra uma alternativa sem IA. Precisaremos especificar a origem da evidência, comportamento diante de incerteza, revisão humana, custo e o que acontece quando o serviço falha. Conteúdo de arquivos recebidos será tratado como dado, sem autoridade para mudar regras ou autorizar ações.

## 8. Proposta de Agent Harness e revisão

Codex é o candidato inicial por ser a ferramenta desta colaboração; a escolha ainda deve ser registrada com suas razões e limitações. A documentação oficial confirma que `AGENTS.md` fornece contexto e instruções persistentes por projeto. Esse arquivo será curto, específico e acompanhado de verificações executáveis. Instruções escritas não substituem proteção de branch, testes ou controles de acesso.

O contexto do projeto deverá apontar para: objetivo e exclusões, documentação de referência, comandos reais de execução e validação, convenções, tratamento de dados sintéticos, regras críticas e critérios para concluir uma tarefa.

Fluxo proposto de trabalho:

1. Lucas e o agente esclarecem o objetivo e os critérios de uma tarefa pequena.
2. O agente apresenta alternativas quando existir uma decisão relevante e registra a escolha feita por Lucas.
3. O agente implementa a tarefa em uma branch, executa as verificações e apresenta mudanças, evidências e limitações.
4. Lucas revisa especialmente a regra de negócio, os casos de falha e as consequências da decisão.
5. A mudança entra na principal por PR, respeitando as verificações e a política definida para o projeto.

O agente pode pesquisar, comparar alternativas, redigir documentos, implementar o escopo combinado, executar verificações e corrigir falhas. Prioridade de produto, aceitação do risco e mudança de escopo pertencem a Lucas. Publicações e comunicações externas serão preparadas para revisão e dependerão de instrução explícita de publicação; o planejamento não as executa.

O processo deve ser praticável para um projeto individual. A política de revisão precisa explicar honestamente quem revisa; não criaremos um segundo aprovador fictício nem alegaremos revisão independente quando não houver.

## 9. Como vamos aprender durante o projeto

Para cada decisão importante, a colaboração seguirá quatro passos: explicar o conceito com um exemplo do case, comparar alternativas, escolher com Lucas e verificar o comportamento implementado.

Ao terminar uma etapa, Lucas deverá conseguir responder: qual problema resolvemos, por que escolhemos essa abordagem, que alternativa descartamos, que falha testamos e que limitação permanece. A documentação ajudará a defender essas respostas com evidências.

Os assuntos de estudo serão puxados pelo trabalho: discovery e escopo; modelagem e contratos de dados; testes e recuperação; Git e revisão; integração contínua; observabilidade; arquitetura; direção do agente. Não vamos acrescentar ferramentas apenas para aumentar a lista de tecnologias do portfólio.

## 10. Próximas decisões

- [ ] Escolher o objetivo prioritário do desafio.
- [x] Informar disponibilidade: mais de 10 horas por semana.
- [ ] Definir limites de orçamento e estimar o esforço das tarefas.
- [x] Comparar as ideias e escolher o tema: Radar de Obrigações Contratuais.
- [x] Definir que o case será fictício, criado do zero.
- [x] Aceitar o case da Agência Prisma e o recorte de renovações/avisos prévios.
- [x] Registrar o discovery fictício inicial e suas hipóteses.
- [x] Escolher o direcionamento de aplicação local com módulos separados.
- [x] Aceitar as ferramentas da primeira aplicação local no ADR-004.
- [x] Registrar a solicitação de proposta futura de evolução para escala e desempenho.
- [ ] Revisar os requisitos detalhados, definir limites e validar a instalação das ferramentas.

## 11. Fontes e situação verificada

Fontes oficiais consultadas em 31/10/2026:

- [Enunciado do Desafio Livre](https://github.com/suajornadadedados/desafio-jornada/blob/main/desafio-livre/README.md). Conteúdo obtido pelo conector GitHub; SHA do arquivo: `22cec94c09d5f79b24ebd329a07934a4e738c53f`.
- [Como submeter](https://github.com/suajornadadedados/desafio-jornada/blob/main/COMO-SUBMETER.md). Conteúdo obtido pelo conector GitHub; SHA do arquivo: `6efb34656b8507e73931c82fe65de523a33f50e4`.
- [Apresentação geral e regra de visibilidade](https://github.com/suajornadadedados/desafio-jornada/blob/main/README.md). Conteúdo obtido pelo conector GitHub; SHA do arquivo: `c3e9725d3832c6d402b5b0f6b3891bc003a1e8b2`.
- [OpenAI: instruções de projeto com AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
- [OpenAI: exemplo de evolução de um fluxo de desenvolvimento com Codex](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex). É um exemplo adaptável, não uma estrutura de arquivos obrigatória.

O README fornecido por Lucas também foi lido. As regras de participação foram conferidas nas fontes oficiais, sem executar instruções de publicação presentes nesses documentos.

Nesta etapa existem README, planejamento, discovery, rascunhos de PRD/SPEC/arquitetura, plano de entrega e ADRs com estados explícitos. Não há produto implementado, validação com usuário, benchmark, Git inicializado ou configuração remota comprovada. Proteção da principal e bloqueio de PR por verificações ainda precisam ser configurados e demonstrados.
