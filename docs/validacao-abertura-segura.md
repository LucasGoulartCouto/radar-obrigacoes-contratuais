# Abertura local e falhas da lista de contratos

07/11/2026 · Base `cb4bd1f3e7d96e776c75153989513afcfa443ec7` da `main`, com 387 testes. Branch independente `codex/abertura-segura`. [Evidência sanitizada](evidencias/abertura-segura-2026-11-07.json). O PR #15 continua preservado e sem merge; suas três regressões não fazem parte da contagem desta branch.

## Problema reproduzido

A abertura da aplicação usava o mesmo modo de conexão que a preparação. Ao apontar para uma pasta ainda não preparada, criava pasta/arquivo SQLite vazio antes de informar que faltava esquema. Um arquivo inválido podia expor a exceção do driver em vez de uma orientação legível. A lista de contratos também deixava escapar falhas de banco, e a tela não tratava o erro desse caso de uso.

Antes da correção, o primeiro conjunto de integração teve **7 falhas e 1 aprovação em 0,44 s**: criação implícita, banco inválido e cinco falhas de leitura. O caso positivo com caminho contendo caracteres especiais já passava. As falhas foram mantidas como regressões; não são evidência de problema de dados reais.

## Comportamento implementado

- `build_service` solicita `make_engine(..., create_if_missing=False)`. Nesse modo, a conexão usa URI SQLite com `mode=rw`: exige arquivo existente e permite as operações normais no banco preparado. Não cria diretório/arquivo ao iniciar ou se o arquivo for movido antes da conexão.
- O caminho é construído com URI absoluta codificada, preservando espaço, acentos, `#`, `%` e `&`. O teste positivo cadastra e consulta no banco preparado com esse nome e verifica chaves estrangeiras habilitadas.
- `init-db` e a preparação continuam usando o modo de criação explícita existente. Sem migração nova, recriação, alteração de journal/timeout ou limpeza automática de arquivo inválido.
- A verificação do esquema e a leitura da lista convertem erros DBAPI em `StorageBusyError` ou `StorageUnavailableError`. Erros de caminho anteriores à criação do engine também recebem mensagem segura. Falta de esquema continua sendo `DatabaseNotReadyError`.
- A UI captura `RadarError` da lista, apresenta a mensagem e interrompe a área que depende dela. Não apresenta uma falha como lista vazia, não sugere cadastrar o primeiro contrato e não oferece edição de um contrato não carregado. O formulário inicial de cadastro continua uma área independente, como antes.
- Ao remover a falha e recarregar, a lista e seus formulários voltam com os dados preservados. Não há retry automático nem recuperação destrutiva.

As dependências continuam na direção existente: tipos de erro sem SDK em `errors.py`, tradução do driver na infraestrutura e apresentação de `RadarError` na UI. Não importar SQLAlchemy na apresentação nem colocar tratamento de arquivo no domínio.

O logger dos caminhos tratados emite apenas operação, resultado e código SQLite primário. Código estendido de ocupado é classificado pelo byte inferior. Não registra SQL, parâmetros, caminho, mensagem do driver ou texto documental. A causa técnica permanece encadeada para depuração controlada; isso não equivale a redigir toda exceção possível do programa.

## Testes por comportamento

