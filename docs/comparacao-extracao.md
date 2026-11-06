# Comparação inicial de alternativas de extração

01/11/2026. **Conclusão: preservar o fluxo manual e não integrar o baseline por regras.** Ele serve como referência experimental; ignorou cinco impedimentos e propôs sete eventos indevidos no desenvolvimento. Nenhuma IA foi executada, portanto ainda não existe evidência de que melhore esses resultados.

## Alternativas e evidência disponível

| Alternativa | O que sabemos | Custo/esforço | Situação |
|---|---|---|---|
| Levantamento manual com validação | Fluxo de evidências, cálculo, confirmação e agenda já implementado; não extrai sozinho | Tempo humano não medido de forma comparável | Referência operacional atual, sem taxa de extração automática atribuída |
| Regras locais de linhas completas | Execução medida abaixo; gramática limitada, sensível a contexto e paráfrases | Zero chamadas e zero despesa de API nesta rodada; desenvolvimento, máquina e revisão têm custo não medido | Experimento offline, sem adoção no produto |
| Modelo local, por exemplo via Ollama | Documentação oferece respostas com JSON Schema; qualidade em português, memória, licença do modelo e latência dependem da escolha/ambiente | Sem orçamento de hardware/esforço validado; custo total não estimado | Documentado, não preparado/executado nesta etapa |
| API hospedada, por exemplo OpenAI | Documentação oferece saídas estruturadas com subconjunto de JSON Schema; formato válido não garante correção factual | Depende de fornecedor/modelo, volume, tokens, preços e tentativas; nenhuma despesa autorizada ou estimada como fato | Referência técnica, sem escolha de fornecedor, credencial ou chamada |

A comparação acima é entre abordagens. Ollama/OpenAI são exemplos documentados, não uma seleção de fornecedores/modelos ou uma prova de superioridade. Não há benchmark de IA nem comparação de esforço humano.

## Execução local por regras

Método `REGEX_EXPERIMENT_V1`, **20 casos/21 documentos de desenvolvimento**, com gabaritos visíveis. [Resultado JSON](evidencias/extracao-regras-v1.json) contém os hashes do código/entradas e os resultados por caso. A [validação](validacao-experimento-extracao.md) registra verificações e limitações.

| Medição | Resultado | Interpretação |
|---|---|---|
| Fatos com valor e evidência anotada corretos | 26 acertos, 1 falso positivo, 3 omissões; precisão 26/27 = 96,3%; recuperação 26/29 = 89,7% | Localizar campos não prova elegibilidade dos eventos |
| Eventos candidatos | 11 acertos, 7 falsos positivos, 2 omissões; precisão 11/18 = 61,1%; recuperação 11/13 = 84,6% | Sete candidatos indevidos no recorte; nenhum foi confirmado ou publicado |
| Bloqueios | 11 casos exigiam bloqueio; em 5 deles faltou reconhecer o impedimento | DEV-012/013/014/017/018: âncora, unidade, divergência numérica e aditivo no conteúdo |
| Casos integralmente correspondentes | 11/20, incluindo campos, evidências, bloqueios e candidatos | Não é acurácia representativa de contratos reais |
| Abstenções | 2/20: DEV-005 e DEV-019 | Ausência de match não vira “conferido sem eventos”; um deles omite término esperado |
| Falhas técnicas/evidências literais inválidas | 0/20 e 0 nesta execução | Citação literal válida ainda pode não sustentar o campo |
| Tempo local | Mediana 0,098 ms; máximo 4,636 ms por caso | Uma execução de extração + pontuação, sem leitura, interface ou revisão; sem conclusão sobre carga/ganho de tempo |

DEV-020 é a regressão semântica central: uma linha com formato reconhecido faz parte de um exemplo, enquanto outra linha define a vigência efetiva. A regra escolheu o exemplo. A citação existe, mas não sustenta o campo; o avaliador conta falso positivo e omissão. DEV-004 mantém o bloqueio por papel declarado, mas o método não extrai a data anotada do aditivo. Essas limitações permanecem no relatório.

## Como reproduzir

Na raiz do repositório, com o ambiente preparado:

```powershell
uv run --locked python -m radar_contratos.infrastructure.experiments.extraction --output .tools/extracao-nova-execucao.json
uv run --locked pytest tests/unit/test_extraction_experiment.py tests/unit/test_synthetic_cases.py
```

O destino deve ser novo e o diretório deve existir. O JSON versionado mantém os números da execução registrada; tempos de outras execuções podem variar. A versão do método e os hashes permitem conferir qual código/conjunto foi executado. O comando é offline, sem banco ou API. Não é uma ação da interface e não implementa estados de execução persistidos ou C20 completo.

## Protocolo da próxima comparação

1. Escolher com Lucas ambiente/fornecedor e teto financeiro antes de qualquer API paga ou aquisição. Não interpretar assinatura de chat como autorização, credencial ou crédito de API.
2. Congelar versão do método/prompt, modelo, schema, normalização, limites de entrada, prazo máximo, tentativas e orçamento total. Saída do modelo propõe apenas campos/evidências/bloqueios; código calcula e pessoa confirma. Não fornecer ferramentas de ação ao extrator.
3. Usar os 20 casos de desenvolvimento para ajuste e documentar mudanças. Para outra alternativa, manter o mesmo conjunto e registrar tokens, falhas, recusas, truncamento e tempo. O avaliador atual precisa de adaptador validado antes de receber respostas de um modelo.
4. Antes de abrir avaliação final, definir limiares de adoção, casos críticos e política de adjudicação. **Proposta para decisão:** nenhum evento indevido nem bloqueio crítico perdido na avaliação, campos sempre com suporte e abstenção explícita; critérios de recuperação/esforço/custo ainda dependem de Lucas. Não são critérios já aceitos ou atingidos.
5. Preparar aproximadamente 10 novos casos reservados depois do congelamento, com anotação/revisão independente das regras/prompt. Preservar proveniência e acesso. Caso seja lido para ajustar método, reclassificar como desenvolvimento e substituí-lo. Um diretório chamado “reserved” não garante independência.
6. Relatar numeradores/denominadores por campo, evento e classe crítica, falhas, abstenções, evidências, custo total e correções humanas. Não somar correção humana aos acertos automáticos. Comparar tempo manual/assistido apenas com tarefa e procedimento comparáveis.
7. Só propor integração com resultados e decisão de adoção. Especificar execução fora da transação, base imutável, timeout/recuperação, tentativa interrompida, idempotência e rejeição de revisão desatualizada antes de conectar ao caminho de confirmação.

## Fontes primárias consultadas

- [Python 3.14 — re](https://docs.python.org/3.14/library/re.html): gramáticas de expressão regular e correspondência de strings. A documentação não garante suporte semântico.
- [Ollama — Structured Outputs](https://docs.ollama.com/capabilities/structured-outputs): schema em `format` e validação da resposta. Isso documenta mecanismo, sem evidência de desempenho neste ambiente.
- [OpenAI — Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs): aderência estrutural, restrições e situações de saída que exigem tratamento. Não garante que valores/citações sejam corretos.

Consulta em 01/11/2026. Nenhum preço, modelo ou condição comercial foi fixado; precisam ser consultados na seleção. Decisão técnica e consequências no [ADR-009](adrs/009-experimento-offline-de-extracao.md).
