## Problema e comportamento

Descreva a tarefa, o resultado e as exclusões relevantes.

## Decisões e referências

Relacione requisitos, cenários da SPEC e ADRs afetados.

## Verificação

Informe comandos executados, resultados e limites. Diferencie verificação local de CI remota.

Relacione cada funcionalidade criada ou alterada. Use links para testes no commit revisado e para sua execução; para verificações manuais, registre procedimento, resultado e alcance. Contagem total de testes não substitui esta relação.

| Funcionalidade criada/alterada | Cenário e resultado esperado | Teste/evidência | Resultado e commit |
|---|---|---|---|
| Preencher conforme o diff final | Incluir sucesso, falha e regressão pertinentes | Link do teste ou registro manual | Execução e SHA |

Em mudança somente documental, registrar revisão e links verificados. Identificar lacunas sem afirmar cobertura ou execução que não ocorreu. Ao atualizar código, base ou HEAD, reconferir a validade das evidências e da CI.

## Revisão

- [ ] Regra de negócio e situações de falha conferidas.
- [ ] Cada funcionalidade criada/alterada está ligada à evidência pertinente; lacunas resolvidas antes da integração.
- [ ] Evidências e CI correspondem ao diff e à versão final; revisão de Lucas continua separada.
- [ ] Nenhum dado real, segredo ou banco gerado incluído.
- [ ] Documentação atualizada para o comportamento final.
