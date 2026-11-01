# ADR-011 — Classificar linhas e interpretar os valores na origem

01/11/2026. **Status: decisão técnica implementada no experimento autorizado.** Não altera confirmação, cálculo do aviso ou decisão de IA local; não libera integração ou produção.

## Problema observado

A rodada V2 perdeu bloqueios, converteu valores sem suporte e inventou regras de aviso. Seu schema permitia apenas número não negativo/unidade normalizada. Isso restringia a forma da resposta sem garantir que a condição inválida fosse preservada. É uma hipótese de desenho a testar, sem atribuir todos os erros a uma causa exclusiva ou ao runtime.

## Decisão

Novo método `OLLAMA_LINE_EXPERIMENT_V1`, prompt `LINE_CLASSIFICATION_V1` e interpretação `LITERAL_CLAUSES_V1`. Preservar o método/relatório anteriores para comparação. Manter o mesmo modelo/digest, runtime e conjunto de desenvolvimento; não iniciar seleção de modelo de produção.

A IA recebe todas as linhas não vazias, com aliases gerados pelo código e papéis dos documentos. Um schema dinâmico exige uma classificação para cada alias; o mesmo schema aparece no prompt para explicitar o formato. A saída não contém datas, números normalizados, citações reescritas ou eventos. Valores, intervalos e citações são buscados pelo código no texto de referência já preparado. Linhas vazias continuam na origem e nos intervalos, sem renumerar.

Interpretador puro em `domain/`, sem Streamlit, persistência ou SDK. Suporta datas numéricas dia/mês/ano, durações numéricas explícitas e âncoras documentadas no código. Não converte meses/dias úteis nem transforma número negativo/fracionário em válido. Ambiguidade, conflito, aditivo conhecido/afirmado explicitamente e trecho sem interpretação suportada geram pendência. Declaração de ausência não é equivalente a omissão de linha; a confirmação humana continua necessária.

O papel de aditivo declarado e as declarações textuais afirmativas suportadas geram bloqueio independentemente do label escolhido. Abstenção do modelo não remove esse impedimento: o relatório separa a abstenção bruta da situação bloqueada resultante. O experimento lê somente o conjunto fornecido, sem consultar histórico de banco; a futura integração terá de preservar também o aditivo histórico do ADR-006.

## Evidência e limitações

Cada observação separa labels da IA, guardas/interpretação do código e proposta final. As métricas são da **combinação**, sem atribuir à IA números/citações produzidos pelo código. Literal localizado não comprova suporte semântico. As guardas são conservadoras e podem reter um caso válido; não são interpretador jurídico geral ou certificação de completude semântica.

O runner reserva o destino, salva progresso por tentativa, recusa repetição sobre parcial anterior e identifica mudança de fonte durante a rodada. Uma interrupção mantém dados parciais, sem declarar conclusão. Isso não é recuperação de execução persistida da aplicação ou C20 completo.

Sem alteração em `AVISO_CORRIDOS_V1`, normalização documental, UI ou banco. Mudar a interpretação literal futura exige nova identificação explícita e reconferência pertinente. [Validação e comparação](../validacao-extracao-por-linhas.md) mantêm testes, resultados reais e limites antes de propor integração.
