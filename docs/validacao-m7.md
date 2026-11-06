# M7 — baseline local e limites da evidência

05/11/2026, America/Sao_Paulo. Execução iniciada às 22:01:30 locais (`2026-11-06T01:01:30Z`). [JSON integral sanitizado](evidencias/m7-baseline-2026-11-05.json), [medidor](../scripts/medir_base_local.py), [proposta](m7-proposta.md).

## Ambiente, origem e reprodução

- Aplicação da `main` em `979bf37d92e975406ca818db9cad76e331dc85f2`, sem mudanças em `src/`. SHA-256 agregado dos caminhos/conteúdos Python em `src/`: `984de18e0973a9d56936b2bf76f7f0c1cf74dbfb056425a73e506e284f1b1163`.
- Medidor novo, SHA-256 `2d9a5618a998c5943826886d03231cdabd6b950d506e84cc2b78e798698fdc14`. O HEAD de origem do JSON identifica a aplicação antes do commit do medidor; seu hash identifica o script efetivamente executado.
- Windows 11 `10.0.26300`, AMD Ryzen 7 6800H, 16 processadores lógicos; modelo lido do registro do Windows. Python 3.14.3, SQLite 3.50.4, SQLAlchemy 2.1.6, Alembic 1.20.1, Streamlit 1.66.1.
- Execução no checkout em D:, bancos novos em pasta única `.tools/m7-*`. RAM física, latência/tipo do disco, energia e carga de outros processos não foram medidos. CIM não estava disponível; não atribuir capacidade da máquina inteira pelo pico do processo.
- Esquema `0005_analysis_execution`, journal `delete`, synchronous `2`, timeout padrão de 5 s, chaves estrangeiras habilitadas. Sem mudar journal/timeouts, tunar banco ou retentar operações.

```powershell
.venv/Scripts/python.exe scripts/medir_base_local.py
# Smoke curto, sem limiares de tempo:
.venv/Scripts/python.exe scripts/medir_base_local.py --sizes 8 --samples 2 --rounds 1 --workers 1 4
```

Cada execução cria pasta nova e não apaga bancos anteriores. Não lê `RADAR_DATA_DIR`; não usa nem migra `var/radar.sqlite3`. Dados e IDs são sintéticos, sem logs de texto/documentos. `resultados.json` fica na pasta criada; somente o JSON sanitizado desta rodada foi copiado para `docs/evidencias/`. Não versionar os bancos.

## Desenho do ensaio

Três carteiras independentes, inseridas pelos serviços reais: 100, 1.000 e 3.000 contratos. Distribuição exata de 25% sem documento, 25% com levantamento pendente, 25% bloqueado por unidade indefinida e 25% conferido com dois eventos. Cada contrato documentado tem um arquivo sintético de 8.192 bytes, uma revisão e um levantamento. Não inclui grande histórico, vazio conferido ou falhas de extração; esses comportamentos têm testes funcionais anteriores, não carga neste experimento.

Seed mede cadastro, recebimento, levantamento manual e confirmação sequenciais separadamente. Não há inferência nem extração automática simulada como se fosse real. Revisor é personagem explícito de simulação.

Uma primeira leitura após o seed é registrada; **não é cache frio**. Depois, para cada limite de 1/4/8 threads, três lotes de 40 leituras: 120 amostras por tamanho/concorrência. Cache do SO não foi limpo. Mesma carteira é reutilizada entre lotes; não são três preparações independentes. Percentis pelo método nearest-rank. Sem intervalo de confiança ou limiar de tempo na CI.

Leituras cronometradas incluem `AgendaService.read` e verificações de carteira/cobertura/IDs/eventos pares, portanto contêm overhead do medidor. Tempo começa quando a tarefa entra em execução; fila do executor não entra na latência. Gerador em ciclo fechado sem pausas; concorrência significa limite de threads, sem barreira que garanta todas iniciando no mesmo instante. Não representa taxa de chegada aberta ou usuários humanos.

Carga mista por carteira: até oito threads, 24 contratos pendentes, duas confirmações com mesmo recibo por contrato e duas leituras intercaladas. Total: 48 confirmações (novas/replays misturados) e 48 leituras. Sem retry. Depois compara recibos bem-sucedidos ao estado persistido, número exato de eventos e histórico; testa também bloqueio por ambiguidade e rejeição de confirmação após nova revisão documental.

## Resultado das leituras

Milissegundos, serviço mais verificações; 120 amostras por linha.

