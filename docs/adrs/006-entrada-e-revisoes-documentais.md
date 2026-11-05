# ADR-006 — Entrada e revisões documentais

01/11/2026 · **Implementado no escopo autorizado por Lucas para receber e versionar documentos.** Decisão técnica do agente, preservando as responsabilidades aceitas no ADR-002.

## Problema

Precisamos distinguir mudança documental de reenvio equivalente. Preservar somente o texto normalizado perderia a origem recebida; usar somente os bytes para identificar a revisão criaria versões para diferenças de BOM ou quebras de linha. Uma gravação parcial poderia ainda deixar a revisão atual apontando para arquivos incompletos.

## Decisão

- Guardar arquivos originais como bytes no SQLite, junto ao texto de referência e aos hashes SHA-256 de ambos. Nomes são metadados; não são caminhos para gravação no disco.
- Usar `TEXT_REFERENCE_V1`: decodificar UTF-8, remover um BOM inicial e normalizar CRLF/CR para LF. Não aparar espaços, remover linhas vazias ou reescrever o texto. A validação rejeita texto vazio, controles incompatíveis e formatos não suportados.
- Identificar o conjunto lógico pela versão do normalizador e pelo conjunto ordenado de pares `(papel, hash do texto de referência)`. Ordem de envio, nome e variações equivalentes de bytes não criam revisão. Repetir um membro com o mesmo texto e papel dentro do conjunto é erro explícito.
- Comparar somente com a revisão atual. Voltar de A para B e depois A cria a revisão 3, preservando a mudança de base; não reativar silenciosamente uma revisão antiga.
- Preservar cada envio aceito por um recibo e seus bytes, inclusive variantes equivalentes. Um novo recibo equivalente não gera nova revisão nem evento de negócio. Repetir o mesmo identificador de operação reaproveita o recibo sem gravar arquivos adicionais.
- Separar `document_version` de `record_version`: mudar o nome do cadastro não é mudar a base documental.
- Gravar revisão, arquivos, recibo, atualização do contador e histórico em uma transação. Comparar a versão exibida dentro dessa escrita; falha ou tela desatualizada não publica parte do conjunto.

## Limites aplicados

Padrões: **262.144 bytes por documento**, **1.048.576 bytes por conjunto** e **até 5 documentos**. Os três tetos se aplicam ao conjunto completo, incluindo arquivos mantidos da revisão anterior. Há variáveis de ambiente documentadas para ajustá-los; valores inválidos impedem a inicialização com uma mensagem útil. São limites do protótipo, não capacidade comprovada sob carga.

O transporte da interface usa limite por arquivo em megabytes inteiros; no padrão, 1 MB. O limite exato de bytes e o limite agregado são conferidos pela aplicação antes da persistência. O filtro `.txt` do navegador não substitui a validação. Não há truncamento.

Retirar o último documento exige declaração explícita e cria uma revisão vazia. O histórico permanece acessível e a situação volta a “Aguardando documentos”. Isso não equivale a uma análise concluída sem eventos.

## Aditivo conhecido

Um aditivo declarado no histórico mantém a sinalização de bloqueio mesmo depois de retirada ou mudança do papel do arquivo em outra revisão. Isso materializa a regra aceita de não contornar um aditivo ignorando-o. Resolver precedência ou corrigir esse bloqueio mediante um processo de conferência permanece fora desta versão; não existe liberação automática.

A implementação usa o papel declarado. Não detecta aditivos disfarçados no texto nem interpreta cláusulas. A ausência dessa sinalização não prova que a base está livre de impedimentos. Confirmação e agenda ainda não existem nesta entrega.

## Persistência e migração

A migração `0002_documents` acrescenta o contador documental ao cadastro e cria `document_revisions` e `document_uploads`. Recibos continuam em `operations`; apenas mudanças de revisão acrescentam `documents_revised` ao histórico de negócio. Chaves estrangeiras e restrições apoiam a integridade.

O SQLite continua adequado ao primeiro recorte local. Armazenar os bytes com a transação evita coordenar gravações entre arquivos externos e banco. O custo é crescimento do banco a cada novo envio aceito, mesmo equivalente. A política futura de retenção e o eventual armazenamento de objetos precisarão preservar as origens e os vínculos; o limite de uma entrada não é uma cota total do banco.

Logs registram identificador de operação, resultado, quantidade, bytes e duração; não registram texto nem nome dos arquivos. Parâmetros SQL ficam ocultos nas mensagens de erro do mecanismo.

## Alternativas consideradas

- Arquivos externos e metadados no banco: permitem separar armazenamento no futuro, mas exigiriam outra estratégia para atomicidade e recuperação.
- Identidade somente pelos bytes: preserva formato, mas duplica revisões equivalentes.
- Guardar somente o texto normalizado: simplifica a leitura, mas descarta a origem recebida.
- Reutilizar qualquer revisão histórica de mesmo conteúdo: evita uma linha, mas pode esconder uma mudança de base relevante para conferência.

## Verificação e limites

O [registro de validação](../validacao-entrada-documental.md) distingue testes, migração do banco local e operações reais no navegador. Não houve benchmark, teste de autenticação, avaliação de extração nem implementação de confirmação ou agenda.

Referências consultadas em 01/11/2026: [Streamlit — upload e validação pela aplicação](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader), [SQLAlchemy — tipos binários](https://docs.sqlalchemy.org/en/21/core/type_basics.html#sqlalchemy.types.LargeBinary), [Alembic — operações de migração](https://alembic.sqlalchemy.org/en/latest/ops.html).
