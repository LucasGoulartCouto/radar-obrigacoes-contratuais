# ADR-009 — Comparar extração fora do fluxo de confirmação

Data: 01/11/2026. **Status: decisão técnica do experimento implementada no escopo autorizado.** Não escolhe fornecedor, orçamento, limiar de adoção ou integração de extrator ao produto.

## Contexto

O caminho manual já chega à agenda. Antes de integrar extração, precisamos distinguir campo encontrado, evidência literal, suporte semântico, bloqueio e evento candidato. Ajustar contra os mesmos exemplos não produz avaliação independente. O ADR-002 mantém extração, cálculo e confirmação separados.

## Decisão

Executar um baseline simples por gramáticas de linhas completas, identificado como `REGEX_EXPERIMENT_V1`, e um avaliador offline em `infrastructure/experiments/`. O método recebe apenas documentos preparados, com papel e ID local para citar evidências; o avaliador guarda IDs dos casos, gabaritos e expectativas. A aplicação não importa nem seleciona esse adaptador.

Ampliar o desenvolvimento de 8 para 20 casos (21 documentos), preservando as oito anotações anteriores. Todos são visíveis e usados para desenvolvimento; nenhum é reservado. Não alterar a semântica de `AVISO_CORRIDOS_V1`. O cálculo dos candidatos reutiliza a regra existente; candidatos do experimento não entram no banco ou na agenda.

Pontuar fatos por correspondência estrita de campo, valor e suporte anotado. Uma citação existente sem suportar o campo não é um acerto. Para bloqueios, comparar código e evidência anotada; para eventos, tipo e data. Preservar falsos positivos, omissões, abstenções e falhas, sem converter falha em resultado vazio. Essa pontuação depende da anotação e não substitui adjudicação semântica humana de citações alternativas válidas.

O relatório identifica hashes do método, catálogo e documentos, numeradores/denominadores e tempo de extração mais pontuação. O comando não usa rede, ferramentas de ação ou banco, não confirma e não sobrescreve evidência anterior. A CLI só executa este método local; não oferece importação de respostas de API nesta entrega.

## Alternativas e consequências

Manter somente plano textual adiaria a descoberta de falhas concretas. Integrar já à tela confundiria experimento com fluxo operacional e exigiria antes estados persistidos, recuperação, concorrência e seleção de resultado. Um experimento isolado permite medir o método simples sem assumir esses compromissos.

As falhas observadas são resultado da comparação, não falhas dos testes do avaliador: uma regra pode acertar datas simples e sugerir evento indevido quando ignora contexto. Não ampliar padrões até obter 100% e chamar o mesmo conjunto de avaliação final.

IA local e API hospedada permanecem alternativas não executadas. [Comparação e protocolo](../comparacao-extracao.md) registram fontes oficiais e decisões necessárias. O [registro de validação](../validacao-experimento-extracao.md) liga comportamentos aos testes e à execução. Integração futura requer nova decisão com evidências, limites de processamento e recuperação, orçamento quando aplicável e reconferência da base.
