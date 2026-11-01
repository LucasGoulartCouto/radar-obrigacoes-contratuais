# ADR-002 — Separar extração, cálculo e confirmação

Data: 31/10/2026.

**Status: proposto.** Material para decisão de Lucas; nenhum componente foi implementado.

## Contexto

Uma sugestão plausível pode conter uma data sem suporte, uma referência incorreta ou informação de uma revisão antiga. Precisamos distinguir o conteúdo do documento, a data derivada e a decisão humana. A solução também precisa continuar coerente se o extrator mudar.

## Alternativas

1. Um modelo lê o contrato e publica diretamente os prazos: reduz etapas visíveis, mas mistura interpretação, aritmética, precedência documental e autorização de publicação.
2. Cadastro inteiramente manual com validações: facilita conferir regras e controlar custo; preserva maior esforço de transcrição e deve servir como comparação inicial.
3. Extrator substituível propõe campos com evidências; código calcula datas por regras do case; usuário confirma: separa responsabilidades, mas acrescenta estados, conferência e gestão de revisões.

## Proposta

Adotar a separação da alternativa 3, avaliando a alternativa 2 como baseline. O método de extração poderá ser simples ou usar IA, conforme experimento. Nenhum extrator terá autoridade para confirmar eventos ou acionar sistemas externos.

Conferência vinculada à revisão documental, ao resultado selecionado e à versão das regras. Alteração relevante exige reconferência. Na primeira versão, aditivos ficam como pendência explícita, sem consolidação automática.

## Consequências previstas

- Cálculo e regras de publicação podem ser verificados independentemente do modelo.
- Evidência localizada não garante que o trecho sustenta o campo: revisão e avaliação semântica continuam necessárias.
- O histórico deve preservar valores antes e depois de correções, sem atribuir acertos humanos ao extrator.
- A experiência precisa tornar a revisão útil e evitar que a confirmação vire uma ação mecânica.
- Não prometemos eliminar erros ou ataques; reduzimos a autoridade de uma saída incorreta e avaliamos falhas conhecidas.

## Critério para aceitar ou rever

Comparar alternativas com os cenários da SPEC, esforço de revisão, custo e facilidade de manutenção. A escolha de ferramentas no ADR-004 não altera o status proposto desta decisão sobre extração e confirmação; Lucas a revisará com os requisitos detalhados. Se o extrator não trouxer benefício verificável, o fluxo com cadastro manual e regras continua sendo uma alternativa legítima.

Referências: [SPEC](../specs/001-primeiro-fluxo.md), [arquitetura](../arquitetura.md), [OWASP Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) e [OWASP Misinformation](https://genai.owasp.org/llmrisk/llm092025-misinformation/).
