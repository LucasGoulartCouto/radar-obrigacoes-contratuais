# Desempenho local — recibos sem escrita e projeção de agenda

07/11/2026. Desenvolvimento autorizado para a versão local L após M7. Base: `cb4bd1f3e7d96e776c75153989513afcfa443ec7`. Mudanças candidatas em branch/PR, sem merge autorizado. [Comparação integral sanitizada](evidencias/contencao-local-2026-11-07.json).

## Problema e mudança

O ensaio M7 mostrou confirmação concorrente lenta. O perfil adicional localizou grande parte da cauda na primeira reserva do escritor, não no cálculo de datas. Na primeira rodada controlada, confirmação p95 de 3.066,155 ms e reserva p95 de 3.064,670 ms. São distribuições relacionadas, não decomposição exata de cada chamada. Commits e leitores também competem; não foram isolados I/O físico, espera interna do SQLite ou CPU como causas únicas.

O executor de conferência/extração reservava escrita e fazia commit mesmo ao apenas devolver um recibo já persistido. A mudança em [reviews.py](../src/radar_contratos/infrastructure/persistence/reviews.py) tem duas etapas:

1. Consultar o recibo imutável pela aplicação numa sessão somente de leitura, encerrada antes de abrir a escrita. Se existir, validar fingerprint e devolver a resposta persistida. Não reservar escritor nem fazer commit. Conflito continua sendo erro.
2. Se não existir, abrir outra sessão/transação, reservar escritor e consultar novamente. Se outro executor tiver concluído no intervalo, devolver o recibo e fazer rollback da reserva neutra. Caso contrário, executar a operação e confirmar atomicamente como antes.

O primeiro recibo lido não é fonte de validade atual de eventos. Reenviar uma operação antiga devolve sua resposta histórica; não recria eventos, muda seleção ou revalida uma base antiga. Operações novas continuam revalidando base, método, evidências e regra. A reserva antecipada da [correção anterior](validacao-concorrencia-gravacao.md) permanece na transação de escrita. Não se promove o snapshot da consulta inicial para escritor.

A [agenda](../src/radar_contratos/infrastructure/persistence/agenda.py) passa a executar sua projeção de colunas por uma conexão SQLAlchemy Core, dispensando o processamento ORM de `Session.execute`. O perfil registrava esse processamento em `loading.py/chunks`. SQL, joins, campos, ordenação, única fotografia de leitura, seis grupos, filtros e tratamento de erro permanecem iguais. Não há paginação/cache nem atalho que deixe contratos fora da cobertura.

Sem nova regra, modelo, prompt, migração, índice, alteração de journal/timeout, lock Python ou retry. Essa mudança não promete que toda leitura/reenvio seja imune a bloqueios: um lock SQLite exclusivo ainda pode bloquear leitura. O cenário verificado permite repetir recibo com outro escritor reservado, sem exigir uma nova escrita.

## Reprodução controlada

```powershell
.venv/Scripts/python.exe scripts/perfilar_contencao_local.py
# Smoke curto:
.venv/Scripts/python.exe scripts/perfilar_contencao_local.py --contracts 8 --rounds 1
```

O [script](../scripts/perfilar_contencao_local.py) cria um seed sintético de 3.000 contratos pelos serviços e seis cópias consistentes em pasta única `.tools/contencao-*`. Não usa `RADAR_DATA_DIR` nem banco de trabalho. Distribuição: 25% sem documento, 25% levantamento pendente, 25% bloqueado por unidade indefinida, 25% conferido com dois eventos. Um documento de 8 KiB/revisão por contrato documentado; sem grande histórico.

Compara exatamente os dois stores de agenda/conferência do commit fixo aprovado acima com os stores candidatos; demais módulos e dependências são os mesmos. Carrega somente código desses arquivos do Git local. Clone raso sem o commit falha antes de criar bancos; obter o histórico antes da reprodução. Não é execução completa do ambiente histórico de M7.

Cada rodada usa o mesmo seed: 24 contratos pendentes, dois pedidos por recibo e duas leituras intercaladas por contrato. São 48 confirmações (novas e replays) + 48 leituras, até oito threads. Três rodadas em ordem baseline/candidato, candidato/baseline, baseline/candidato. Cada variante recebe banco novo com a mesma entrada, sem reaproveitar efeitos da anterior. Não há inferência, UI, rede, usuários reais, retry ou aquecimento/cache frio garantidos. A fila do executor não entra no tempo individual; gerador em ciclo fechado.

Instrumentação: eventos antes/depois de executar SQL, categoria sem parâmetros/textos; medição de `do_commit` no engine isolado; plano `EXPLAIN QUERY PLAN`; cProfile de dez leituras após cada lote. Instrumentação adiciona overhead igual nas variantes. Tempo de SQL execute não inclui consumir todas as linhas. Tempos somados de threads se sobrepõem e não representam parede/CPU. Plano é diagnóstico da versão, sem parser ou dependência operacional de seu formato.

Ambiente: Windows 11 `10.0.26300`, Ryzen 7 6800H/16 CPUs lógicos, Python 3.14.3, SQLite 3.50.4, SQLAlchemy 2.1.6, Alembic 1.20.1, Streamlit 1.66.1. Journal `delete`, synchronous `2`, timeout 5 s. A suíte funcional terminou durante o seed, antes dos seis lotes medidos. Não houve outro teste iniciado durante os lotes; outras atividades do SO não foram controladas. Não medir seed/energia/capacidade total a partir deste ensaio.

