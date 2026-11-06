# ADR-014 — evolução condicional para uso compartilhado

05/11/2026 · **Status: proposto para revisão de Lucas.** Não substitui ADRs 003/004 aceitos, nem autoriza implantação, gasto ou modelo definitivo.

## Contexto

Fluxo local aceito e PRs #1–#13 integrados. Lucas solicitou M7 com cenários hipotéticos. O [estudo](../m7-proposta.md) e o [baseline](../validacao-m7.md) separam desempenho observado de requisitos novos de identidade, acesso remoto e continuidade. Não foi demonstrada necessidade de migrar uso individual por saturação do SQLite.

## Decisão proposta

Manter aplicação modular local para L. Se Lucas escolher C, construir protótipo isolado PostgreSQL + identidade/autorização no servidor + worker com jobs transacionais. Reutilizar casos de uso/regras puras, preservar origem/versões e confirmação humana idempotente sobre base atual. IA não recebe autoridade de confirmar.

Objetos privados/versionados quando tamanho/retenção/recuperação justificarem; broker somente com necessidade comprovada, outbox e consumidor idempotente. Lease vencido requer recuperação explícita no primeiro piloto, sem retry automático de inferência.

## Alternativas

- SQLite otimizado: menor operação para L; perfilar/paginar e comparar WAL antes de migrar por desempenho. Não compartilhar arquivo pela rede.
- PostgreSQL sem worker: centraliza dados, mas não resolve trabalho durável após fechar a tela.
- Banco + broker desde o início: isolamento de despacho ao custo de operação/consistência/duplicação antes de necessidade comprovada. Adiar.
- Microsserviços/Kubernetes: sem equipes/carga que justifiquem. Adiar.
- Plataforma totalmente gerenciada: depende de avaliação de preço, identidade, portabilidade e controles. Sem fornecedor aprovado.

## Consequências e critérios

PostgreSQL exige adaptar SQL/transações/constraints e migrar/restaurar dados; não é apenas trocar URL. Worker introduz lease/token/estados incompletos. Objetos exigem restauração conjunta e tratamento de órfãos. Login não substitui autorização. [Custos](../m7-custos.md) são subtotais, não orçamento completo.

Aceitar implementação após equivalência de dados/eventos/cobertura, conflito/base antiga, isolamento de acesso, restore e metas de carga do cenário aprovado. Rejeitar ganho de latência que perca invariantes. Sem cenário/teto/responsáveis escolhidos, manter L. Não promover E por resultados de C, nem capacidade remota por benchmark local.

## Evidência e pendências

M7 entrega medidor reproduzível, baseline, alternativas, fluxo, custos, migração/reversão e gates. PostgreSQL, autenticação/autorização, worker distribuído, broker, objetos externos, restore remoto e avaliação reservada da IA não foram implementados. Lucas decide cenário/metas/teto, identidade, retenção e próximo protótipo. Status continua proposto até revisão.
