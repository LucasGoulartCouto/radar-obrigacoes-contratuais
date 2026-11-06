# Radar de Obrigações Contratuais

Aplicação local para o Desafio Livre de novembro/dezembro de 2026 da Jornada de Dados.

**Retomando em outra sessão?** Leia [AGENTS.md](AGENTS.md) e o [ponto de retomada](docs/RETOMADA.md), que identifica a branch funcional, PRs, evidências e próximo passo. Confira o estado atual no Git antes de continuar.

**Situação em 01/11/2026:** aplicação local com cadastro, documentos versionados, candidatos manuais, conferência, agenda temporal e cobertura. **165 testes passaram localmente**, com [CI da versão funcional aprovada em Windows e Linux](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/actions/runs/41330174954). A versão mais recente está na branch `feat/agenda-e-cobertura`, no [PR #5](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/5). O [repositório é público](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais), e a `main` mantém a documentação anterior ao código enquanto os PRs encadeados aguardam revisão e integração.

A implementação está no [PR #1](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/1), aberto para revisão de Lucas. A principal mantém a documentação anterior ao código enquanto o PR não for integrado. Uma falha temporária comprovou o bloqueio da integração; o arquivo da prova foi removido. Veja a [validação da publicação](docs/validacao-publicacao.md).

A primeira versão de produto acompanha renovações e avisos prévios do case fictício da Agência Prisma. É possível receber textos sintéticos, preservar originais, registrar candidatos manualmente com trechos de origem, calcular aviso e realizar uma conferência separada. Eventos da base atual alimentam a agenda; eventos de bases antigas ficam no histórico. A extração automática continua pendente. Não há IA nem comunicação externa de negócio nesta entrega.

**Regras e casos do primeiro fluxo:** [decisão de produto](docs/decisoes-primeiro-fluxo.md) e [20 casos sintéticos de desenvolvimento](tests/fixtures/contracts/README.md), com 21 documentos e gabarito. Os oito iniciais foram preservados na ampliação do experimento offline. Lucas aceitou o ADR-002; os limites de entrada foram implementados no ADR-006. Esses exemplos ainda não são uma avaliação de extração. As verificações da entrada estão no [registro documental](docs/validacao-entrada-documental.md).

**Verificação local da versão com documentos:** 81 testes aprovados, incluindo migração com dados e os 38 testes novos da entrada. Upload, reenvio, alteração, rejeição por tamanho e download do original foram conferidos no navegador.

**Verificação local da versão com conferência:** 123 testes aprovados. O [registro da conferência](docs/validacao-conferencia-manual.md) distingue testes, migração e demonstração simulada no navegador de uma revisão humana real.

**Verificação local da agenda:** 165 testes aprovados, incluindo 42 novos. O [registro da agenda](docs/validacao-agenda.md) relaciona cada funcionalidade aos testes e à demonstração no navegador. A [matriz dos PRs anteriores](docs/evidencias-testes-por-pr.md) preserva a rastreabilidade das entregas encadeadas.

## Executar no Windows

Pré-requisito: Python **3.14.3**, com `python` acessível no terminal. Abra PowerShell na pasta do projeto. Os scripts funcionam sem ativar manualmente um ambiente e sem alterar pacotes globais.

```powershell
.\scripts\Preparar-Ambiente.ps1
.\scripts\Iniciar-Radar.ps1
```

O primeiro comando instala o uv **0.13.6** em `.tools/bootstrap`, sincroniza as dependências de `uv.lock` em `.venv` e aplica a migração. O segundo inicia a interface em [http://127.0.0.1:8501](http://127.0.0.1:8501). Encerre a execução iniciada no terminal com `Ctrl+C`.

Cadastre apenas um contrato fictício, informe um nome de personagem como responsável e confirme o contexto de simulação. O registro aparece como **Aguardando documentos** e permanece após recarregar. É possível editar seu nome; uma edição desatualizada é rejeitada.

Em **Documentos do contrato**, selecione os documentos atuais que deseja manter, adicione arquivos `.txt` sintéticos e informe seus papéis. Salvar envia o conjunto completo; arquivos retirados continuam nas revisões anteriores. Os limites padrão são **262.144 bytes por arquivo, 1.048.576 bytes por conjunto e 5 documentos**. Não há truncamento. Os parâmetros opcionais estão em `.env.example` e devem ser definidos na sessão.

O reenvio de mesmo texto e papel mantém a revisão, inclusive quando muda apenas o nome, BOM ou quebra de linha. Os bytes de cada envio aceito ficam disponíveis no histórico. Aditivo declarado mantém o bloqueio mesmo se for retirado do conjunto; o Radar não consolida seus efeitos. Veja o [registro de validação](docs/validacao-entrada-documental.md).

Em **Candidatos e conferência**, registre manualmente o resultado, selecione as linhas de evidência e salve o levantamento. A data do aviso é calculada pelo código. Os candidatos permanecem pendentes até a ação separada **Confirmar conferência**, após verificar campos, significado dos trechos e cobertura do texto. Ausência de eventos exige declaração específica. Corrigir um levantamento exige motivo e nova conferência; alterações documentais invalidam os eventos da visão atual sem apagar o histórico. Os responsáveis informados são personagens da simulação.

Em **Agenda e cobertura**, escolha a data de referência da simulação: o padrão é **01/05/2027**, com horizonte fixo de **30 dias**. Filtre situações de prazo e tipo de evento; “Depois do horizonte” permite consultar datas mais distantes. Limpar os filtros deixa a lista vazia e mantém a cobertura de todos os contratos. Apagar a referência pede uma data, sem inventá-la. Use **Origem de um evento exibido** para conferir trechos, cálculo e base; **Atualizar agenda** refaz a leitura de mudanças externas. Uma nova sessão volta à referência padrão. Consultar não altera confirmações.

O banco é criado em `var/radar.sqlite3`, fora do Git. Para escolher outro diretório local, defina `RADAR_DATA_DIR` na sessão antes de preparar/iniciar. Nenhuma chave de API é necessária. Os scripts não carregam `.env` automaticamente.

## Verificar e fazer backup

```powershell
.\scripts\Validar-Projeto.ps1
.\.tools\bootstrap\Scripts\uv.exe run --locked radar backup
```

A verificação inclui código, formatação, testes, links locais e dependências. O backup cria um novo arquivo em `var/backups/`, sem sobrescrever um destino existente. O teste de restauração usa outro banco temporário e preserva o banco de execução.

Em um ambiente que restrinja conexões locais ou a pasta temporária, os testes de interface precisam da liberação dessas operações pelo ambiente. Não altere o código para esconder uma falha de infraestrutura; o [registro de validação](docs/validacao-fundacao.md) explica o que foi executado nesta máquina.

## Evidência da interface

Agenda com um aviso confirmado, referência explícita e contratos pendentes:

![Agenda e cobertura do Radar](docs/evidencias/agenda-cobertura.png)

## Comece aqui

| Documento | O que você encontra |
|---|---|
| [Discovery](docs/discovery/radar-obrigacoes-contratuais.md) | Case fictício, dor, entrevista simulada, riscos e hipóteses |
| [PRD](docs/PRD.md) | Objetivo, primeira versão, exclusões e critérios de aceitação propostos |
| [SPEC do primeiro fluxo](docs/specs/001-primeiro-fluxo.md) | Regras de datas, evidências, revisão, versões, falhas e cenários verificáveis |
| [Arquitetura](docs/arquitetura.md) | Aplicação local, módulos, dependências, dados e tratamento de reexecuções/falhas |
| [Validação da fundação](docs/validacao-fundacao.md) | Ambiente, verificações executadas e limites do que está comprovado |
| [Validação da entrada documental](docs/validacao-entrada-documental.md) | Migração com dados, revisões, reenvio e envio/download reais pela interface |
| [Validação da conferência](docs/validacao-conferencia-manual.md) | Candidatos, evidências, confirmação separada e preservação do histórico |
| [Validação da agenda](docs/validacao-agenda.md) | Prazos, filtros, cobertura, origem e matriz de testes da entrega |
| [Evidências dos PRs anteriores](docs/evidencias-testes-por-pr.md) | Testes e registros de execução ligados às funcionalidades de cada PR |
| [Mapa dos agentes](AGENTS.md) | Rotas de leitura por tarefa, limites essenciais e comandos |
| [Agent Harness](docs/agents/harness.md) | Uso do Codex, contexto, automações e direção humana |
| [Governança do repositório](docs/governanca-repositorio.md) | Histórico Git, CI executada e controles ativos na principal |
| [Validação da publicação](docs/validacao-publicacao.md) | Repositório, PR, CI real e prova do bloqueio da principal |
| [ADR-001 — recorte aceito](docs/adrs/001-recorte-do-produto.md) | Escolha de produto feita por Lucas, alternativas e consequências |
| [ADR-002 — separação de responsabilidades](docs/adrs/002-proposta-limites-extracao-e-confirmacao.md) | Decisão aceita de separar extração, cálculo e confirmação; fluxo completo ainda a implementar |
| [Decisões do primeiro fluxo](docs/decisoes-primeiro-fluxo.md) | Regra aceita, limites de entrada aplicados e processamento futuro |
| [Casos sintéticos](tests/fixtures/contracts/README.md) | Oito casos de desenvolvimento com documentos e respostas esperadas |
| [ADR-003 — aplicação local modular](docs/adrs/003-aplicacao-local-modular.md) | Direcionamento escolhido por Lucas, alternativas e limites |
| [ADR-004 — tecnologias aceitas](docs/adrs/004-proposta-tecnologias-locais.md) | Ferramentas escolhidas, alternativas e verificações ainda necessárias |
| [ADR-005 — persistência da fundação](docs/adrs/005-persistencia-da-fundacao.md) | Transação, reenvio, histórico e controle de edição implementados |
| [ADR-006 — entrada documental](docs/adrs/006-entrada-e-revisoes-documentais.md) | Identidade das revisões, originais, limites e consequências implementadas |
| [ADR-007 — levantamento e conferência](docs/adrs/007-levantamento-manual-e-conferencia.md) | Baseline manual, confirmação atômica, correções e invalidação da base antiga |
| [ADR-008 — agenda e cobertura](docs/adrs/008-agenda-e-cobertura-da-carteira.md) | Leitura consistente, horizonte de 30 dias, filtros e cobertura independente |
| [Evolução da arquitetura](docs/evolucao-arquitetural.md) | Etapa futura solicitada: cenário de crescimento, medições e proposta de evolução |
| [IA local](docs/ia-local.md) | Preparo do runtime, modelo provisório, rodada real e limitações |
| [Comparação de extração](docs/comparacao-extracao.md) | Experimento offline por regras, falhas mensuradas e protocolo para avaliar IA |
| [Validação do experimento](docs/validacao-experimento-extracao.md) | Evidências por comportamento, testes e limites do benchmark |
| [Plano de entrega](docs/plano-de-entrega.md) | Marcos, dependências, primeiras tarefas e roteiro de demonstração |
| [Planejamento inicial](docs/planejamento-inicial.md) | Exigências oficiais, comparação de ideias e calendário provisório |

A documentação dos agentes foi organizada e a [comparação inicial de extração](docs/comparacao-extracao.md) executou um baseline offline em 20 casos de desenvolvimento. As falhas encontradas impedem recomendar sua integração; a aplicação continua usando levantamento manual. Lucas escolheu [IA local durante o desenvolvimento](docs/ia-local.md); a primeira rodada real revelou erros e permanece fora da aplicação. O próximo passo é revisar a fronteira de extração local. Planejamento de produção e escolha do melhor modelo ficam para depois da aplicação concluída. O [plano de entrega](docs/plano-de-entrega.md) mantém os passos de produto e a proposta futura de evolução para escala e desempenho. Os PRs continuam separados para revisão de Lucas; desempenho sob carga e qualidade da extração ainda não foram avaliados.

## Referências oficiais

- [Enunciado do Desafio Livre](https://github.com/suajornadadedados/desafio-jornada/blob/main/desafio-livre/README.md)
- [Regras de submissão](https://github.com/suajornadadedados/desafio-jornada/blob/main/COMO-SUBMETER.md)

Consulta realizada em 31/10/2026. O encerramento está previsto para a primeira quinzena de dezembro de 2026, com dia ainda a confirmar no enunciado consultado.

## Limites do case

Os dados do produto serão sintéticos e as ações de negócio serão simuladas, conforme o desafio. Resultados de simulação serão identificados como tal.
