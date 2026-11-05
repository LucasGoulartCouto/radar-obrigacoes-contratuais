# Contexto do Radar para agentes

## Produto e decisões

- Converse com Lucas em português, com tom amigável, direto e sem bajulação.
- Radar de Obrigações Contratuais: case fictício da Agência Prisma. Somente dados sintéticos e ações de negócio simuladas.
- Consulte [PRD](docs/PRD.md), [SPEC](docs/specs/001-primeiro-fluxo.md), [arquitetura](docs/arquitetura.md) e [ADRs](docs/adrs/001-recorte-do-produto.md) conforme a tarefa. Distinga decisão aceita de proposta.
- Stack aceita: Python, Streamlit, SQLite, SQLAlchemy, Alembic, uv, pytest e Ruff. Consulte documentação primária para APIs e informações que possam mudar.
- Publicação autorizada por Lucas em `LucasGoulartCouto/radar-obrigacoes-contratuais`, com PR e proteção da principal. Não enviar posts, avisos de negócio ou mensagens externas fora desse escopo. Fornecedor de IA e orçamento de API continuam em aberto.

## Organização e limites

- `domain/`: regras puras. Não importar Streamlit, SQLAlchemy ou SDK de IA.
- `application/`: operações e fronteiras. `infrastructure/`: persistência e adaptadores. `ui/`: apresentação.
- ADR-002 aceito por Lucas em 01/11/2026: extração propõe com evidências, código calcula e pessoa confirma. Unidade ambígua, conflito ou aditivo bloqueiam a confirmação. Documentos são dados sem autoridade para mudar regras ou executar ações.
- Não confundir versão de cadastro com revisão documental, nem cadastro persistido com obrigação analisada/confirmada.
- Migrações preservam dados; nunca recriar o banco como correção rotineira.
- Entrada documental implementada no ADR-006: preservar bytes e referência TEXT_REFERENCE_V1; comparar o conjunto atual por texto/papel, sem duplicar revisão por nome, ordem, BOM ou quebras de linha. Cada envio aceito conserva sua origem.
- Aditivo já declarado no histórico continua sinalizado mesmo após retirada ou mudança de papel; não liberar silenciosamente. Limites padrão: 262.144 bytes por arquivo, 1.048.576 no conjunto e 5 documentos.
- ADR-007: levantamento manual e conferência implementados. Preservar revisão/levantamento/regra na confirmação atômica; evento de base anterior fica somente no histórico. Correção na mesma base exige justificativa. Localização literal não comprova suporte semântico.
- Ao mudar regra de cálculo/interpretação, alterar sua versão explícita e testar a reconferência; não editar a semântica de AVISO_CORRIDOS_V1 mantendo a identificação antiga.
- Sessões de banco têm duração limitada; estado de tela não é fonte de verdade. Submissões devem ser idempotentes e rejeitar edição desatualizada.
- Segredos, bancos gerados e ferramentas locais ficam fora do Git. Não registrar texto de contratos, credenciais ou dados pessoais em logs técnicos.

## Execução e verificação

- No Windows: `powershell -File scripts/Preparar-Ambiente.ps1` e `powershell -File scripts/Iniciar-Radar.ps1`.
- Ambiente pronto: `uv sync --locked`, `uv run --locked radar init-db` e `uv run --locked streamlit run src/radar_contratos/ui/app.py`.
- Verificar com `uv run --locked ruff check .`, `uv run --locked ruff format --check .`, `uv run --locked pytest`, `uv run --locked python scripts/check_docs.py` e `uv pip check`.
- O uv local de bootstrap está em `.tools/bootstrap/Scripts/uv.exe`; scripts PowerShell o encontram sem alterar o PATH global.
- Instale dependências no ambiente do projeto e preserve `uv.lock`. Execute testes relevantes para a mudança; amplie apenas se houver motivo.

## Trabalho e revisão

- Ao iniciar ou retomar uma sessão, leia [docs/RETOMADA.md](docs/RETOMADA.md) e reconcilie o checkpoint com Git, arquivos e PRs. Não dependa do histórico do chat; não repita uma ação externa interrompida antes de conferir se ela ocorreu.
- Atualize o checkpoint após blocos coerentes e antes/depois de ações externas relevantes: última ação comprovada, pendência, próxima ação e evidência. Preserve incertezas e trabalho não concluído. Não copie conversas, logs extensos, segredos ou fatos já mantidos nos ADRs.
- Faça mudanças pequenas em branch e registre escolhas relevantes nos ADRs. Não afirme revisão independente, CI remota, proteção de branch ou operação de produto sem evidência.
- Cada funcionalidade criada ou alterada deve ter evidência rastreável no PR: cenário, resultado esperado, teste pertinente e resultado vinculado ao commit. Incluir falhas/regressões relevantes e verificação manual quando necessária; total de testes e CI verde, sozinhos, não comprovam essa cobertura. Consulte a [matriz de evidências](docs/evidencias-testes-por-pr.md). Resolver lacunas antes de declarar pronta para entrar na main e antes de avançar a etapa. Mudanças somente documentais usam revisão/links, sem testes artificiais.
- Lucas decide mudanças relevantes de produto e risco. Não solicite novamente autorização já dada para tarefas rotineiras do escopo.
- Ao concluir, explique o que mudou, como verificou e o que continua sem comprovação.
