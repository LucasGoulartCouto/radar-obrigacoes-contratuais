# Validação da validade do método assistido

04/11/2026. Branch `codex/validade-do-metodo`, base `040fb72a4ab8bddec21dd63ca9abc5028783cd99` do PR #12. [PR #13 em rascunho](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/13), snapshot funcional `76b649eca97075246bb6d0b4c0d1d271a135a996`, árvore remota `17eb564137273446bfbb5149f6106d6f7efd6c7e` comparada ao índice local. Correção encontrada na revisão técnica do fluxo existente; não representa revisão independente ou aprovação de Lucas. Este fechamento altera somente README/checkpoint/validação; a descrição do PR identifica HEAD/CI finais.

## Falha reproduzida e resultado esperado

Após selecionar e confirmar uma análise assistida, mudar a identificação do prompt deixava agenda, detalhe, histórico e consultas de eventos/estados tratando a conferência antiga como vigente. A confirmação já rejeitava o método antigo, criando uma inconsistência entre escrita e leitura. Os cinco casos parametrizados de regressão falharam antes da correção.

Outro teste mostrou que uma nova tentativa com método atualizado e as mesmas datas reutilizava a análise antiga, em vez de exigir reconferência. A igualdade dos candidatos não torna dois métodos equivalentes. Esse teste também falhou antes da correção da seleção.

O comportamento exigido já consta na SPEC e no ADR-013: método desatualizado deixa de publicar eventos atuais; registros anteriores continuam no histórico. Nova análise com método atual precisa de seleção, justificativa de substituição e conferência separadas. Reexecução idêntica do mesmo método continua idempotente. Impedimento conhecido mantém sua precedência de bloqueio.

## Implementação e limites

A migração aditiva `0005_analysis_execution` acrescenta referência nullable da análise à execução, com chave estrangeira. Para análises assistidas existentes, recupera o identificador já preservado no payload somente quando execução, contrato e revisão coincidem. Levantamentos manuais ficam sem execução. Nenhuma coluna anterior ou payload é reescrito; referência irrecuperável permanece pendente.

As projeções usam essa referência para comparar o método registrado na execução concluída ao método atual, incluindo prompt, interpretação, regra e hashes dos componentes. A agenda continua uma única consulta de metadados: o teste existente que proíbe carregar texto/payload permanece aprovado. Não usa a última tentativa exploratória como substituta da execução selecionada.

Se o método mudou, a seleção cria outro levantamento mesmo com candidatos iguais, preservando a conferência anterior apenas no histórico. A validação de confirmação também confere a consistência da referência. O caminho manual continua válido independentemente de alterações do classificador.

Não houve mudança em `AVISO_CORRIDOS_V1`, prompt, interpretador, modelo, normalizador ou catálogo de exemplos. Nenhuma inferência real nova ou rodada dos 20 casos; referência automática continua 18/20 antes de correções. Não é avaliação semântica, auditoria completa dos 12 PRs ou escolha de produção.

## Evidências por comportamento

| Comportamento | Cenário e resultado esperado | Evidência |
|---|---|---|
| Cinco leituras alinhadas | Mudar o prompt após confirmação retira eventos atuais e identifica base antiga sem apagar revisão | [test_extractions.py](../tests/integration/test_extractions.py): `test_changed_kernel_invalidates_confirmed_assisted_views`, cinco casos |
| Recuperação com os mesmos candidatos | Novo método/datas iguais cria análise pendente; só nova confirmação publica dois eventos; quatro eventos físicos conservam ambas as conferências | `test_same_candidates_from_new_kernel_require_new_selection_and_review` |
| Caminho manual preservado | Mudar prompt não invalida levantamento manual ou seus eventos | `test_kernel_change_preserves_manual_review_and_its_events` |
| Origem indisponível | Referência ausente ou execução incompleta deixa conferência assistida pendente; confirmação rejeitada | `test_unavailable_selected_execution_never_remains_current`, dois casos |
| Migração com os dois métodos | Preservar todos os valores anteriores e vínculos de conferência; preencher referência assistida; FK rejeitar execução inexistente | `test_execution_metadata_migration_preserves_all_values_and_both_methods` |
| Tela e reconferência | Mudança retira cobertura confirmada, mantém aviso e impede confirmação; nova tentativa/seleção/conferência recuperam o caso | [test_extractions_ui.py](../tests/scenarios/test_extractions_ui.py): `test_method_change_removes_current_events_and_requires_explicit_new_review` |
| Consulta e regressões existentes | Uma leitura de metadados, método idêntico idempotente, falha de tentativa não selecionada preserva conferência válida | [test_agenda.py](../tests/integration/test_agenda.py): `test_read_is_single_metadata_select_and_reference_filters_never_write`; testes existentes em `test_extractions.py` |

**382 testes completos aprovados em 30,30 s (11 casos novos).** `scripts/Validar-Projeto.ps1` aprovou Ruff/formatação, lock e compatibilidade das 44 dependências. O cenário novo de tela passou também isoladamente. A inferência é simulada e os bancos de teste são temporários em arquivo; o resultado não é execução do modelo. Diretórios únicos em `.tools/` foram usados para os temporários; não remover pendências anteriores para repetir testes.

## Atualização do banco de trabalho

Antes de aplicar 0005, consultado o banco de trabalho por conexão somente leitura: esquema 0004, três contratos. Snapshot por conteúdo das nove tabelas preservado fora do Git. O comando documentado `powershell -NoProfile -File scripts/Preparar-Ambiente.ps1` criou backup consistente e aplicou a migração.

Comparados todos os valores das colunas anteriores após migrar e no backup: nenhum mudou. A consulta posterior manteve **três contratos e dois eventos vigentes**, com integridade referencial aprovada. O [registro sanitizado](evidencias/validade-metodo-migracao.json) identifica backup, contagens e hashes, sem registrar textos. Não repetir a preparação sem conferir esse registro e `.tools/validade-metodo/`.

As evidências de reprodução de 02/11 permanecem históricas do snapshot 0004; não alegar que a instalação completa de então foi repetida neste bloco. A revisão de Lucas e qualquer merge continuam separados dos testes e desta atualização local.

Wheel e distribuição de fonte construídos offline e inspecionados: ambos contêm a migração 0005 e o helper de validade; excluem ferramentas/cache/banco. A primeira construção tentou usar cache global sem acesso; a repetição com o cache local documentado concluiu, sem mudar dependências. Verificação documental final: 56 arquivos/430 referências locais e `git diff --check` aprovados.

Fontes primárias consultadas em 04/11/2026: [SQLite — ADD COLUMN e referências nullable](https://www.sqlite.org/lang_altertable.html#alter_table_add_column), [SQLAlchemy — JSON](https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.JSON) e [dialeto SQLite](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#sqlalchemy.dialects.sqlite.JSON). O comportamento usado pela migração foi testado no SQLite local, incluindo upgrade/downgrade com dados; a documentação não substitui esses resultados.
