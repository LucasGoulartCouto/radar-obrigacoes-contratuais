# Correção da disputa de gravação encontrada na integração

05/11/2026. A integração autorizada parou no PR #12 antes de qualquer merge desse PR. A [CI 42135787736](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/actions/runs/42135787736) falhou no Windows: `test_only_one_worker_can_claim_a_pending_attempt`, durante a conclusão de uma tentativa; 370 testes passaram e um falhou. A falha foi preservada, sem remover o teste ou repetir a execução para obter verde.

## Reprodução e causa

O executor transacional de conferência/extração consultava primeiro o recibo da operação, abrindo uma leitura SQLite DEFERRED. Outra conexão podia reservar a escrita nesse intervalo. Ao concluir a tentativa, promover a primeira transação para escrita falhava com `SQLITE_BUSY`, mesmo sem repetir a inferência. O erro era traduzido em `StorageBusyError`, deixando a tentativa recuperável, mas interrompendo uma conclusão que poderia ser serializada.

O novo teste `test_finish_reserves_writer_before_reading_receipt`, em [test_extractions.py](../tests/integration/test_extractions.py), reproduz a disputa de forma controlada: após ler o recibo, uma segunda conexão com timeout zero tenta reservar escrita. Sem a correção, ela consegue e a conclusão falha; a regressão local retornou exatamente o erro de banco ocupado. Não depende de sleeps, sorte de escalonamento ou modelo real.

## Correção e evidência

O caso de uso de escrita agora faz uma atualização neutra do contador do contrato antes de ler o recibo. Isso reserva escrita sem alterar o contador e evita promover uma leitura depois que outra conexão já reservou o escritor. As comparações de versão, recibos idempotentes, histórico e transação atômica continuam nas operações originais. Rede/inferência permanecem fora dessa transação; o timeout não foi aumentado e não há retry automático de inferência.

No teste corrigido, a conexão concorrente recebe o bloqueio esperado, a tentativa original termina e o classificador é chamado uma vez. O teste concorrente anterior foi preservado. Cinquenta testes de extração/conferência passaram após a alteração; a suíte completa da linha funcional mais recente, que inclui também a correção do PR #13, passou com **383 testes em 39,60 s**, além de Ruff/formatação, lock e compatibilidade das 44 dependências.

Esta correção foi aplicada ao PR #12 e carregada pelo PR #13 para não reintroduzir a disputa na etapa seguinte. A aplicação original foi preservada nos demais arquivos; os desvios dos snapshots revisados são essa reserva de escrita, o teste novo e este registro. Cada novo HEAD precisa de CI em Windows/Linux antes do merge. As descrições dos PRs mantêm os resultados finais e a referência à execução que falhou.

Não há migração adicional, troca de regra/prompt/modelo ou nova inferência real. O banco de trabalho permanece em 0005; a reprodução utiliza bancos temporários. A reserva antecipada reduz esta disputa; não promete ausência de bloqueios sob carga nem capacidade de produção.

Fonte primária consultada em 05/11/2026: [SQLite — transações de leitura, escrita e DEFERRED](https://www.sqlite.org/lang_transaction.html). A documentação descreve o mecanismo; os testes acima reproduzem a falha e verificam a correção no ambiente do projeto.
