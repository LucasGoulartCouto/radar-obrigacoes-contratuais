# Governança do repositório

**Atualização em 05/11/2026:** Lucas informou validação funcional, revisão dos PRs #1–#13 e autorização de integração. [Registro e alcance](entrega/aceite-funcional.md). O resultado/HEAD/CI finais ficam na descrição do PR #13; conferir a plataforma antes de repetir integrações. O histórico original está preservado em `codex/arquivo-pre-integracao-20261105`. A consulta da `main` nesta retomada confirmou proteção habilitada e os dois checks obrigatórios; isso não reaudita todos os controles administrativos descritos no histórico abaixo.

## Histórico da fundação

O Git foi inicializado localmente com `main`. A documentação existente foi registrada no commit inicial antes da implementação, e a fundação foi desenvolvida na branch `feat/fundacao-local`. Esse primeiro commit é o bootstrap do repositório, não uma mudança que entrou por PR remoto.

O perfil GitHub conectado informou o usuário `LucasGoulartCouto`. A autoria local utiliza o nome público retornado pelo conector e o endereço de privacidade do GitHub. A configuração foi aplicada somente a este repositório.

O [repositório público](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais) foi criado após autorização de Lucas. O [PR #1](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/1) permanece aberto para sua revisão. A CI foi executada em Windows e Linux, e a proteção da `main` foi ativada e verificada, conforme o [registro de publicação](validacao-publicacao.md).

A publicação foi feita pelo conector GitHub. Isso gerou identificadores de commit remotos diferentes dos originais locais; as árvores de arquivos foram comparadas e são idênticas. Os commits originais foram preservados em `local/bootstrap-documentacao` e `local/fundacao-original`. As branches de trabalho passaram a acompanhar o histórico remoto, sem descartar conteúdo.

## Material preparado

- Fluxo de CI em `.github/workflows/ci.yml`, com verificação em Windows e Linux.
- Dependências resolvidas em `uv.lock` e ambiente isolado.
- Referências das ações de CI fixadas por SHA, conferidas nos repositórios oficiais.
- Permissão da CI limitada à leitura do conteúdo e checkout sem persistir credenciais.
- Modelo de PR e responsável em `CODEOWNERS`.
- `.gitignore` para ferramentas locais, ambientes, bancos, logs e arquivos de segredo.
- Contexto de execução e revisão do agente em `AGENTS.md`.

## Controles ativos no GitHub

1. A `main` exige PR e os checks `qualidade (ubuntu-latest)` e `qualidade (windows-latest)`, aceitando resultados do GitHub Actions.
2. A branch precisa estar atualizada com a principal, e conversas precisam ser resolvidas.
3. Histórico linear é exigido; force push e exclusão da principal permanecem desabilitados.
4. As regras também se aplicam ao administrador. A API da branch confirmou checks com nível de aplicação `everyone`.
5. A prova negativa falhou intencionalmente nos dois ambientes. O GitHub informou `mergeable_state: blocked`, com o botão de integração desabilitado. O arquivo da prova foi removido e não alterou a `main`.

A revisão humana cabe a Lucas, que declarou a revisão dos PRs #1–#13 em 05/11/2026. Não declararemos aprovação independente sem outro revisor real. A política inicial para um projeto individual não deve exigir um aprovador fictício nem produzir um bloqueio impossível de atender.

Na fundação, a revisão de Lucas e a integração permaneciam pendentes. A autorização posterior está registrada na abertura deste documento. As [evidências remotas da fundação](validacao-publicacao.md) identificam as execuções observadas naquele momento e distinguem revisão humana dos checks automáticos.

## Evidências por funcionalidade

Lucas definiu que cada PR destinado à main deve demonstrar o teste das funcionalidades criadas ou alteradas antes de avançarmos a etapa. A [matriz dos quatro PRs](evidencias-testes-por-pr.md) liga os comportamentos aos testes e registros de execução, com commits e CI identificados.

O modelo de PR exige cenário, resultado esperado, teste/evidência e resultado vinculado ao commit. Evidências manuais complementam a suíte quando a operação requer navegador, instalação ou configuração. Mudanças apenas documentais passam por revisão e links; não criamos testes que apenas repitam a implementação.

Essa rastreabilidade é conferida na revisão. Os checks obrigatórios executam a suíte, mas não provam automaticamente que cada funcionalidade recebeu um teste adequado. Quantidade de testes não é percentual de cobertura nem aprovação humana. Uma lacuna deve ser resolvida antes de declarar o PR pronto para integrar e antes de avançar o desenvolvimento funcional.

Os PRs encadeados serão reconferidos ao apontar para a main, incluindo diff e CI da versão final. Nenhum merge foi autorizado por essa definição de evidências.

## Referências

- [GitHub: branches protegidas](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
- [actions/checkout v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1).
- [actions/setup-python v7.1.0](https://github.com/actions/setup-python/releases/tag/v7.1.0).
- [astral-sh/setup-uv v10.3.3](https://github.com/astral-sh/setup-uv/releases/tag/v10.3.3).
