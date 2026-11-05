# Validação da documentação dos agentes

Data: **01/11/2026**. Mudança exclusivamente documental, baseada em `e0ea2c8285bdbe7c17e99741d97e92910f3e263f` (PR #5). O commit final e a execução remota devem ser vinculados na descrição do PR desta reorganização; não há mudança na aplicação, no banco ou nas regras.

## Inventário e preservação

| Origem | Destino mantido | Verificação |
|---|---|---|
| AGENTS: produto, limites gerais e mapa | [AGENTS.md](../AGENTS.md) | Contexto sintético, confirmação humana, fronteiras e autorização continuam na entrada |
| AGENTS: camadas, stack, sessões, idempotência e migrações | [Fluxo de trabalho](agents/fluxo-de-trabalho.md) | Proibição de dependências em domain, edição desatualizada, preservação dos dados e lock mantidos |
| AGENTS: invariantes de ADR-002/006/007/008 e versão da regra | [Segurança e limites](agents/seguranca-e-limites.md) | Comparados com o AGENTS da base; nenhuma regra removida ou mudada |
| AGENTS: comandos/checks, evidências e publicação | [Qualidade e evidências](agents/qualidade-e-evidencias.md) | Cinco checks, teste por comportamento, revisão de Lucas e ausência de merge inferido mantidos |
| RETOMADA: protocolo e limites da persistência | [Continuidade](agents/continuidade.md) | Procedimento separado do estado; pausa histórica preservada, retomada atual explícita |
| agent-harness: ferramenta, mecanismos e direção humana | [Harness](agents/harness.md) | Caminho antigo mantém ponte; afirmação de proteção remete à evidência histórica |
| RETOMADA: pendência local, histórico, PRs e próximos passos | [Checkpoint](RETOMADA.md) | Pendência anterior preservada na branch própria; PRs #1–#5 abertos, base/HEAD conferidos pelo conector |
| PRD/SPEC/ADRs, registros de validação e matriz dos PRs | Caminhos anteriores | Sem alterações; referências históricas a commits preservadas |

Fontes oficiais abertas nesta sessão e distinção entre recomendações e escolhas locais estão em [fontes e organização](agents/fontes-e-organizacao.md).

## Percursos de leitura

Procedimento: ler o mapa da raiz, escolher a rota da tarefa, abrir os destinos indicados e comparar o conteúdo com o resultado esperado abaixo. Revisão documental realizada pelo próprio agente nesta sessão; não é execução por outro modelo ou uma nova sessão automática.

| Tarefa simulada | Percurso a partir do mapa | Resultado observado |
|---|---|---|
| Retomar após publicação interrompida | Checkpoint → continuidade | Encontra comparação local/remota antes de repetir ação, preservação de alterações e registro de incerteza |
| Corrigir edição desatualizada | Fluxo → arquitetura; limites → ADR-005 | Encontra sessões limitadas, idempotência e rejeição de sobrescrita; migração não recria banco |
| Alterar identidade do conjunto documental | Limites → ADR-006 | Encontra bytes, TEXT_REFERENCE_V1, texto/papel, reenvios, limites e aditivo histórico persistente |
| Mudar cálculo/confirmação | Limites → ADR-002/007 e SPEC | Encontra nova versão de regra, reconferência, confirmação atômica, justificativa e bloqueios |
| Corrigir agenda vazia ou leitura com erro | Limites → ADR-008 | Encontra cobertura independente de filtros, pendentes, uma consulta e proibição de zerar cobertura por erro |
| Revisar/publicar documentação | Qualidade → governança/modelo de PR | Encontra revisão/links e evidências pertinentes, sem testes artificiais ou merge inferido |
| Avaliar criação de skill | Harness → fontes | Distingue guia comum de SKILL.md; não presume carregamento automático nem troca modelo/configuração |

Todos os percursos encontraram as regras indicadas. Os destinos dos ADRs foram lidos no recorte pertinente para conferir que continuam sendo as decisões de origem.

## Checks e alcance

- `uv run --locked python scripts/check_docs.py`: **35 arquivos e 236 links locais verificados**, sem falhas nesta versão; execução final vinculada ao commit no PR.
- `git diff --check`: sem erros de whitespace no diff revisado.
- Revisão dos links com fragmento novos/alterados: títulos de continuidade e pontes conferidos. O script não valida âncoras.
- Diff restrito a Markdown; sem alteração em código, testes, dependências, configuração, migrations ou banco. `uv.lock` preservado.
- A suíte da aplicação não foi reexecutada localmente por esta alteração documental. A [CI do commit 7957473](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/actions/runs/41354304508) passou em Windows/Linux, incluindo os checks de código, testes, links e dependências. Este fechamento documental altera o HEAD; a execução final e seu SHA ficam na descrição do [PR #6](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/6).

Não foi validada a descoberta automática em um novo processo do Codex, nem medido ganho de tempo, custo ou qualidade. A documentação oficial descreve o mecanismo; esta conferência verifica o mapa e o conteúdo no repositório. Não houve revisão independente nem revisão humana real de Lucas nesta sessão. Extração automática e C20 completo continuam pendentes.
