# ADR-012 — Revisão explícita das retenções de contexto

02/11/2026. **Status: decisão técnica implementada no experimento autorizado.** Aplica a separação do [ADR-002](002-proposta-limites-extracao-e-confirmacao.md); não aprova integração, modelo de produção ou revisão humana real.

## Problema e decisão

A referência do [ADR-011](011-classificacao-de-linhas-e-interpretacao-literal.md) reteve DEV-008 e DEV-020 apesar de preservar seus fatos válidos. Alterar o prompt regrediu outros casos. Manter prompt, interpretador e rodadas anteriores intactos e tratar essas retenções por revisão explícita de contexto, com versão própria `RETAINED_CONTEXT_REVIEW_V1`.

O código puro recebe todas as linhas originais, classificações, abstenção e declaração explícita de aditivo conhecido. Reinterpreta a origem pela V1; não recebe fatos editáveis nem usa gabarito para propor valores. Cada decisão precisa de alias, citação literal, tratamento e justificativa; o responsável simulado declara ter conferido o texto completo. O hash esperado inclui texto, papel, ordem/linhas, labels, abstenção, aditivo conhecido, interpretação, revisão e regra. Qualquer alteração invalida o plano. O adaptador vincula também caso e hash do relatório.

Dois tratamentos são admitidos somente em documento de papel base:

- `untrusted_instruction`: retenção `model_reports_unsupported`, prefixo explícito `INSTRUÇÃO AO ASSISTENTE:`, sem algarismos ou sinais contratuais reconhecidos pela guarda. Texto misto permanece rejeitado. O texto nunca se torna comando.
- `illustrative`: retenção `clause_inside_illustration`, com marcador imediatamente anterior não vazio no mesmo documento, contendo “exemplo”, “não define” e terminando em dois-pontos. A decisão reconhece o contexto já retido pelo interpretador; não acrescenta a data ilustrativa aos fatos.

Não existe decisão genérica para ignorar um bloqueio ou corrigir valores. Somente os findings de contexto correspondentes são resolvidos; outros findings/bloqueios permanecem, inclusive quando compartilham o código `unsupported_scope`. As evidências das pendências restantes apontam às linhas ainda não resolvidas. Conflitos, aditivos, unidades/datas inválidas e âncoras não suportadas não são resolvidos por esse mecanismo. Aditivo histórico declarado continua bloqueado; abstenção exige nova análise. Os fatos originais não mudam. Datas candidatas continuam calculadas pela regra existente.

## Proveniência e fronteiras

O recibo conserva origem completa, classificações, resultado original, decisões e resultado revisado, responsável, instante UTC e identificação da rodada. Continua `confirmed=false`, sem banco, ferramentas de negócio ou confirmação. Arquivo novo é criado exclusivamente; destino existente, inclusive parcial, é preservado. Falha de serialização não cria recibo. Uma interrupção durante a escrita pode deixar JSON incompleto; ele exige inspeção e outro destino, nunca é retomado silenciosamente como sucesso. Não há assinatura, autenticação, imutabilidade do sistema de arquivos ou recuperação persistida da aplicação.

O adaptador offline verifica componentes ativos, catálogo e todos os documentos contra os hashes da rodada preservada. Reconstrói fatos usando somente linhas/classificações; gabaritos presentes no catálogo não entram no método de revisão. O catálogo continua de desenvolvimento visível e os hashes não provam autenticidade contra alteração maliciosa simultânea do relatório e das fontes. Sem inferência nova, seleção de fornecedor ou custo de API.

## Consequências e limites

Esta é uma simulação de correção pelo agente sobre casos conhecidos, não melhoria automática de 18/20 para 20/20 nem medição de esforço humano. A guarda lexical restringe o mecanismo e pode reter outras formulações; não prova compreensão jurídica ou detecção geral de instruções. Classificação, validação literal e revisão de significado continuam distintas.

O recibo offline não pode ser importado diretamente para a agenda nem registrado como `MANUAL_V1` apagando a origem assistida. A integração deverá persistir a execução e o recibo, preservar histórico de aditivo, comparar revisão/execução/regra na transação e exigir confirmação separada. [Validação e próximo bloco](../validacao-revisao-retencoes.md) detalham resultados e pendências.

Fonte primária reaberta em 02/11/2026: [OWASP — Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/). Restringir autoridade e exigir decisão externa à entrada fundamentam a fronteira; a eficácia específica acima é limitada aos testes e à simulação registrados.