JSON registra hashes dos stores baseline/candidato, do script e do seed, versões, parâmetros, seis resultados, perfis, plano e invariantes. SHA-256 do script: `efd605e405dee84a72249d8176a4810eea55dd8b983f1f855b11ec22e792db55`. Percentis nearest-rank, 48 amostras por operação/linha, sem intervalo de confiança.

## Resultados, incluindo os limites

Milissegundos nos percentis; parede do lote em segundos.

| Rodada / variante | Parede | Confirmação p50 / p95 | Leitura p50 / p95 | Commits | Reservas de escritor |
|---|---|---|---|---|---|
| 1 baseline | 3,828 | 81,927 / 3.066,155 | 76,872 / 243,339 | 48 | 48 |
| 1 candidato | 3,086 | 132,694 / 1.481,743 | 138,659 / 216,858 | 24 | 36 |
| 2 candidato | 3,276 | 141,044 / 1.924,310 | 130,083 / 223,753 | 24 | 37 |
| 2 baseline | 3,544 | 81,778 / 1.880,668 | 80,677 / 217,099 | 48 | 48 |
| 3 baseline | 3,575 | 170,280 / 2.363,726 | 76,441 / 182,075 | 48 | 48 |
| 3 candidato | 3,244 | 172,078 / 1.849,917 | 123,831 / 202,334 | 24 | 37 |

**Resultado estrutural verificado:** metade dos commits nos lotes com reenvios. Nem todo replay evita reserva: se o recibo ainda não existia na primeira leitura, precisa reservar e checar de novo. O rollback evita seu commit inútil. Os três lotes candidatos terminaram mais rápido, mas isso não é promessa geral de ganho.

**A meta hipotética de p95 ≤ 1 s continua não atendida.** O p95 candidato ficou entre 1,482 e 1,924 s. Na rodada 2 o p95 de confirmação piorou ligeiramente; p50 e algumas leituras também pioraram. Há consulta inicial adicional nas operações novas e mudança na distribuição da concorrência. Não selecionar somente percentis favoráveis nem chamar a latência geral de corrigida.

Nos seis lotes: sem falha técnica; carteira/cobertura completas, eventos sem duplicação/parcialidade, 24 confirmações únicas por variante, `foreign_key_check` vazio e `integrity_check = ok`. Não houve mudança no banco original do seed entre variantes. O formato não testa chegada aberta, retenção longa, documentos grandes, seis estados sob carga ou inferência.

## Regressões e verificação funcional

| Comportamento | Evidência | Resultado |
|---|---|---|
| Recibo persistido não disputa escrita | `test_persisted_receipt_replays_or_rejects_conflict_while_other_writer_is_reserved`, parametrizado em [test_reviews.py](../tests/integration/test_reviews.py) | Reenvio devolve recibo; outro ator gera conflito, mesmo com escritor reservado; zero DML e contagens idênticas |
| Recibo criado no intervalo é rechecado | `test_receipt_arriving_after_read_is_rechecked_and_reservation_is_rolled_back` no mesmo arquivo | Outra conexão conclui antes da reserva; leitura inicial foi liberada; um efeito, nenhum commit na conexão que apenas encontrou o recibo |
| Escrita continua reservada antes da leitura transacional | `test_finish_reserves_writer_before_reading_receipt` em [test_extractions.py](../tests/integration/test_extractions.py) | Observador distingue a consulta inicial da consulta na transação de escrita; mesma asserção de bloqueio e uma chamada do classificador |
| Agenda mantém projeção e falhas | [test_agenda.py](../tests/integration/test_agenda.py), regressões de método e cenários UI existentes | Uma consulta, sem payload/textos, cobertura/origem/base atual e erro sem carteira vazia preservados |

Os três casos novos foram executados contra `_change` do commit baseline: **3 falhas esperadas**, sem alterar os testes para obter verde (11,44 s). Com a correção: 53 testes de conferência/extração e **390 testes completos aprovados em 29,46 s**, além de lock, Ruff/formatação, dependências e links existentes. O teste antigo de reserva conserva a mesma exigência dentro da transação de escrita; a leitura rápida anterior não faz parte dela. Não há sleeps nem limiar de tempo nos testes de regressão.

Smoke do profiler com 8 contratos/uma rodada aprovado. Após acrescentar esta documentação, reconferir links/diff; CI final do PR é a fonte dos resultados remotos no HEAD publicado. Nenhuma nova inferência real ou teste funcional manual de navegador foi necessário, pois o contrato da interface não mudou e os cenários automatizados passaram.

Banco de trabalho SHA-256 antes/depois: `13e713408e528534fb63cb8cc0e780161dcd649c473061a2c136ea85f60f6d86`, idêntico. Sem migração ou gravação nesse banco.

## Referências e continuidade

Fontes primárias consultadas em 07/11/2026: [SQLite — transações](https://www.sqlite.org/lang_transaction.html), [plano de consulta](https://www.sqlite.org/eqp.html), [SQLAlchemy — perfil de desempenho](https://docs.sqlalchemy.org/en/21/faq/performance.html) e [escopo de sessão/transação](https://docs.sqlalchemy.org/en/21/orm/session_transaction.html). Fundamentam instrumentos e limites; os testes/medições acima são a evidência da aplicação.

Próximo passo após revisão: manter L, observar o volume real do case e perfilar leitura/commit se a concorrência for necessária. WAL, fila de escritor, migrações de índice, PostgreSQL e novas regras não foram adotados para mascarar a cauda. Este bloco entrega reenvio sem escrita e uma projeção mais simples; não conclui a investigação de capacidade.