| Contratos | Threads | p50 | p95 | Máximo | Erros de ocupação |
|---|---|---|---|---|---|
| 100 | 1 | 4,646 | 5,747 | 27,952 | 0 |
| 100 | 4 | 19,723 | 27,828 | 36,686 | 0 |
| 100 | 8 | 44,800 | 112,114 | 119,649 | 0 |
| 1.000 | 1 | 21,072 | 27,177 | 44,621 | 0 |
| 1.000 | 4 | 84,467 | 102,770 | 115,486 | 0 |
| 1.000 | 8 | 225,792 | 254,099 | 280,741 | 0 |
| 3.000 | 1 | 72,267 | 87,164 | 98,494 | 0 |
| 3.000 | 4 | 273,962 | 314,722 | 337,232 | 0 |
| 3.000 | 8 | 647,811 | 702,570 | 756,963 | 0 |

Primeira leitura após seed: 8,718 / 21,341 / 82,384 ms, respectivamente. Não inferir benefício de cache comparando uma amostra com um percentil.

## Gravação concorrente e recursos

Tempos em ms; 48 amostras de cada operação por carteira. Confirmações incluem novas e reenvios idempotentes; não estimam tempo de conferência humana.

| Contratos | Confirmação p50 / p95 / máximo | Leitura mista p95 | Ocupação / falhas técnicas | Confirmações únicas |
|---|---|---|---|---|
| 100 | 31,267 / 443,219 / 588,643 | 38,108 | 0 / 0 | 24 |
| 1.000 | 48,342 / 869,086 / 1.458,320 | 77,855 | 0 / 0 | 24 |
| 3.000 | 237,288 / 2.351,993 / 4.170,821 | 265,421 | 0 / 0 | 24 |

**A gravação mista em 3.000 contratos ultrapassa a meta hipotética de p95 ≤ 1 s.** Zero erro não significa latência adequada. Mesmo em 1.000 contratos, o máximo excedeu 1 s. Há indício de contenção/custo de coordenação, mas não houve perfil de locks/SQL/I/O que isole a causa. Não afirmar que PostgreSQL ou WAL já resolveram o problema. Leituras mistas não devem ser comparadas como se houvesse oito leitores dedicados.

| Contratos | Seed parede / CPU (s) | Banco final (MiB) | Pico do processo (MiB) |
|---|---|---|---|
| 100 | 2,374 / 1,422 | 1,89 | 104,38 |
| 1.000 | 23,248 / 14,766 | 17,04 | 115,90 |
| 3.000 | 73,097 / 45,047 | 50,61 | 126,36 |

CPU é tempo de processo, pode ultrapassar tempo de parede com threads. JSON guarda CPU/parede por lote e carga mista. Memória é pico acumulado do processo desde o início, incluindo seed/carteiras anteriores, não delta de uma consulta ou consumo do modelo. Banco final inclui revisões/recibos gerados no ensaio. Não medidos: IOPS, tráfego, CPU de outros processos e tempo/custo da IA.

Seed sequencial p95, em ms:

| Contratos | Cadastro | Documentos | Levantamento manual | Confirmação |
|---|---|---|---|---|
| 100 | 8,483 | 12,020 | 12,828 | 13,398 |
| 1.000 | 7,478 | 10,358 | 10,512 | 10,476 |
| 3.000 | 8,897 | 11,784 | 11,939 | 11,878 |

## Correção, proteção do banco e verificação

Nas três carteiras: cobertura soma a carteira, confirmações concorrentes produzem um único efeito por recibo, sem evento parcial/duplicado; histórico preservado; ambiguidade e base antiga rejeitadas; `foreign_key_check` vazio e `integrity_check = ok`. Não é avaliação independente da extração ou auditoria completa dos seis estados sob carga.

Banco de trabalho: SHA-256 antes/depois da rodada `13e713408e528534fb63cb8cc0e780161dcd649c473061a2c136ea85f60f6d86`, idêntico. Nenhuma escrita/migração/inferência no banco de trabalho. O hash comprova preservação deste arquivo na janela observada, não restauração ou proteção contra alterações futuras.

Quatro novos casos em [test_performance_harness.py](../tests/integration/test_performance_harness.py): smoke com serviços/concorrência/invariantes e banco-sentinela preservado; três entradas inválidas rejeitadas antes de criar banco. Nenhum teste aprova capacidade por tempo. Validação completa via `scripts/Validar-Projeto.ps1`: **387 testes aprovados em 21,23 s**, lock, Ruff/formatação, 63 documentos/478 links locais e dependências compatíveis. Ajustes documentais posteriores exigem nova conferência de links/diff, não nova medição. A CI final fica na descrição do PR M7, vinculada ao HEAD publicado.

## Conclusão com alcance

O desenho atual sustenta as leituras deste ensaio curto, com crescimento de latência e gravação concorrente acima da meta hipotética em 3.000 contratos. Não se mediu saturação máxima, carga longa, histórico grande, interface, rede, autorização ou IA. Próximo experimento deve perfilar leitura/escrita e reproduzir cenário aprovado em protótipo isolado. Nenhuma troca de tecnologia ou prontidão de produção foi validada por estes números.
