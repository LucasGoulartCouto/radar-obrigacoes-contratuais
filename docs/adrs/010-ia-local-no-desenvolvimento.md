# ADR-010 — IA local agora; produção depois da aplicação

Data: 01/11/2026. **Decisão de produto aceita por Lucas:** usar IA local durante o desenvolvimento. Planejamento de IA em produção e seleção do melhor modelo ficam para depois da aplicação concluída.

## Contexto e decisão

O experimento do ADR-009 criou a fronteira de avaliação e uma referência por regras. Lucas escolheu IA local para prosseguir. Essa decisão permite preparar um runtime e um modelo provisório compatível com o computador, sem iniciar seleção de produção nem assumir despesas de API.

Escolha técnica provisória: Ollama portátil 0.40.13 e Qwen3 4B Instruct Q4, identificados por versão/SHA/digest. Não é afirmação de superioridade ou adequação para produção. O runtime/pesos ficam fora do Git, em `.tools/ollama/`, sem alterar PATH global ou instalar serviço de inicialização do Windows.

Inferência restrita a loopback literal, sem proxies/redirecionamentos ou ferramentas de ação. Nuvem do runtime desabilitada. Download inicial requer internet; inferência usa o modelo GGUF já presente e com digest conferido. O cliente não puxa modelo ausente nem aceita modelo remoto como fallback.

Saída estruturada passa por validação local de schema, tipos, datas e citações literais. Resposta incompleta, contexto não verificado, origem inexistente, solicitação de ferramenta e erro técnico não viram análise vazia. O cálculo continua no código; confirmação continua humana e vinculada à base atual.

## Alcance desta entrega

Adaptador e avaliação continuam isolados em `infrastructure/experiments/`. Não há seleção do método pela UI, gravação de resultado de IA, migração ou mudança da agenda. Não considerar essa etapa como aplicação concluída ou C20 completo. A integração ao fluxo persistido é o próximo bloco, com execução/recuperação, revisão e concorrência ainda necessárias.

O prompt pode ser ajustado no desenvolvimento, com versão e falhas registradas. Exemplos usados para ajuste não são avaliação independente. A escolha definitiva de modelo/infraestrutura de produção será tratada na etapa posterior indicada por Lucas; os controles de integridade, limites e conferência seguem necessários desde o protótipo.

## Evidências e consequências

[IA local no Radar](../ia-local.md) mantém comandos, limites e fontes primárias. A [validação](../validacao-ia-local.md) separa testes simulados, operação real no computador e qualidade observada. `AVISO_CORRIDOS_V1`, dados sintéticos, ausência de ações de negócio externas e histórico da aplicação permanecem.
