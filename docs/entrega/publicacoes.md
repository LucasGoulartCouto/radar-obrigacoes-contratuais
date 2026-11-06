# Rascunhos de divulgação — não enviados

Atualizado em 05/11/2026. Rascunhos para Lucas adaptar. O agente não publicou posts; URLs reais de divulgação ainda não foram fornecidas. Só adicionar os links ao cartão depois de existirem publicações reais. Confirmar autor, estado final do PR #13 e números antes de usar em outra data.

## LinkedIn

Estou desenvolvendo o Radar de Obrigações Contratuais para o Desafio Livre da Jornada de Dados.

O case é fictício: na Agência Prisma, a equipe precisa conferir términos de contratos e prazos de aviso de não renovação sem confundir sugestão com informação confirmada.

A decisão central foi separar responsabilidades: a IA local classifica linhas, o código valida literais/evidências e calcula datas, e a conferência registra a decisão sobre a base atual. Um documento não pode mandar o sistema confirmar eventos ou enviar mensagens.

O projeto usa Python, Streamlit, SQLite, SQLAlchemy, Alembic e uv. O desenvolvimento com Codex segue contexto, ADRs, testes e PRs. Validei o fluxo local, revisei os PRs e autorizei sua integração; o histórico registra os resultados e as limitações.

Em 02/11/2026, os 371 testes passaram também em uma cópia com ambiente e banco novos. A referência automática continua em 18/20 casos de desenvolvimento conhecidos; correções de contexto e conferências simuladas são registradas separadamente. Não houve avaliação reservada nem uso de contratos reais.

O aprendizado mais útil até aqui foi preservar uma regressão de prompt em vez de escolher uma versão pelo exemplo que ela corrigiu.

Código, decisões e limites: https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais

A consolidação na `main` segue a integração autorizada dos PRs #1–#13. Produção e escolha definitiva do modelo continuam como etapa posterior. Os testes locais da linha mais recente chegaram a 383, incluindo uma disputa de gravação reproduzida e corrigida durante a integração.

## Comunidade da Jornada

Meu projeto para o Desafio Livre é o Radar de Obrigações Contratuais, no case sintético da Agência Prisma.

O usuário fictício precisa saber quais contratos merecem atenção, de onde saiu cada data e quais análises ainda não podem ser consideradas conferidas. O recorte inicial acompanha término do ciclo e aviso de não renovação; não produz parecer jurídico, cancela contrato ou envia avisos a fornecedores.

Comecei pelo discovery, pelo recorte e pelas decisões de separar sugestão, cálculo e confirmação. A aplicação local tem documentos versionados, levantamento manual, análise assistida, conferência separada, agenda, cobertura e histórico de tentativas/falhas.

A IA classifica linhas; o código interpreta os valores na origem e calcula. Foi necessário preservar uma tentativa de prompt que regrediu e restaurar a referência anterior. Os resultados automáticos e as correções simuladas não foram somados para apresentar uma taxa melhor.

Em 02/11/2026, reproduzi o preparo, a validação e o início em uma cópia nova nesta máquina Windows: 371 testes aprovados, banco separado e backup no segundo preparo. O caminho com IA reutilizou o runtime local já instalado; não foi uma instalação de sistema operacional ou pesos do zero.

Repositório: https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais

A versão consolidada fica na `main` após a conclusão do PR #13, com validação funcional e integração autorizadas. Ainda faltam avaliação independente e decisões de produção. Os documentos explicam o que foi medido, simulado e deixado para depois.
