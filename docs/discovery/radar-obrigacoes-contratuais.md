# Radar de Obrigações Contratuais — discovery inicial

Data: 31/10/2026.

**Decisões confirmadas por Lucas:** tema Radar de Obrigações Contratuais; case fictício da Agência Prisma criado do zero; foco em renovações e avisos prévios em contratos de serviços com fornecedores; planejamento anterior à implementação. Aceite registrado no [ADR-001](../adrs/001-recorte-do-produto.md).

**Situação deste documento:** discovery fictício com case e recorte aceitos. O detalhamento da primeira versão está proposto no [PRD](../PRD.md) e na [SPEC](../specs/001-primeiro-fluxo.md), ainda em rascunho. Todos os nomes, episódios e condições contratuais abaixo são fictícios. Não houve entrevista com cliente nem validação de demanda.

## 1. O que sabemos e o que continua sendo hipótese

- A escolha do tema é uma decisão de Lucas.
- Já existe uma categoria comercial de gestão de obrigações e renovações. A página oficial da Docusign consultada descreve essas funcionalidades. Isso confirma a existência da categoria, sem provar demanda pelo nosso produto ou seu desempenho.
- A ideia de que poucos participantes escolherão este tema não está confirmada. O mural público consultado não revela projetos que ainda não foram submetidos.
- A dor, a frequência dos problemas, o esforço manual e o valor de uma solução para o negócio proposto são hipóteses de um case fictício.
- Vamos buscar diferenciação no recorte e em evidências de comportamento: origem da informação, revisão, cobertura de análise, versões e reação a dados insuficientes.

## 2. Case adotado

| Elemento | Definição do case |
|---|---|
| Negócio | Agência Prisma, empresa fictícia de serviços digitais que contrata fornecedores recorrentes |
| Cliente do projeto | Marina Costa, diretora de operações, responsável por avaliar continuidade e renegociação de fornecedores |
| Usuário principal | Rafael Lima, analista administrativo que mantém os registros e prepara a lista de contratos que precisam de decisão |
| Produto | Radar de Obrigações Contratuais |
| Família de documentos | Contratos sintéticos de prestação de serviços recorrentes com fornecedores, em português |
| Recorte aceito para a primeira versão | Marcos de renovação e prazos de aviso de não renovação |
| Decisão apoiada | Quais contratos exigem análise nesta semana, qual prazo candidato fundamenta essa prioridade e quais casos ainda não podem ser considerados conferidos? |

O produto ajuda a organizar uma decisão administrativa simulada. Uma data próxima não determina, por si só, uma obrigação de cancelar nem uma infração contratual.

## 3. Fluxo atual e episódio de dor — ficção do case

No processo proposto, Rafael recebe documentos, guarda arquivos em pastas e transcreve datas em uma planilha. Marina consulta essa lista antes de decidir se mantém um fornecedor. Quando chega um aditivo ou uma correção, a relação com o contrato anterior pode ficar pouco clara.

Episódio fictício: a planilha mostra o fim de um contrato em junho. A equipe revisa a contratação perto dessa data e só então percebe uma cláusula que previa um aviso anterior. O problema a investigar é a distância entre a data visível na planilha e a janela em que a equipe precisava tomar uma decisão.

Não estamos atribuindo perda financeira medida à agência. O episódio serve para formular o problema e criar cenários de teste.

### Conversa simulada para iniciar o discovery

**Pergunta:** o que você precisa saber ao abrir o sistema na segunda-feira?

**Marina, personagem fictícia:** quais contratos precisam de uma decisão, até quando e quais informações ainda faltam para confiar nessa lista.

**Pergunta:** qual é seu maior medo em automatizar a leitura?

**Marina:** uma data parecer confirmada quando foi deduzida sem base ou extraída de um documento que já não deveria orientar aquela decisão.

**Pergunta:** o que faria a ferramenta atrapalhar?

**Rafael, personagem fictícia:** esconder os contratos que não conseguiu analisar e dar a impressão de que a lista está completa.

**Pergunta:** que explicação você precisa conseguir dar depois?

**Rafael:** de qual documento e cláusula saiu a informação, quem conferiu e o que mudou quando recebemos uma nova versão.

