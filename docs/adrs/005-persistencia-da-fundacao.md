# ADR-005 — Cadastro, recibo de operação e histórico na mesma transação

**Status: implementado na fundação em 01/11/2026.** Decisão técnica do agente dentro do trabalho de fundação autorizado por Lucas. Não altera o recorte funcional do produto nem representa aceite da proposta de extração do ADR-002.

## Contexto

A interface pode reenviar uma ação, e duas telas podem exibir o mesmo cadastro antes de uma edição. Precisamos evitar duplicação por reenvio, sobrescrita silenciosa e cadastro sem histórico quando uma escrita falhar.

## Alternativas

1. Guardar controle apenas no estado da tela: não cobre nova sessão, reenvio ou outro processo.
2. Gravar cadastro e histórico em operações independentes: uma falha intermediária pode deixar um resultado parcial.
3. Usar recibo persistido da operação, comparação da versão de cadastro e transação única: exige registros adicionais, mas permite verificar repetição e atomicidade no armazenamento.

## Decisão implementada

Adotar a alternativa 3. A persistência mantém cadastro, recibo com identificação/fingerprint/resposta e evento de histórico. Uma repetição com o mesmo conteúdo retorna a resposta anterior; reutilizar a identificação com outros dados é rejeitado. A edição compara a versão esperada na escrita. O conjunto só é publicado se a transação terminar.

O histórico liga a ação e o operador fictício ao recibo que preserva a resposta daquela operação. A versão de cadastro controla o nome; revisão documental será um conceito separado.

As migrações foram empacotadas junto ao adaptador de persistência para que o comando de preparação também funcione a partir do wheel instalado. O arquivo de dados gerado continua fora do Git.

## Consequências e limites

- Reenvio não é deduplicação semântica: contratos com mesmo nome e identificações de operação diferentes continuam cadastros distintos.
- Respostas antigas preservam o resultado original sem desfazer edições posteriores.
- Um banco ocupado pode rejeitar uma tentativa com mensagem para tentar novamente; não há promessa de espera ilimitada ou de escalabilidade distribuída.
- O histórico é lógico e local; não é auditoria inviolável nem autenticação do operador.
- Os controles de revisão documental e confirmação de obrigações exigirão implementação e testes próprios.

## Evidência

Os testes cobrem reenvio, colisão de identificação, conflito de versão, edições concorrentes e falha de histórico com rollback. A [validação da fundação](../validacao-fundacao.md) registra também persistência, backup, interface e instalação do pacote.
