# Casos sintéticos do Radar

01/11/2026 · Material de desenvolvimento. **Lucas aceitou a separação entre extração, cálculo e confirmação e o bloqueio por ambiguidade, conflito ou aditivo.** O [registro do primeiro fluxo](../../../docs/decisoes-primeiro-fluxo.md) distingue essa decisão dos limites de entrada implementados e das escolhas futuras de processamento.

Todos os personagens, fornecedores e documentos deste conjunto são fictícios. Os textos são trechos mínimos construídos para exercitar decisões do produto; não são modelos de contrato nem uma amostra representativa de contratos reais.

## Conteúdo inicial

| Caso | O que precisamos conferir | Resposta esperada |
|---|---|---|
| DEV-001 | Término e aviso explícitos | Término 30/06/2027; aviso 31/05/2027; agenda vazia antes de conferir |
| DEV-002 | “30 dias” sem unidade definida | Bloqueio por unidade; não publicar parcialmente os eventos |
| DEV-003 | Duas datas de término conflitantes | Preservar ambas e bloquear |
| DEV-004 | Base e aditivo | Bloquear sem consolidar efeitos nem ignorar o aditivo |
| DEV-005 | Texto completo sem eventos do recorte | Exigir conferência antes de classificar como conferido sem eventos |
| DEV-006 | Ano bissexto | 01/03/2028 menos um dia corrido resulta em 29/02/2028 |
| DEV-007 | Antecedência expressa de zero | Aviso e término em 01/05/2027; dois tipos de evento, ambos “Hoje” |
| DEV-008 | Instrução indevida dentro do texto | Preservar as regras de conferência e ausência de ações externas |

Os nove arquivos de origem estão em [development/documents](development/documents/DEV-001-base.txt). O [gabarito JSON](development/cases.json) contém a data de referência fixa **01/05/2027**, valores anotados, evidências e resultados esperados.

## Como interpretar o gabarito

- `schema_version`: versão do formato deste conjunto, não de uma API de extrator.
- `decision_status`: `accepted` registra a decisão do ADR-002; não declara aprovação de todos os detalhes do PRD nem execução do fluxo futuro.
- `split`: `development`. Estes exemplos podem ser lidos e usados para ajustar a implementação.
- `documents`: identificador dentro do caso, papel declarado e caminho relativo ao diretório do gabarito.
- `facts`: afirmações anotadas com valores normalizados e transcrições literais. Um conflito pode conter dois fatos para o mesmo campo; isso não os torna válidos para confirmação.
- `blockers`: impedimentos conhecidos com evidência. O sistema futuro deverá detectá-los; o arquivo não é usado para injetar resultados na aplicação.
- `expected.candidate_events`: eventos esperados para conferência nos casos sem bloqueio. Nos casos bloqueados, os fatos continuam disponíveis, mas nenhum evento está apto à confirmação. Esta coleção não define o formato de saída do extrator.
- `expected.agenda_before_review`: sempre vazia. Candidatos não são eventos confirmados.
- `expected.confirmation_allowed`: descreve se uma conferência válida da mesma base poderia concluir o caso; não executa confirmação.
- `expected.coverage_after_review`: situação esperada apenas depois da conferência explícita; `null` nos casos bloqueados.
- `untrusted_instruction`: referência a um trecho adversarial. Ler esse campo não autoriza executar seu conteúdo.

Uma evidência usa `document_id`, `start_line`, `end_line` e `quote`. As linhas são inclusivas e começam em 1. O texto de referência normaliza CRLF/CR para LF e remove somente um BOM inicial. Nenhum conteúdo é removido para esconder divergências.

As respostas foram anotadas a partir dos exemplos e da SPEC, sem executar extrator. Os testes comparam as evidências com os arquivos e a aritmética já existente com as datas anotadas. A adequação semântica das anotações continua exigindo revisão humana.

## Separação da avaliação

Esta entrega contém **oito casos de desenvolvimento e nenhum caso reservado**. O plano de 20 casos de desenvolvimento e 10 de avaliação continua uma proposta de tamanho; este pacote é inicial.

Antes da avaliação de um extrator, precisamos ampliar a diversidade, definir critérios de adoção e preparar um conjunto reservado separado. Exemplos já usados para ajustar código ou prompts não podem ser reapresentados como avaliação independente. Não há taxa de acerto medida nesta entrega.

## Verificação executável

Com o ambiente do projeto preparado:

```powershell
uv run --locked pytest tests/unit/test_synthetic_cases.py tests/unit/test_dates.py
```

Esses testes verificam integridade do conjunto e regras aritméticas. A CI existente também os executará via `pytest` quando esta branch for publicada. O conjunto não comprova implementação dos cenários completos C01, C02, C04, C05, C07, C10, C14 ou C16 da [SPEC](../../../docs/specs/001-primeiro-fluxo.md).
