# Qualidade, evidências e publicação

Use ao testar, revisar ou publicar. O [modelo de PR](../../.github/PULL_REQUEST_TEMPLATE.md), a [matriz de evidências](../evidencias-testes-por-pr.md) e a [governança](../governanca-repositorio.md) mantêm o formato e as evidências anteriores.

## Verificação adequada à mudança

Para código, execute testes pertinentes; amplie quando houver falha, dependência afetada ou dúvida concreta. Comandos disponíveis:

```powershell
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
uv run --locked python scripts/check_docs.py
uv pip check
```

`powershell -File scripts/Validar-Projeto.ps1` reúne esses checks e verifica o lock. Quando `uv` não estiver no PATH, os scripts encontram `.tools/bootstrap/Scripts/uv.exe`. Use o ambiente do projeto; preserve `uv.lock`.

Em mudança somente documental, revise o diff, referências e links locais com `check_docs.py`. Ao mudar o mapa de instruções, percorra cenários representativos de leitura e registre onde cada tarefa encontra suas regras. Não crie testes artificiais nem alegue nova execução local da suíte da aplicação. O verificador confirma arquivos de destino; não valida âncoras, conteúdo ou carregamento automático de instruções.

## Evidência por funcionalidade

Cada funcionalidade criada ou alterada precisa de cenário, resultado esperado, teste pertinente e resultado vinculado ao commit no PR. Inclua sucesso, falhas/regressões relevantes e verificação manual quando necessária, com procedimento, alcance e resultado. Resolva lacunas antes de declarar pronta para entrar na main e antes de avançar a etapa.

Total de testes ou CI verde não comprova cobertura por funcionalidade. Gabarito sintético íntegro não comprova extração, trecho literal não comprova suporte semântico e demonstração pelo agente não representa revisão humana real. As evidências precisam continuar válidas quando mudar código, base ou HEAD.

## Publicação e revisão

Publicar branches e PRs no repositório do Radar está autorizado. Antes de uma operação externa, confira se já ocorreu e atualize o [checkpoint](../RETOMADA.md). Confira seu resultado depois de executá-la. As descrições dos PRs devem apontar para a versão e evidências finais.

PRs encadeados exigem reconferência de base, diff e CI ao integrar os anteriores. Não faça merge por inferência de pedido genérico para continuar. Lucas revisa; não declare aprovação independente, proteção atual da principal ou CI remota sem evidência correspondente. Registros anteriores comprovam observações identificadas por data/commit, sem garantir estado remoto permanente.
