# Continuidade entre sessões

Use ao retomar, interromper ou publicar trabalho. O estado atual permanece em [docs/RETOMADA.md](../RETOMADA.md), caminho estável para pessoas e chats novos. Este documento contém o procedimento; não é um segundo checkpoint.

## Retomar com segurança

1. Confirme a pasta; leia [AGENTS.md](../../AGENTS.md) e o checkpoint. Um chat novo pode não ter o histórico anterior.
2. Leia `git status --short --branch`, `git log -5 --oneline` e o diff relevante. Preserve alterações pendentes; não restaure nem descarte arquivos para obter um estado aparentemente limpo. Se necessária uma nova branch, leve as alterações do escopo sem perdê-las.
3. Confira PRs e a branch remota antes de publicar. Uma ação interrompida pode ter criado branch, commit ou PR mesmo sem resposta visível; verifique seu efeito antes de repetir.
4. Identifique última ação comprovada, pendência e verificação necessária. Marque **não verificado** quando faltar confirmação e investigue; não presuma sucesso ou falha.
5. Execute a próxima ação do escopo vigente. Uma pausa explícita impede continuação automática até o usuário retomar; ao retomar, preserve as prioridades e limites registrados.
6. Atualize o checkpoint após blocos coerentes e antes/depois de ações externas relevantes, sem deixar o registro somente para o fim. Use verificações adequadas à alteração, conforme [qualidade e evidências](qualidade-e-evidencias.md).

## Conteúdo do checkpoint

Registre branch/base, versão funcional verificada, PRs, última ação comprovada, pendência, próxima ação e links de evidência. Diferencie trabalho local, publicação confirmada, CI e revisão humana. Preserve incertezas e trabalho incompleto. Não copie conversa, logs extensos, segredos ou decisões já mantidas nos ADRs.

O checkpoint pode ficar uma ação atrás se a interrupção acontecer durante uma ferramenta. Reconciliação local/remota reduz perda de contexto; não garante captura de cada instante nem substitui Git e plataforma.

## O que persiste e o que precisa ser redescoberto

- Arquivos versionados e Git preservam trabalho publicado. Histórico/resumos do chat ajudam, mas não são o único registro.
- Handles de ferramentas, abas, sessões, PIDs e conexões autenticadas podem desaparecer. Redescubra-os; não reutilize identificadores antigos sem conferir.
- `.tools/` ajuda no mesmo computador, fica fora do Git e não é requisito para reconstruir o projeto.
- `.venv/`, `.uv-cache/`, `dist/` e `var/` ficam fora do Git. Banco e backups precisam ser preservados separadamente ao trocar de computador; clonar não os recupera.
- Não há serviço de monitoramento nem automação para gravar o checkpoint enquanto o modelo estiver interrompido.