Essas respostas foram criadas para o case; são hipóteses a examinar, não depoimentos coletados.

## 4. Proposta de primeira versão

O fluxo demonstrável seria:

1. Registrar contratos sintéticos em texto e identificar os documentos fornecidos para cada contrato. A escolha de começar com texto deixa a extração de PDF e o OCR para uma decisão posterior.
2. Identificar candidatos a marcos de renovação e prazos de aviso, preservando documento, versão e trecho de origem de cada campo relevante.
3. Verificar se há informação suficiente e consistente para calcular uma data candidata segundo regras explicitamente definidas para o case.
4. Apresentar uma fila de revisão: o usuário confere, corrige ou rejeita a extração, com histórico. Qualquer correção manual deve registrar autor e motivo, sem parecer uma extração automática do documento.
5. Exibir uma agenda interna com os itens confirmados e uma área visível para análises pendentes, ambiguidades e falhas. Toda notificação de negócio permanece dentro da simulação.

O primeiro fluxo deve demonstrar a diferença entre três informações:

- **O que está escrito:** datas, períodos e condições citados no documento.
- **O que foi calculado:** uma data derivada desses campos por uma regra identificável.
- **O que foi conferido:** uma confirmação humana ligada à versão dos dados efetivamente revisada.

Se a primeira versão usar IA para extrair campos, a saída será uma proposta verificável. O cálculo de datas deverá ser reproduzível e testado separadamente. O desenho final depende de avaliar uma alternativa sem IA e dos limites de tempo e orçamento.

## 5. Exemplo que torna o problema concreto

Considere um documento sintético que fixa o término em **30/06/2027** e descreve um aviso com antecedência mínima de **30 dias corridos**. Para o cenário de teste, definimos explicitamente a regra de cálculo como data do término menos 30 dias, sem ajuste por fim de semana ou feriado.

O resultado esperado dessa regra do case é **31/05/2027**. Esse cálculo aritmético foi conferido localmente; não representa um comportamento já implementado no produto nem uma interpretação jurídica aplicável a contratos reais.

O usuário deve conseguir ver o trecho que informa o término, o trecho que informa a antecedência, a regra aplicada e a situação da revisão. Guardar apenas a data final apagaria informações necessárias para verificar o resultado.

Se o texto disser somente “30 dias” e o case não definir uma convenção aplicável, ou se o prazo depender de um evento cuja data não foi fornecida, a resposta esperada será uma pendência de revisão. Não completaremos a informação com um palpite.

## 6. Casos críticos que precisam orientar as especificações

| Caso | Comportamento que propomos exigir |
|---|---|
| Prazo e término explícitos, sem conflito | Propor dados com evidências, calcular pela regra do case e solicitar conferência |
| Antecedência ausente ou unidade ambígua | Explicitar a ausência ou ambiguidade; impedir que a informação apareça como confirmada |
| Prazo dependente de evento sem data conhecida | Registrar a condição e a dependência pendente; não inventar vencimento |
| Cláusulas com datas incompatíveis | Destacar o conflito e encaminhar para revisão |
| Contrato recebido duas vezes | Identificar repetição e evitar duplicar obrigações ou itens de agenda |
| Contrato com aditivo fornecido | Manter bloqueio explícito na primeira versão, sem presumir vigência pela ordem de envio nem consolidar seus efeitos automaticamente |
| Informação revisada em uma versão e alterada depois | Preservar histórico e tornar visível que a confirmação anterior não cobre a nova informação |
| Falha na leitura ou na extração | Manter o contrato visível como análise incompleta; nunca traduzir falha como ausência de obrigações |
| Trecho citado existe, mas não sustenta o campo proposto | Rejeitar a associação na revisão e na avaliação; existência de uma citação não prova correção semântica |
| Documento contém instruções ao agente | Tratar o conteúdo como dado, sem permitir que altere as regras ou autorize ações |

No detalhamento proposto para a primeira versão, aditivos ficam identificados e bloqueados. Consolidar automaticamente seus efeitos seria uma expansão distinta. O sistema também deverá informar quais documentos foram fornecidos; ele não pode garantir a inexistência de aditivos que nunca recebeu.

