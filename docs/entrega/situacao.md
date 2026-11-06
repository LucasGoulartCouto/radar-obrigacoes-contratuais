# Situação da entrega para revisão de Lucas

Atualizado em 05/11/2026. Este quadro organiza a entrega; não declara submissão ao desafio, avaliação independente ou aprovação de produção.

**Aceite em 05/11/2026:** Lucas informou validação funcional e revisão dos PRs #1–#13, autorizando a integração. [Registro](aceite-funcional.md). A descrição do PR #13 identifica o resultado e a CI finais; confirmar sua incorporação antes de repetir integrações ou iniciar a etapa futura. A linha local mais recente passou em 383 testes, incluindo a [correção da disputa de gravação](../validacao-concorrencia-gravacao.md) encontrada no Windows durante a integração.

**Conferência em 04/11/2026:** Git limpo no HEAD `0ecf882` do PR #12 e PRs #1–#12 abertos/sem merge, todos com CI bem-sucedida nos HEADs consultados. [Registro remoto](../evidencias/retomada-2026-11-04.json) e [roteiro de revisão](revisao.md). A SPEC foi atualizada para retirar descrições antigas de execução/cobertura; nenhuma regra foi alterada. O roteiro prepara a revisão de Lucas e não a substitui. A CI de eventuais atualizações posteriores deve ser conferida na descrição do PR #12.

| Item | Evidência disponível | Situação |
|---|---|---|
| Case e discovery | [Case Prisma](../discovery/radar-obrigacoes-contratuais.md), personagens e conversa fictícia explícitos | Decisão aceita; demanda real não validada |
| Produto, comportamento e decisões | [PRD](../PRD.md), [SPEC](../specs/001-primeiro-fluxo.md), ADRs e arquitetura | Recorte e limites aceitos identificados; não converter todas as propostas em aceite |
| Código e histórico | PRs #1–#13 e histórico original arquivado | Revisados por Lucas; integração autorizada na ordem; resultado final na descrição do #13 |
| Verificação funcional | Matrizes por comportamento, 383 testes na linha mais recente e aceite funcional informado | Não é percentual de cobertura ou avaliação independente do modelo |
| Extração | 20 casos de desenvolvimento conhecidos, referência 18/20 e regressão preservada | Sem conjunto reservado ou generalização comprovada |
| Reprodução | Cópia, ambiente, cache e banco novos nesta máquina; [registro](../validacao-reproducao.md) | Preparo/início/validação exercitados; runtime de IA reutilizado |
| Demonstração | [Roteiro](roteiro-demonstracao.md), capturas e registros de simulação | Roteiro pronto para revisão; vídeo não gravado |
| Cartão | [Pasta portátil](galeria/lucasgoulartcouto/README.md), metadados e imagem | Rascunho com links de posts vazios; não pronto para submeter |
| Visibilidade | [Textos para os dois canais](publicacoes.md) | Não enviados; dependem de instrução de Lucas |
| Galeria | Destino oficial conferido em `desafio-livre/projetos/lucasgoulartcouto/` | Nenhum fork, PR ou submissão executados |
| Operação e escala | [M7](../m7-proposta.md), [baseline sintético](../validacao-m7.md), custos e ADR proposto | Estudo para revisão; medição local curta, sem carga remota/IA ou implantação |

## Sequência para finalizar a participação

1. Aceite funcional e revisão dos PRs #1–#13 informados por Lucas em 05/11; integração autorizada. Conferir a conclusão no PR #13 e na `main`, sem pedir novamente essa autorização. Afirmações finais do cartão/textos, links e envio continuam separados.
2. Decidir quais lacunas do MVP precisam de outro bloco de trabalho. Avaliação reservada requer protocolo/critérios e respostas de referência independentes do ajuste; não chamar os exemplos conhecidos de avaliação independente.
3. Se Lucas quiser gravar, executar o roteiro em banco de demonstração e conferir se as evidências permanecem válidas. Vídeo é opcional nas regras consultadas.
4. Após instrução explícita, publicar os textos nos canais escolhidos e registrar os links reais dos posts. Não substituir por perfis nem inventar URLs.
5. Completar o cartão e reconferir as regras/destino oficiais antes de qualquer submissão. Só então preparar a ação de galeria autorizada por Lucas.

As [regras oficiais](https://github.com/suajornadadedados/desafio-jornada/blob/main/COMO-SUBMETER.md) e o [enunciado](https://github.com/suajornadadedados/desafio-jornada/blob/main/desafio-livre/README.md) foram reabertos em 02/11/2026. Eles aceitam projetos em diferentes estágios, exigem os links de divulgação no cartão e não tornam os checks automáticos equivalentes à revisão humana. Não foi assumida uma data exata de encerramento.
