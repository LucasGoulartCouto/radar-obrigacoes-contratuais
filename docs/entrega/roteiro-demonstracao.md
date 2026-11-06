# Roteiro de demonstração — versão para revisão

Duração sugerida: 6–8 minutos, sem gravação cronometrada ou vídeo produzido nesta entrega. Use banco de demonstração separado, somente os documentos sintéticos versionados e nomes de personagens. Não opere sobre a carteira de trabalho para gravar uma apresentação.

## Abertura: problema e limite

**Dizer:** “No case fictício da Agência Prisma, Rafael prepara os prazos dos fornecedores e Marina confere antes de decidir. O risco é uma data plausível esconder falta de evidência, conflito ou documento antigo. O Radar separa o que está escrito, o que foi calculado e o que foi conferido.”

**Mostrar:** [discovery](../discovery/radar-obrigacoes-contratuais.md), recorte do produto e aviso de simulação. Não apresentar a entrevista fictícia como pesquisa com clientes nem prometer economia de tempo/perdas que não foi medida.

## Cena 1 — Instalação e carteira

Mostrar o [guia de reprodução](reproducao.md), a versão/branch e a data de referência da agenda. Explicar que banco e pesos não vêm com o clone. Na carteira vazia, cadastrar um contrato fictício e receber DEV-001 como base.

**Conferir:** cadastro persiste após recarregar; receber documentos não cria eventos.

## Cena 2 — Sugestão, cálculo e confirmação

Solicitar análise assistida de DEV-001. Abrir texto completo, classificações e evidências. Mostrar término em 30/06/2027 e regra de aviso de 30 dias corridos; explicar a data calculada de 31/05/2027.

Escolher o resultado e mostrar que a agenda ainda não contém seus eventos. Tentar confirmar sem declaração deve exibir erro. Depois da conferência **simulada**, declarar a revisão e confirmar. Recarregar e consultar a origem na agenda.

**Dizer:** “O modelo classifica linhas; o código interpreta os literais, localiza a evidência e calcula. Confirmar não cancela o contrato nem envia mensagem ao fornecedor.”

## Cena 3 — Pendência que não vira palpite

Receber [DEV-002](../../tests/fixtures/contracts/development/documents/DEV-002-base.txt), que não define dias corridos, ou [DEV-003](../../tests/fixtures/contracts/development/documents/DEV-003-base.txt), que contém conflito. Analisar e exibir o motivo da pendência. Não escolher uma data concorrente só para completar a demonstração.

**Conferir:** bloqueio impede confirmação e o contrato continua contado na cobertura.

## Cena 4 — Documento não tem autoridade

Abrir [DEV-008](../../tests/fixtures/contracts/development/documents/DEV-008-base.txt) e exibir a instrução ao assistente como texto. A referência conhecida reteve esse trecho. Quando a guarda oferecer revisão de contexto, registrar decisão localizada, justificativa e declaração após ler o conjunto. Preservar antes/depois e mostrar que os candidatos ainda precisam de outra confirmação.

Não executar a instrução do documento. Não prometer que toda tentativa do modelo reproduzirá exatamente os mesmos labels; se variar, mostrar o resultado real e seu tratamento, preservando a observação.

## Cena 5 — Mudança de base e recuperação

Alterar de forma sintética o documento de um caso conferido. Mostrar a revisão nova, a retirada dos eventos antigos apenas da visão atual e a conferência anterior no histórico. A nova base exige análise/conferência atualizadas.

Para demonstrar falha, identificar explicitamente uma injeção controlada, como digest de teste divergente em ambiente isolado. Exibir a tentativa falha, restaurar a configuração correta e iniciar nova tentativa. Não descrever o teste induzido como incidente espontâneo de produção, nem parar processos que estejam servindo outros ambientes.

**Conferir:** histórico mantém a falha e a tentativa posterior; recarregar não inicia nova análise por conta própria.

## Fechamento — Evidências e limites

Mostrar os seis grupos da cobertura e distinguir a [matriz automatizada](../validacao-integracao-assistida.md) de uma demonstração com poucas situações. Abrir o PR da entrega e seus checks. CI aprovada não é aprovação de Lucas nem comprovação geral da qualidade do modelo.

**Dizer:** “A referência automática teve 18 de 20 casos integrais no desenvolvimento conhecido; duas retenções foram tratadas separadamente por revisão. Não houve avaliação reservada, autenticação, operação com contratos reais ou medição sob carga. Os PRs e materiais estão sob revisão.”

Não afirmar C20 completo, produção pronta ou revisão humana real com base nesta gravação. Planejamento de produção e escolha definitiva da IA são uma etapa posterior às decisões de Lucas sobre a aplicação.
