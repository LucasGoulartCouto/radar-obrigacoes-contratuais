# Fluxo de trabalho dos agentes

Use ao implementar ou corrigir. O estado vigente fica no [checkpoint](../RETOMADA.md); critérios de publicação e conclusão, em [qualidade e evidências](qualidade-e-evidencias.md).

## Antes de alterar

Identifique o comportamento esperado no [PRD](../PRD.md), na [SPEC](../specs/001-primeiro-fluxo.md) e no ADR afetado. Leia somente o necessário para a tarefa. Proposta não vira decisão aceita por constar na documentação; mudanças relevantes de produto e risco cabem a Lucas.

Compare Git local, diff pendente e estado remoto antes de criar ou publicar trabalho. Faça mudanças pequenas em branch; preserve trabalho anterior. Registre escolhas relevantes nos ADRs e mantenha resultados de execução separados das decisões. Ao reorganizar documentação, preserve caminhos referenciados ou atualize consumidores conhecidos.

## Implementação

Stack aceita: Python, Streamlit, SQLite, SQLAlchemy, Alembic, uv, pytest e Ruff. Consulte fontes primárias para APIs e informações que possam mudar. Instale dependências no ambiente do projeto e preserve `uv.lock`.

Respeite a [arquitetura](../arquitetura.md):

- `domain/` contém regras puras; não importa Streamlit, SQLAlchemy ou SDK de IA.
- `application/` contém operações e fronteiras; `infrastructure/`, persistência e adaptadores; `ui/`, apresentação.
- Sessões de banco têm duração limitada. Submissões são idempotentes e rejeitam edição desatualizada; estado de tela não substitui leitura da base.
- Migrações preservam dados. Não recrie o banco como correção rotineira.

Antes de alterar interpretação ou cálculo, consulte os [limites e invariantes](seguranca-e-limites.md) e a decisão de origem. Mudança semântica exige nova versão explícita da regra e teste de reconferência; não reutilize `AVISO_CORRIDOS_V1` com outro significado.

## Conclusão de um bloco

Execute verificações pertinentes, resolva falhas causadas pela mudança e ligue os resultados ao diff/commit. Atualize o checkpoint com última ação comprovada, pendência, próxima ação e evidência, inclusive antes/depois de publicação. Preserve incertezas em vez de inferir sucesso.

Ao concluir, explique o que mudou, como verificou e o que continua sem comprovação. Rotinas já autorizadas não precisam de nova permissão; ampliação de escopo, risco relevante e decisões comerciais continuam com Lucas.