## 7. O que fica fora da proposta inicial

- Extração de todo tipo de obrigação e interpretação de qualquer contrato.
- Calendários de dias úteis, regras legais de contagem e interpretação de legislação.
- Parecer jurídico, determinação de validade, negociação ou recomendação automática de cancelamento.
- Documentos reais, OCR, assinatura eletrônica e comunicações para terceiros.
- Integrações com e-mail, mensageria, sistemas financeiros e calendários externos.
- Consolidação automática geral de aditivos e versões conflitantes.
- Operação de várias empresas no mesmo ambiente, integrações em produção e arquitetura distribuída sem requisito demonstrado.

As exclusões são propostas de escopo. Elas não justificam ocultar situações não suportadas: o produto deverá identificá-las para revisão quando forem encontradas.

## 8. Como avaliar sem mascarar erros

Antes da implementação, construiremos exemplos sintéticos com respostas esperadas e justificativas conferidas a partir da regra do case. O conjunto de avaliação deverá incluir situações positivas, negativas e ambíguas, com variação de redação; um conjunto reservado servirá para verificar se a solução generaliza além dos exemplos usados no desenvolvimento.

Medições propostas, ainda sem metas numéricas aprovadas:

- Obrigações esperadas que foram detectadas e obrigações que ficaram de fora, avaliadas por tipo de cenário.
- Campos extraídos corretamente e sustentados pelo trecho associado.
- Datas calculadas corretamente nos casos em que todos os dados necessários estão disponíveis.
- Casos ambíguos ou incompletos encaminhados para revisão, incluindo liberações incorretas.
- Cobertura da análise: contratos processados, incompletos e com falha, sempre com denominador visível.
- Tempo e quantidade de correções na conferência manual simulada, comparados ao fluxo com o Radar, se essa avaliação couber no projeto.

Também registraremos resultados antes e depois da revisão humana. Acerto obtido após uma correção manual não será atribuído à extração automática. Uma porcentagem de confiança declarada pela própria IA não será tratada como medida de precisão.

## 9. Próximas decisões de produto

1. Case e recorte já foram aceitos por Lucas; os detalhes do PRD/SPEC e o desenho da conferência serão revisados na próxima decisão de produto.
2. O [plano de entrega](../plano-de-entrega.md) propõe a tarefa de demonstração, os marcos e as dependências.
3. Lucas informou disponibilidade superior a 10 horas por semana. Orçamento e estimativa de esforço continuam em aberto.
4. Aplicação local modular e ferramentas foram aceitas nos [ADR-003](../adrs/003-aplicacao-local-modular.md) e [ADR-004](../adrs/004-proposta-tecnologias-locais.md). Instalação e método de extração continuam em aberto. Lucas solicitou uma [proposta futura de evolução](../evolucao-arquitetural.md) para escala e desempenho.

O domínio também permite exercitar Engenharia de Dados: transformar texto em informação estruturada, modelar contratos e versões, preservar origem e histórico, medir qualidade e recuperar falhas de processamento. As ferramentas aceitas ainda precisam de validação integrada no ambiente local.

## 10. Fontes e limites da pesquisa

Consultadas em 31/10/2026:

- [Docusign Agreement Manager](https://www.docusign.com/products/platform/agreement-manager): fonte primária do fornecedor que descreve extração de dados, gestão de renovações/obrigações e recursos de auditoria. É evidência da oferta comercial, não comprovação independente de resultados ou validação do nosso case.
- [Mural oficial de projetos da Jornada](https://github.com/suajornadadedados/desafio-jornada/blob/main/PROJETOS.md), obtido pelo conector GitHub; SHA `318cdfe1723b30f04f1fab1d92452136b8c89c7e`. É um índice público de submissões e não permite prever os temas dos demais participantes.
- [Enunciado do Desafio Livre](https://github.com/suajornadadedados/desafio-jornada/blob/main/desafio-livre/README.md), conferido na etapa anterior: dados sintéticos, ações simuladas, decisões documentadas e arquitetura explicada.

Não realizamos pesquisa representativa de mercado, avaliação jurídica ou teste de extração neste momento. A aritmética de datas pode ser conferida isoladamente, sem representar execução do produto.