| Cenário | Teste/evidência | Resultado |
|---|---|---|
| Pasta/banco ainda não preparados | `test_opening_unprepared_app_does_not_create_directory_or_database`, em [test_startup_failures.py](../tests/integration/test_startup_failures.py) | Erro de aplicação, sem criar pasta/arquivo |
| Banco inválido | `test_invalid_database_is_preserved_and_reported_without_driver_details`, no mesmo arquivo | Bytes idênticos, mensagem e logs sem detalhes de driver/caminho |
| Arquivo movido entre engine e conexão | `test_database_moved_after_engine_creation_is_not_recreated` | Erro seguro; arquivo movido preservado, caminho antigo não recriado |
| Erro de caminho/permissão | `test_path_failure_before_engine_creation_does_not_expose_details` | Falha simulada antes do engine vira mensagem do Radar, sem marcador privado |
| Banco preparado com nome especial | `test_existing_database_with_uri_characters_remains_writable` | Escrita/leitura reais, mesmo arquivo, integridade referencial ativa |
| Ocupado, bloqueado, ocupado estendido, I/O e arquivo inválido durante lista | `test_catalog_failures_are_sanitized_not_empty_and_recoverable`, cinco parâmetros | Erro tipado; não retorna vazio; logs/mensagem sem SQL/parâmetros; nova leitura recupera dados e hash |
| Tela sem banco e com banco inválido | Teste de ambiente não preparado ampliado e `test_invalid_database_is_presented_without_traceback_or_overwrite`, em [test_foundation_ui.py](../tests/scenarios/test_foundation_ui.py) | AppTest sem exceção técnica; erro visível; arquivo ausente não criado e inválido não alterado |
| Falha da lista e recuperação da tela | `test_catalog_error_is_not_empty_portfolio_and_reload_recovers`, dois parâmetros | Sem traceback, falso vazio ou seletor de edição; após recarga os contratos reaparecem |

São **13 casos novos**: dez de integração e três de interface, além do teste existente de ambiente não preparado ampliado. AppTest executa o fluxo Streamlit e verifica os elementos; não é uma nova demonstração manual em navegador.

## Verificação executada

`scripts/Validar-Projeto.ps1`: **400 testes aprovados em 33,10 s**, lock, Ruff/formatação e dependências compatíveis. Depois dos documentos, reconferir links/diff; a descrição do PR registra HEAD e CI finais.

Wheel e sdist construídos offline e inspecionados: novo módulo `read_errors.py` presente; sem banco, `.tools`, `.venv` ou `.uv-cache`. Os avisos de cache local/hardlink do build não alteraram os pacotes; o conteúdo foi conferido. Não houve nova instalação no ambiente do operador.

Compatibilidade com #15: cópia temporária do código/testes desta branch, com os quatro arquivos funcionais/testes do HEAD `4f11d48819e7dd53f43d0bbf7613bdcbcd295199` sobrepostos. Importação confirmada da cópia, bancos temporários; **403 testes aprovados em 33,12 s**. Manifesto/hashes na evidência. Não houve merge, nova CI combinada ou aprovação de Lucas desses diffs. A combinação deve ser reconferida se qualquer PR mudar.

Banco de trabalho: SHA-256 antes/depois `13e713408e528534fb63cb8cc0e780161dcd649c473061a2c136ea85f60f6d86`, idêntico. Sem migração, escrita, inferência ou restauração nesse banco. Somente fixtures sintéticas foram criadas/movidas para os testes.

## Alcance e continuidade

Este bloco cobre abertura/verificação de esquema e leitura da lista, incluindo sua apresentação. Não promete recuperação de corrupção, restauração, disponibilidade de disco ou tratamento completo das falhas de todas as escritas/leituras documentais. Erros não se tornam resultados vazios; arquivo inválido permanece preservado para diagnóstico/backup.

RF-04/RF-07 e os limites de simulação continuam vigentes. Nenhuma alteração de extração, cálculo, confirmação ou modelo. Próximo passo: revisão do novo PR por Lucas; #15 continua independente, sem merge autorizado.

Fontes primárias consultadas em 07/11/2026: [URI SQLite e modos de abertura](https://www.sqlite.org/uri.html), [conexões URI no SQLAlchemy](https://docs.sqlalchemy.org/en/21/dialects/sqlite.html#uri-connections) e [erros DBAPI](https://docs.sqlalchemy.org/en/21/errors.html#dbapi-errors). Os mecanismos documentados orientam a implementação; a evidência do Radar está nos testes acima.
