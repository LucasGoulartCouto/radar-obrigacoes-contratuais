# ADR-002 — Separar extração, cálculo e confirmação

Data: 31/10/2026.

**Status: aceito por Lucas em 01/11/2026.** Aritmética, entrada, revisões documentais, levantamento manual e fluxo de conferência estão implementados. Extração automática e agenda temporal completa ainda são futuras. A demonstração de conferência é simulada; não representa revisão humana real de Lucas.

## Contexto

Uma sugestão plausível pode conter uma data sem suporte, uma referência incorreta ou informação de uma revisão antiga. Precisamos distinguir o conteúdo do documento, a data derivada e a decisão humana. A solução também precisa continuar coerente se o extrator mudar.

## Alternativas

1. Um modelo lê o contrato e publica diretamente os prazos: reduz etapas visíveis, mas mistura interpretação, aritmética, precedência documental e autorização de publicação.
2. Cadastro inteiramente manual com validações: facilita conferir regras e controlar custo; preserva maior esforço de transcrição e deve servir como comparação inicial.
3. Extrator substituível propõe campos com evidências; código calcula datas por regras do case; usuário confirma: separa responsabilidades, mas acrescenta estados, conferência e gestão de revisões.

## Decisão

Adotar a separação da alternativa 3, avaliando a alternativa 2 como baseline. Lucas escolheu “Adotar essa regra” ao revisar a separação entre sugestão, cálculo e conferência, com bloqueio por unidade ambígua, conflito de datas ou aditivo. O método de extração poderá ser simples ou usar IA, conforme experimento. Nenhum extrator terá autoridade para confirmar eventos ou acionar sistemas externos.

Conferência vinculada à revisão documental, ao resultado selecionado e à versão das regras. Alteração relevante exige reconferência. Na primeira versão, aditivos ficam como pendência explícita, sem consolidação automática.

## Consequências previstas

- Cálculo e regras de publicação podem ser verificados independentemente do modelo.
- Evidência localizada não garante que o trecho sustenta o campo: revisão e avaliação semântica continuam necessárias.
- O histórico deve preservar valores antes e depois de correções, sem atribuir acertos humanos ao extrator.
- A experiência precisa tornar a revisão útil e evitar que a confirmação vire uma ação mecânica.
- Não prometemos eliminar erros ou ataques; reduzimos a autoridade de uma saída incorreta e avaliamos falhas conhecidas.

## Critério para avaliar o extrator e rever a decisão

Comparar métodos de extração com os cenários da SPEC, esforço de revisão, custo e facilidade de manutenção. A decisão aceita define responsabilidades e bloqueios, mas não escolhe fornecedor de IA nem aprova todos os detalhes operacionais. Se o extrator não trouxer benefício verificável, o fluxo com cadastro manual e regras continua sendo uma alternativa legítima. Os [exemplos e limites iniciais](../decisoes-primeiro-fluxo.md) distinguem a decisão aceita dos detalhes ainda propostos.

Referências: [SPEC](../specs/001-primeiro-fluxo.md), [arquitetura](../arquitetura.md), [OWASP Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) e [OWASP Misinformation](https://genai.owasp.org/llmrisk/llm092025-misinformation/).
