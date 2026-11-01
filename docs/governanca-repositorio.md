# Governança do repositório

## Situação da fundação

O Git foi inicializado localmente com `main`. A documentação existente foi registrada no commit inicial antes da implementação, e a fundação foi desenvolvida na branch `feat/fundacao-local`. Esse primeiro commit é o bootstrap do repositório, não uma mudança que entrou por PR remoto.

O perfil GitHub conectado informou o usuário `LucasGoulartCouto`. A autoria local utiliza o nome público retornado pelo conector e o endereço de privacidade do GitHub. A configuração foi aplicada somente a este repositório.

Ainda não há repositório remoto criado/publicado por esta entrega. A CI foi escrita para pull requests e atualizações da `main`, mas não executou no GitHub. Não há proteção remota ativada ou bloqueio de merge demonstrado.

## Material preparado

- Fluxo de CI em `.github/workflows/ci.yml`, com verificação em Windows e Linux.
- Dependências resolvidas em `uv.lock` e ambiente isolado.
- Referências das ações de CI fixadas por SHA, conferidas nos repositórios oficiais.
- Permissão da CI limitada à leitura do conteúdo e checkout sem persistir credenciais.
- Modelo de PR e responsável em `CODEOWNERS`.
- `.gitignore` para ferramentas locais, ambientes, bancos, logs e arquivos de segredo.
- Contexto de execução e revisão do agente em `AGENTS.md`.

## Configuração a concluir no GitHub

1. Criar o repositório próprio e publicar o bootstrap da documentação e a branch da fundação.
2. Abrir um PR da fundação e verificar as execuções reais de `qualidade (ubuntu-latest)` e `qualidade (windows-latest)`.
3. Exigir PR para a `main`, verificações obrigatórias, resolução de conversas e bloqueio de force push/exclusão. Conferir os nomes reais dos checks antes de configurá-los como obrigatórios.
4. Aplicar as regras também ao administrador, quando configurável, e verificar seu efeito.
5. Demonstrar que um PR com uma verificação falha não pode integrar a principal.

A revisão humana será feita por Lucas. Não declararemos aprovação independente sem outro revisor real. A política inicial para um projeto individual não deve exigir um aprovador fictício nem produzir um bloqueio impossível de atender.

A publicação do projeto, o PR e os controles remotos devem ter evidências próprias. A presença dos arquivos de configuração na pasta não comprova sua operação no GitHub.

## Referências

- [GitHub: branches protegidas](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
- [actions/checkout v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1).
- [actions/setup-python v7.1.0](https://github.com/actions/setup-python/releases/tag/v7.1.0).
- [astral-sh/setup-uv v10.3.3](https://github.com/astral-sh/setup-uv/releases/tag/v10.3.3).
