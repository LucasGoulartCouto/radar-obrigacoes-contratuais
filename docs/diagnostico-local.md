# Verificar o banco local sem alterar dados

07/11/2026 · Funcionalidade em revisão, dependente do PR #16. Versão local L. [Evidências](evidencias/diagnostico-local-2026-11-07.json).

## Uso

Na pasta do projeto, com o ambiente já instalado:

```powershell
.tools/bootstrap/Scripts/uv.exe run --locked radar check-db
# Opcional: orçamento de consulta diferente do padrão de 10 segundos
.tools/bootstrap/Scripts/uv.exe run --locked radar check-db --timeout 20
```

O comando usa `RADAR_DATA_DIR` da sessão, como a aplicação. Sem essa variável, consulta `var/radar.sqlite3`. Não carrega `.env`. Não cria diretórios/banco, não executa migração, correção ou restauração e não chama IA. Não requer iniciar Streamlit.

Saída normal:

```text
Esquema básico: OK
Integridade estrutural rápida: OK
Chaves estrangeiras: OK
Restrições CHECK do modelo: OK
Verificação concluída em modo somente leitura.
```

Código de saída **0** quando todas as verificações concluem com sucesso. Código **1** quando há pendência, falha de acesso, banco ausente/inválido ou orçamento excedido. Uma falha interrompida não é resultado vazio nem sucesso. Nenhuma correção é automática. Preserve arquivo e backups antes de decidir uma recuperação.

## O que cada resultado significa

| Resultado | Verificação executada | Limite |
|---|---|---|
| Esquema básico | Uma versão Alembic igual à esperada, tabelas e colunas exigidas pelo modelo | Não compara todo DDL, tipos, índices ou definições das constraints |
| Integridade estrutural rápida | `PRAGMA quick_check(1)` | Não substitui `integrity_check` completo; UNIQUE e correspondência de índices não são verificados por esse pragma |
| Chaves estrangeiras | `PRAGMA foreign_key_check`, sem apresentar identificadores/linhas | Verifica relações declaradas no arquivo, não inventa constraints ausentes |
| CHECKs do modelo | Consultas de existência de violações das expressões `CheckConstraint` versionadas no código | Não valida semântica dos contratos, qualidade de extração, auditoria ou todas as regras de negócio |

Quando o esquema básico não corresponde ao esperado, os CHECKs aparecem como **NÃO VERIFICADO**, sem tentar aplicar o modelo atual a tabelas/colunas incompatíveis. Isso mantém o código de saída 1. Não exibir o valor da versão encontrado: ele pode ser dado não confiável.

Na fixture local com SQLite 3.50.4, um `record_version=0` inserido com checagem temporariamente desabilitada passou no quick_check da conexão somente leitura. A consulta explícita dos CHECKs detectou a violação. Essa observação é restrita ao ambiente ensaiado; não presumimos sua causa ou comportamento idêntico em toda distribuição SQLite. Os dois resultados ficam separados, e a violação impede sucesso global. Não foi removido o teste para obter verde.

## Implementação e proteção

[health.py](../src/radar_contratos/infrastructure/persistence/health.py) abre uma conexão SQLite `mode=ro`, sem compartilhar sessão da interface. `autocommit=False` inicia a transação de leitura; versão, estrutura, FKs e CHECKs são observados no mesmo snapshot. Nomes/expressões das consultas de CHECK vêm do modelo versionado, sem executar SQL recebido do banco/documentos.

O limite é cooperativo: há verificações de relógio entre etapas e um progress handler a cada 1.000 instruções SQLite. Espera por lock é limitada a até 5 s ou ao orçamento menor informado. Não é promessa de interrupção instantânea de toda operação do sistema operacional. Orçamento não positivo, infinito ou NaN é rejeitado antes da abertura.

O diagnóstico pode manter uma leitura e disputar acesso com escritores enquanto executa. Banco ocupado gera mensagem segura; não há retry automático. Não muda journal, não usa `immutable=1` e não ignora locks para produzir resultado rápido.

Mensagens/saída não contêm contratos, nomes de fornecedores, IDs de linhas, SQL ou detalhes do driver. Falhas reaproveitam a tradução segura do PR #16, com operação/código SQLite no log. A saída técnica é voltada ao operador e não foi incluída no fluxo de conferência da pessoa usuária.

## Validação executada

Base: `b16e12f8874b0b89221fcf61eb8de6983c555705` do PR #16. O PR #15 não está integrado; esta branch depende de #16 e não inclui as três regressões próprias de #15.

| Cenário | Evidência | Resultado |
|---|---|---|
| Banco preparado, ausente e arquivo inválido | [test_database_health.py](../tests/integration/test_database_health.py) | Estado correto, sem criação de pasta/arquivo ausente, bytes preservados e erro sanitizado |
| Versão correta com tabela/coluna faltando | Mesmo arquivo | Esquema básico falha; não há sucesso por confiar apenas no marcador de versão |
| FK órfã e CHECK violado | Mesmo arquivo | Pendências detectadas sem reparo; hashes idênticos antes/depois da verificação |
| Somente leitura real | Tentativa controlada de `CREATE TABLE` na conexão do diagnóstico | SQLite rejeita com `SQLITE_READONLY`; transação de leitura ativa; arquivo preservado |
| Orçamento inválido, deadline entre etapas e consulta longa | Testes determinísticos, sem sleeps | Rejeição antes da abertura; progress handler aborta consulta antes de concluí-la; timeout não é convertido em erro de acesso |
| Lock exclusivo real | Fixture mantém lock; conexão de teste usa espera zero | `StorageBusyError` sem retry ou alteração do arquivo |
| CLI válido, ausente, versão não confiável, FK e CHECK | [test_database_health_cli.py](../tests/integration/test_database_health_cli.py) | Códigos 0/1 corretos, sem traceback/valores privados e sem migração/reparo |

**21 casos novos aprovados em 6,01 s; 421 testes completos em 24,99 s**, com Ruff/formatação, lock e dependências compatíveis. Após documentação, conferir links/diff; resultado remoto do HEAD final fica na descrição do PR.

Wheel/sdist construídos offline e inspecionados: novo módulo e migrações presentes, sem banco/ambiente/cache/ferramentas. Smoke com wheel extraído em pasta temporária, ambiente Python/dependências já existentes, importação confirmada daquela cópia e entrypoint `radar` conferido. Banco sintético válido retornou 0; CHECK violado e banco ausente retornaram 1. Hash preservado em cada comando; pasta ausente não foi criada. Isso não é instalação limpa em outra máquina.

Banco de trabalho manteve SHA-256 `13e713408e528534fb63cb8cc0e780161dcd649c473061a2c136ea85f60f6d86`. Não executamos `check-db`, migração, inferência ou escrita nele; os ensaios usaram somente fixtures e diretórios temporários. Hashes do código/testes e saída sanitizada do smoke estão no JSON.

Este diagnóstico não certifica prontidão de produção, qualidade dos eventos, backup restaurável ou integridade semântica. Restauração continua uma operação separada. PRs #15/#16 e o novo PR aguardam revisão, sem merge autorizado.

Fontes primárias consultadas em 07/11/2026: [PRAGMAs de diagnóstico](https://www.sqlite.org/pragma.html#pragma_quick_check), [URI somente leitura](https://www.sqlite.org/uri.html), [CHECKs e seus limites](https://www.sqlite.org/lang_createtable.html#check_constraints) e [progress handler no Python](https://docs.python.org/3.14/library/sqlite3.html#sqlite3.Connection.set_progress_handler). As fontes fundamentam mecanismos; os resultados do Radar são os testes/smoke descritos acima.
