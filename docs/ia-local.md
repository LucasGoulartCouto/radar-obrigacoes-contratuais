# IA local no desenvolvimento do Radar

Decisão de Lucas em **01/11/2026**: usar IA local agora. Planejar a IA em produção e escolher o melhor modelo **depois da aplicação concluída**. [ADR-010](adrs/010-ia-local-no-desenvolvimento.md).

## O que está sendo preparado

Ollama portátil 0.40.13 em `.tools/ollama/v0.40.13/`, com modelos em `.tools/ollama/models/`. Candidato provisório: `qwen3:4b-instruct-2507-q4_K_M`, aproximadamente 2,5 GB, digest `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`. A seleção serve para desenvolver a aplicação; não é benchmark de “melhor modelo”.

O servidor usa somente `127.0.0.1:11435`, `OLLAMA_NO_CLOUD=1`, um modelo carregado e uma execução por vez. Scripts não mudam o PATH global nem criam serviço/autostart. O preparo baixa runtime/pesos oficiais; sem API paga. A inferência local não envia documentos para fornecedor de modelo.

## Resultado do primeiro candidato

A [rodada V2](evidencias/ia-local-v2.json) concluiu 20 casos de desenvolvimento: 6 correspondências integrais, 3 respostas rejeitadas e 19 candidatos indevidos. Entre os 11 casos bloqueados no gabarito, 9 perderam o impedimento e 2 falharam na validação. **O candidato está disponível para desenvolvimento, sem liberação para alimentar a aplicação.** A falha da rodada não foi escondida: a CLI retornou erro e preservou o relatório.

Esses erros motivaram o protocolo por linhas abaixo. A rodada anterior permanece preservada; a aplicação continua manual até a integração ter evidências adequadas.

## Protocolo por linhas — referência atual

O método `OLLAMA_LINE_EXPERIMENT_V1`, prompt `LINE_CLASSIFICATION_V1` e interpretação `LITERAL_CLAUSES_V1` separam classificação por IA da leitura literal no código. A IA classifica todas as linhas não vazias; não normaliza datas/números/unidades. O código monta as evidências diretamente da origem, preserva ambiguidades e aplica guardas conservadoras. [ADR-011](adrs/011-classificacao-de-linhas-e-interpretacao-literal.md).

A [rodada de referência](evidencias/ia-local-linhas-v1.json) alcançou 18/20 casos integrais, sem candidatos indevidos/falhas técnicas e com os 11 impedimentos esperados reconhecidos. Duas retenções extras omitiram 3 candidatos válidos. Uma tentativa de esclarecer mais o prompt regrediu para 16/20 e foi rejeitada; seu [relatório](evidencias/ia-local-linhas-v2.json) e código foram preservados antes de restaurar a referência.

São resultados da combinação IA + código em desenvolvimento conhecido, sem avaliação independente. Citações agora são montadas pelo código, sem atribuir essa transcrição ao modelo. Não há integração à UI/banco ou liberação para confirmação automática. A [validação detalhada](validacao-extracao-por-linhas.md) identifica resultados, regressão, guardas e pendências.

## Comandos no Windows

Com o ambiente Python do projeto preparado:

```powershell
powershell -File scripts/Preparar-IA-Local.ps1
powershell -File scripts/Avaliar-IA-Local.ps1
```

O primeiro comando verifica o SHA-256 do pacote oficial e o digest do modelo. Reutiliza somente o processo registrado para este projeto e falha se a porta estiver ocupada por outro processo; não encerra serviços alheios. O download inicial precisa de internet e de espaço para pacote extraído, arquivo e pesos.

O segundo comando usa por padrão o protocolo por linhas nos 20 casos de desenvolvimento e cria um JSON novo em `.tools/ollama/results/`. Para escolher um destino novo: `powershell -File scripts/Avaliar-IA-Local.ps1 -Saida .tools/resultado-ia-local.json`. Não sobrescreve evidência anterior nem repete uma rodada com `.partial.json` existente. O parcial registra progresso e distingue conclusão, interrupção e fonte alterada. Para reproduzir o método antigo de valores normalizados, use `-Metodo v2` (não é o prompt V2 do protocolo por linhas). O comando demora conforme a máquina; não repetir enquanto a rodada anterior estiver em execução.

O preparo só configura variáveis no processo da sessão. Não há configuração de API paga ou credencial no código. Runtime, pesos, logs e estado do processo ficam fora do Git. O runtime pode manter arquivos próprios no perfil do usuário; copiar apenas o repositório não preserva o ambiente já preparado.

## Fronteira experimental e limites

Método anterior `OLLAMA_LOCAL_EXPERIMENT_V1` preservado para reprodução; protocolo ativo por linhas identificado acima, com schema dinâmico e interpretação versionada. O modelo recebe documentos/papéis/linhas, sem gabarito, expectativas ou ferramentas de ação. A validação rejeita campos extras, coerções, datas inválidas, evidência não literal, saída cortada, modelo diferente e orçamento de contexto excedido.

Configuração inicial: 8.192 tokens de contexto, até 1.536 de saída, temperatura 0 e seed 42. A entrada tem orçamento conservador em bytes somando instrução, schema e documentos, com reserva de saída/overhead. Excesso falha antes de enviar e não trunca texto. Isso pode recusar textos aceitos pela entrada documental do produto; ainda não existe processamento por partes.

Timeout de socket de até 120 segundos, sem repetição automática. Não é garantia de prazo global/cancelamento da geração; a conexão é fechada ao falhar e o servidor pode levar tempo para liberar a execução. O relatório diferencia falha, abstenção e resultado vazio. Citações literais não garantem suporte semântico; o resultado continua sujeito a avaliação e conferência.

O cliente consulta versão/modelo local antes da rodada, exige GGUF com digest esperado e não segue redirecionamentos HTTP. Não há fallback para nuvem ou download disparado pela extração. O JSON registra versão, digest, parâmetros, hashes do método/avaliador/entradas, contagens e propostas validadas para inspeção; não registra o corpo bruto das falhas.

Este comando é um experimento, sem escrita no banco ou confirmação de eventos. Os próximos passos são integrar a execução e a conferência à aplicação com rastreabilidade e recuperação. Planejamento de produção/seleção definitiva de modelo ficam na etapa posterior definida por Lucas.

## Fontes primárias

Consultadas em 01/11/2026:

- [Ollama no Windows](https://docs.ollama.com/windows): pacote portátil e execução nativa.
- [Release oficial 0.40.13](https://github.com/ollama/ollama/releases/tag/v0.40.13): pacote Windows; SHA-256 usado `7afa38624fa62ee5d8293422d0ab084c1bb4603134c7f4dafce11a033b57cc19`.
- [Modelo provisório](https://ollama.com/library/qwen3:4b-instruct-2507-q4_K_M): variante, quantização e licença indicada.
- [Ollama FAQ](https://docs.ollama.com/faq): modo sem nuvem, bind local e contexto.
- [API de chat](https://docs.ollama.com/api/chat) e [saída estruturada](https://docs.ollama.com/capabilities/structured-outputs): formato, metadados e schema.

Essas fontes documentam mecanismos, sem provar qualidade da extração neste projeto. A [validação da entrega](validacao-ia-local.md) mantém resultados efetivamente observados.
