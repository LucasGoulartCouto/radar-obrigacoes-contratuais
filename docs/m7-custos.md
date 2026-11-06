# M7 — custos e sensibilidade

05/11/2026 · Estudo sem contratação, consumo pago ou orçamento aprovado. Relacionado à [proposta M7](m7-proposta.md).

## Referência de catálogo

Referência ilustrativa: AWS Lightsail, região de estudo **US East / N. Virginia**, USD/mês, preços públicos consultados em 05/11/2026, sem créditos/free tier. Não é escolha de fornecedor/região; confirmar disponibilidade, residência dos dados e orçamento antes de contratar. Conversão para reais depende de câmbio/tributos da decisão.

A [página oficial](https://aws.amazon.com/lightsail/pricing/) informa: contêiner Medium 1 vCPU/2 GB a US$40/nó-mês; banco criptografado 2 GB/80 GB a US$30 padrão ou US$60 HA; objetos 100 GB a US$3; snapshot a US$0,05/GB-mês. O banco de US$15 não inclui criptografia em repouso nessa tabela e foi excluído.

| Composição de estudo | Cálculo mensal | Subtotal de catálogo |
|---|---|---|
| Piloto | 1 nó web + 1 worker: 80; banco: 30; objetos: 3; snapshots 20 GB-mês: 1 | **US$114** |
| Comparação com redundância | 2 nós web + 1 worker: 120; banco HA: 60; objetos: 3; snapshots: 1 | **US$184** |

São comparações, não topologias implantadas/certificadas para HA. O [serviço de contêineres](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-container-services.html) já distribui tráfego entre nós; não foi somado outro balanceador. Dois nós web exigem validar afinidade/WebSockets/perda de sessão. A [documentação de cobrança](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-frequently-asked-questions-faq-billing-and-account-management.html) informa que parar instância/banco não encerra cobrança; exclusão exige preservar dados.

## Exclusões e fórmula do total

Subtotais **excluem IA**, identidade, observabilidade, suporte, domínio, rede excedente, tributos, cópias fora da conta/região e trabalho humano. Não são custo mensal completo. Os 20 GB-mês de snapshot são hipótese contábil: não demonstram que a retenção de 7 diárias/4 semanais cabe nela.

Worker de 2 GB representa coordenação/validação, não hospedagem do modelo local. IA em CPU/GPU precisa de outro dimensionamento; API exige avaliação/contrato/autorização. Modelo provisório não virou escolha de produção.

```text
C_total = web + worker + banco + objetos + backup + rede + identidade
          + observabilidade + IA + suporte + tributos + horas_operacao × valor_hora
C_IA_API = N × (tokens_entrada × preco_entrada + tokens_saida × preco_saida) / 1.000.000
           + chamadas_repetidas + demais_cobrancas_do_provedor
C_IA_dedicada = horas_alocadas × tarifa_compute + disco + rede + operacao
```

Tarifas na fórmula são por milhão de tokens. Medir entradas/saídas/contexto no método escolhido, inclusive classificação por linhas. Não presumir retry grátis ou inferência única.

## Sensibilidade com hipóteses próprias

C: 100 análises/dia útil × 22 dias = **2.200/mês**. Valores por análise abaixo são hipóteses matemáticas, **não tarifas de fornecedor**, nem comprovação de que um modelo atende à qualidade/prazo.

| Custo hipotético/análise | IA mensal | Piloto + IA, ainda com exclusões |
|---|---|---|
| US$0,01 | US$22 | US$136 |
| US$0,10 | US$220 | US$334 |
| US$1,00 | US$2.200 | US$2.314 |

Repetir 10% das chamadas acrescentaria US$2,20 / US$22 / US$220, respectivamente. Em máquinas dedicadas capacidade ociosa também custa; dobrar slots não garante dobrar desempenho. E teria dez vezes mais chamadas que C, sem presumir preço/performance lineares.

L não contrata hospedagem nova, mas energia, máquina, backups e manutenção têm custo. Medir consumo/horas e aplicar tarifa/valor-hora locais; não chamar custo operacional de zero.

Lucas define teto total e de IA antes do piloto, responsáveis, alertas 50/80% e bloqueio de novas extrações no teto. Se exceder, reduzir escopo/carga ou manter L. Revalidar catálogo/disponibilidade na data da decisão.
