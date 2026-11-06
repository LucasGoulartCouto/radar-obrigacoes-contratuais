# Consolidação do Radar na main

05/11/2026. Lucas informou o [aceite funcional e a revisão dos PRs #1–#13](aceite-funcional.md), autorizando a integração. O agente não deve solicitar novamente essa autorização. Publicação social, galeria, despesas e implantação continuam separadas.

## Como conferir o resultado

O [PR #13](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/13) é a etapa final da consolidação. Sua descrição registra o commit integrado e a CI do último HEAD. Confirmar `merged` na plataforma antes de considerar concluída a incorporação da entrega e antes de repetir qualquer ação interrompida.

O [snapshot de integração](../evidencias/integracao-2026-11-05.json) foi preparado depois dos merges #1–#12 e antes da etapa final: contém os commits efetivamente incorporados, as árvores originais, a CI consultada e o endereço do resultado final. Não antecipa o merge do #13. A fonte do código consolidado é a `main`, após essa última incorporação.

O histórico anterior foi preservado em [codex/arquivo-pre-integracao-20261105](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/tree/codex/arquivo-pre-integracao-20261105). As etapas foram reaplicadas sobre a `main` e incorporadas por rebase, mantendo histórico linear. Os commits receberam novos identificadores; as árvores foram comparadas aos snapshots revisados. Assim, referências antigas a código, experimentos e regressões continuam acessíveis pelo histórico arquivado.

## Ajuste necessário durante a integração

A CI do PR #12 revelou uma disputa real no SQLite ao concluir uma tentativa concorrente. A integração foi interrompida; o caso foi reproduzido de forma determinística e corrigido reservando escrita antes de ler o recibo. O [registro da correção](../validacao-concorrencia-gravacao.md) preserva a execução que falhou, o teste e os limites. A correção foi carregada pelo #13 para não ser perdida na reaplicação.

Essa é a exceção documentada à igualdade dos arquivos da aplicação com os snapshots originais: reserva antecipada de escrita, teste novo e registro da regressão. O fechamento atualiza somente guias, estado e aceite. A linha funcional completa passou em **383 testes locais**, sem nova inferência real ou migração adicional; cada HEAD destinado à integração passa pela CI em Windows/Linux.

## Próxima etapa do escopo

Depois de confirmar a incorporação do #13 e a CI da `main`, a proposta futura é [M7 — evolução da arquitetura](../evolucao-arquitetural.md): definir cenário de crescimento, metas, custos e medir a base local antes de escolher mudanças. Esses valores ainda dependem de Lucas; não inventar demanda ou iniciar implantação, serviços pagos ou seleção definitiva de modelo.

Os [materiais](README.md) permanecem disponíveis. Cartão e textos de divulgação continuam rascunhos, sem URLs reais fornecidas e sem envio pelo agente. A avaliação automática continua 18/20 no desenvolvimento conhecido, antes de correções; aceite funcional, integração e testes não substituem avaliação reservada nem certificam produção.
