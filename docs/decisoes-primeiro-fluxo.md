# Decisões para o primeiro fluxo

01/11/2026 · **Decisão de produto aceita por Lucas nesta conversa.** Os limites de entrada abaixo foram adotados na implementação autorizada de recebimento e versionamento; análise, conferência e agenda continuam sem implementação.

## O que já está decidido

Case fictício da Agência Prisma, documentos sintéticos, foco em término e aviso de não renovação, aplicação local modular e ferramentas da fundação. O PR da fundação continua separado desta entrega e aberto para revisão.

## Decisão de produto

Lucas escolheu “Adotar essa regra” para a proposta: a extração sugere com trechos de origem, o código calcula e a pessoa confere antes de entrar na agenda; unidade ambígua, datas conflitantes ou aditivo bloqueiam a confirmação do contrato. Essa decisão aceita a alternativa 3 do [ADR-002](adrs/002-proposta-limites-extracao-e-confirmacao.md). Começar pela entrada manual dos candidatos permite verificar esse fluxo antes de avaliar a automação.

| Comportamento da decisão | Exemplo concreto | Consequência |
|---|---|---|
| Agenda depende de conferência explícita | Término em 30/06/2027 e aviso de 30 dias corridos produzem 31/05/2027 como sugestão | A agenda permanece vazia antes de confirmar |
| Ambiguidade bloqueia o contrato | O documento informa apenas “30 dias”, sem unidade definida no case | Mostrar a pendência; não presumir dias corridos nem publicar parcialmente o término |
| Conflito preserva as duas evidências | Duas cláusulas informam términos diferentes para o mesmo ciclo | Não escolher a última cláusula nem uma data conveniente |
| Aditivo exige tratamento fora do recorte inicial | Base acompanhada de aditivo com outro término | Manter o contrato bloqueado; não ignorar nem consolidar o aditivo |
| Resultado vazio também exige conferência | Texto completo sem término ou aviso do recorte | Só depois da revisão fica “Conferido sem eventos no recorte” |
| Alteração invalida confirmação anterior | Documento, regra ou resultado selecionado muda | Retirar eventos antigos da agenda atual, preservar histórico e mostrar reconferência |
| Documento não autoriza ações | Texto pede confirmação automática e envio de mensagem | Tratar a frase como dado; nenhuma ação ou confirmação é autorizada pelo documento |

Essas regras são convenções da simulação. Não estabelecem interpretação jurídica para documentos reais. O bloqueio impede confirmação da base atual; uma futura revisão com suporte suficiente precisará passar por nova análise e conferência. A consolidação de aditivos permanece fora desta versão.

## Limites operacionais da entrada

São tetos conservadores implementados para limitar o trabalho do protótipo, **sem medição de capacidade sob carga**. Podem ser configurados por variáveis de ambiente; alterações devem preservar a validação e ser justificadas. Decisão técnica e consequências: [ADR-006](adrs/006-entrada-e-revisoes-documentais.md).

| Entrada | Configuração ou decisão | Comportamento esperado |
|---|---|---|
| Formato | Arquivos `.txt` UTF-8; aceitar BOM inicial | Rejeitar codificação inválida e formatos não suportados com mensagem útil |
| Documento individual | 262.144 bytes, medidos antes de normalizar o texto | Rejeitar excesso antes de análise; sem truncamento |
| Conjunto documental de uma revisão | Até 5 documentos e 1.048.576 bytes no total; ambos os limites se aplicam | Rejeitar conjunto que exceda qualquer teto; preservar a revisão anterior |
| Localização de evidência | Linhas a partir de 1 no texto de referência, após normalizar CRLF/CR para LF e remover BOM inicial | Preservar bytes originais e verificar citação literal |
| Agenda da simulação | Referência explícita e horizonte de 30 dias conforme SPEC | Separar ultrapassada, hoje, próximos 30 dias e depois do horizonte |
| Processamento automático | Prazo, tentativas e orçamento definidos antes de integrar cada extrator | A primeira entrega de casos não faz chamada de IA nem assume custo de API |

Extensão `.txt` não comprova conteúdo válido. A entrada verifica os bytes e o texto e rejeita conteúdo vazio, só espaços, UTF-8 inválido e controles incompatíveis. Esses casos não representam análise válida sem eventos.

O prazo máximo de processamento e a política de recuperação ainda precisam de especificação antes da etapa de análise. Um timeout de teste da interface não representa esse limite operacional.

## Material disponível para conferir o comportamento

O [conjunto de desenvolvimento](../tests/fixtures/contracts/README.md) contém oito casos, nove documentos e respostas esperadas com citações literais. O [caso simples](../tests/fixtures/contracts/development/documents/DEV-001-base.txt) é o primeiro exemplo a revisar; o [caso ambíguo](../tests/fixtures/contracts/development/documents/DEV-002-base.txt) mostra o custo da escolha por bloquear.

O gabarito foi escrito como referência de desenvolvimento. Ele não é resultado de extração nem avaliação reservada. Seus testes verificam consistência dos dados, localização das evidências e aritmética existente. A gestão de revisões agora tem [verificações próprias](validacao-entrada-documental.md); isso não comprova confirmação, agenda ou resistência de um extrator a instruções indevidas.

## Próxima implementação depois da decisão

O recebimento e versionamento foram implementados com limites explícitos, preservação da origem e reenvio sem duplicação de revisão. O próximo passo é registrar candidatos com evidências e implementar conferência, confirmação atômica e invalidação de resultados desatualizados. Cada entrega deverá ligar o requisito da SPEC à sua verificação.

## Verificação da entrega de regras e casos

Executada localmente no Windows em 01/11/2026: **43 testes passaram**, sendo os 34 da fundação e 9 de integridade do conjunto sintético. Ruff e formatação também passaram. A verificação de links foi ampliada para incluir a documentação dos exemplos.

Os novos testes conferem cadastro dos casos, vínculos com cenários existentes, arquivos declarados, citações literais, coerência dos gabaritos e compatibilidade das datas com a aritmética já existente. Não exercitam um extrator, confirmação humana, agenda ou bloqueio real por instrução indevida. Nenhuma taxa de qualidade ou ganho de tempo foi medida.

## Referência de segurança consultada

A OWASP descreve instruções em arquivos como uma possível origem de prompt injection indireta e recomenda validar saídas, limitar privilégios e separar conteúdo externo. Aplicamos esse raciocínio ao desenho proposto; a referência não certifica a implementação. [OWASP LLM01:2025 — Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/), consultada em 01/11/2026.
