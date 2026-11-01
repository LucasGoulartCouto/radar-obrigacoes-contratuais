# SPEC-001 — Do contrato sintético à agenda conferida

Versão 0.1 · 31/10/2026 · Proposta de comportamento, anterior à implementação.

Referência: [PRD](../PRD.md). Esta SPEC define regras do case fictício, sem estabelecer interpretação jurídica para contratos reais. Limites, nomes de estados e detalhes técnicos ainda estão sujeitos à revisão de produto.

## 1. Conceitos e unidade de processamento

- **Contrato:** cadastro estável do caso acompanhado, com identificador próprio.
- **Documento:** texto sintético recebido, com conteúdo e origem preservados.
- **Revisão documental:** conjunto identificado dos documentos declarados para um contrato. Acrescentar, remover ou substituir documento cria outra revisão, sem apagar a anterior.
- **Execução de análise:** tentativa de ler uma revisão com um método identificado. Reexecutar não substitui silenciosamente os resultados anteriores.
- **Candidato:** evento proposto pela análise, ainda sem confirmação humana.
- **Evento:** término ou aviso de não renovação ligado ao ciclo explicitamente informado. Não é uma decisão de cancelar nem uma conclusão sobre descumprimento.
- **Revisão humana:** conferência de candidatos e da cobertura da análise, vinculada à revisão documental, à execução selecionada e à versão das regras.

Um contrato pode ter várias revisões e execuções, mas apenas uma base de análise selecionada para a visão atual. Uma revisão pode produzir zero, um ou mais candidatos. O recorte automático suporta um término não ambíguo e até um aviso associado ao ciclo informado; múltiplos ciclos ou regras concorrentes exigem revisão fora do processamento automático.

## 2. Entradas e origem

O cadastro deve informar identificador/título do contrato e os documentos fornecidos. O conteúdo deve ser sintético, em português e em texto UTF-8. O cadastro declara o papel conhecido de cada documento: base, aditivo, substituição ou desconhecido. O papel declarado não comprova precedência jurídica.

Preservar os bytes recebidos. Para localizar evidências, produzir um texto de referência versionado com quebras CRLF/CR normalizadas para LF e eventual marcador BOM inicial removido na leitura. Nenhuma outra reescrita pode ocorrer sem mudar a versão do procedimento. Numerar linhas a partir de 1, mantendo linhas vazias.

Uma evidência identifica documento/revisão, intervalo inclusivo de linhas e transcrição literal das linhas referidas. O sistema compara a transcrição com o texto de referência. Isso valida a localização; a revisão e a avaliação precisam conferir também se o trecho sustenta o campo.

Reenvio com o mesmo texto de referência, mesmo papel e conjunto documental inalterado no mesmo contrato não cria nova revisão nem evento. Diferenças relevantes no conteúdo, no conjunto documental ou no papel declarado criam outra revisão. O mesmo arquivo associado a outro contrato não pode provocar fusão automática dos cadastros.

Limites máximos de bytes, documentos por revisão e duração de processamento são configurações obrigatórias, a definir com a tecnologia. Ultrapassá-los deve produzir rejeição/pendência explícita antes de uma confirmação. O texto não pode ser truncado e apresentado como análise completa.

## 3. Campos necessários

| Informação | Origem e requisito |
|---|---|
| Término do ciclo informado | Data explícita e válida, com ano e evidência; armazenar em formato normalizado sem perder a grafia de origem |
| Aviso de não renovação | Existência e condição identificadas no texto; não presumir que toda renovação exige aviso |
| Antecedência | Inteiro não negativo e unidade explicitamente de dias corridos; preservar a evidência |
| Data-âncora do aviso | Deve ser o término identificado neste recorte; outro evento torna a regra não suportada |
| Data candidata do aviso | Derivada pelo código, com versão da regra e identificação das entradas usadas |
| Responsável interno | Informação do cadastro do case; não apresentar como parte extraída do contrato |
| Método e base de análise | Identificação da revisão, execução e método que produziram os candidatos |

Uma data pode ser corrigida manualmente somente com justificativa e evidência associada. O valor original e a origem manual da correção ficam preservados. Ausência de suporte não pode ser resolvida apenas por uma caixa de confirmação.

## 4. Regra de datas do case

Regra `AVISO_CORRIDOS_V1`: data candidata do aviso = data explícita do término − quantidade de dias corridos explicitamente informada.

- Operar com datas, sem horário; não ajustar sábados, domingos ou feriados.
- Aceitar zero quando constar expressamente; número negativo, fracionário ou conflitante impede o cálculo confirmado.
- Não converter meses, anos ou dias úteis para dias corridos.
- Não inferir uma data ausente a partir de duração ou de eventos cuja ocorrência não foi registrada.
- Datas impossíveis e divergências entre algarismos e texto por extenso são pendências.
- Um prazo cuja data já passou continua visível. A situação temporal não prova infração nem cumprimento.

Data de referência da simulação e horizonte de atenção devem estar visíveis e reproduzíveis. Proposta inicial: horizonte de 30 dias, inclusivo nas duas pontas para itens futuros. Para um evento confirmado de data D e uma referência R:

| Condição | Rótulo temporal |
|---|---|
| D < R | Data ultrapassada |
| D = R | Hoje |
| R < D ≤ R + 30 dias | Próximos 30 dias |
| D > R + 30 dias | Depois do horizonte |

Os quatro grupos não se sobrepõem. O filtro padrão pode priorizar os três primeiros, sem remover o acesso aos demais. A simulação da passagem do tempo não modifica o conteúdo confirmado nem indica que alguma ação foi realizada.

## 5. Estados e invariantes

Separar três aspectos que não podem ser confundidos:

1. Execução técnica: pendente, em processamento, concluída ou falhou.
2. Resultado da conferência: pendente, bloqueado, confirmado com eventos ou confirmado sem eventos no recorte.
3. Situação temporal dos eventos confirmados, calculada pela seção anterior.

Uma execução concluída não significa conferência concluída. Uma execução falha não significa ausência de eventos. A confirmação sem eventos exige conferência explícita do resultado vazio e não afirma que o contrato inteiro não possui obrigações.

Para a contagem de cobertura da carteira, cada contrato entra em exatamente uma situação, segundo esta precedência:

1. **Bloqueado:** existe impeditivo conhecido na base atual, como aditivo ou conflito não resolvido.
2. **Falha de análise:** a execução selecionada falhou sem um impeditivo já classificado acima.
3. **Aguardando análise:** falta execução concluída, inclusive processamento em andamento.
4. **Revisão pendente:** a análise terminou, mas não existe conferência válida para a base atual.
5. **Conferido com eventos:** revisão válida e ao menos um evento confirmado.
6. **Conferido sem eventos no recorte:** revisão válida de análise vazia.

Detalhes de situações anteriores continuam acessíveis no histórico. A soma dos seis grupos deve ser igual à quantidade de contratos cadastrados, inclusive aqueles com novos documentos ainda pendentes de análise.

## 6. Confirmação, alteração e recuperação

A confirmação só pode ocorrer se a revisão documental, a execução selecionada e a versão da regra ainda forem as mesmas que o usuário viu. Exigir evidências localizadas, cálculo válido quando aplicável, ausência de bloqueios e identificação do revisor do case.

Uma confirmação registra, como uma única operação lógica, resultado revisado, eventos vigentes e histórico. Se falhar antes de concluir, nenhum evento pode aparecer como confirmado parcialmente. Se duas ações concorrerem ou a base mudar durante a conferência, rejeitar a ação desatualizada e pedir atualização da tela.

Ao receber uma alteração documental, mudar a versão da regra ou selecionar uma análise com resultado diferente, a confirmação anterior deixa de valer para a visão atual. O contrato volta à pendência e seus eventos anteriores aparecem apenas no histórico, identificados como desatualizados. A visão principal precisa destacar a necessidade de reconferência; retirar um evento da agenda não pode esconder o contrato.

Reexecutar com a mesma base e produzir um resultado idêntico não duplica eventos. A implementação pode reaproveitar uma análise concluída ou registrar outra tentativa idêntica sem substituir a execução selecionada. Resultado diferente, se selecionado para a visão atual, exige nova conferência. Tentativas iniciadas e interrompidas devem ser recuperáveis, sem serem contadas como concluídas.

Para a primeira versão, um aditivo declarado ou identificado mantém o contrato bloqueado. Não consolidar seus efeitos, não selecionar a cláusula mais recente pela ordem de envio e não permitir confirmar apenas ignorando o arquivo. Resolver esse caso automaticamente fica fora do escopo; o resultado esperado da demonstração pode ser a pendência bem explicada.

## 7. Exibição e fronteira do extrator

Na conferência, exibir texto de origem e contexto junto aos campos propostos, distinguindo valores extraídos, derivados e corrigidos. Identificar motivo de bloqueio e próxima informação necessária. Identificadores técnicos completos podem ficar em detalhes, sem sobrecarregar a tarefa do usuário.

O extrator propõe campos e evidências. Ele não confirma eventos, não decide qual documento está vigente, não executa código vindo de documentos e não recebe ferramentas de envio ou alteração de contratos. A aplicação valida a estrutura e as referências antes de permitir a conferência. Texto retornado deve ser renderizado como dado, sem executar HTML, comandos ou links incorporados como ações.

## 8. Cenários obrigatórios para futura verificação

As respostas abaixo foram definidas antes da implementação. Elas serão material para testes e demonstração, não são resultados já obtidos.

| ID | Entrada/ação | Resultado esperado |
|---|---|---|
| C01 | Término 30/06/2027; aviso de 30 dias corridos; evidências válidas | Data candidata 31/05/2027; agenda vazia até confirmação |
| C02 | Término 01/03/2028; aviso de 1 dia corrido | Data candidata 29/02/2028 |
| C03 | Término 01/03/2027; aviso de 1 dia corrido | Data candidata 28/02/2027 |
| C04 | Aviso explicitamente de zero dias corridos | Data candidata igual ao término, sujeita à conferência |
| C05 | Documento diz apenas “30 dias”, sem unidade/convenção aplicável | Bloqueio por unidade não definida; não presumir dias corridos |
| C06 | Prazo ancorado em evento sem data conhecida | Pendência de evento; não inventar vencimento |
| C07 | Datas de término conflitantes ou uma data impossível | Bloqueio e evidências do conflito/erro |
| C08 | Envio idêntico repetido no mesmo contrato | Nenhuma revisão ou evento de negócio duplicado |
| C09 | Mesmo documento associado a outro contrato | Cadastros separados; nenhuma fusão automática |
| C10 | Documento com aditivo fornecido | Bloqueio do contrato; nenhuma confirmação automática de efeito do aditivo |
| C11 | Mudança documental após confirmação | Confirmação desatualizada; contrato em pendência e evento anterior acessível no histórico |
| C12 | Usuário confirma uma tela cuja base mudou | Operação rejeitada sem publicação parcial |
| C13 | Falha/interrupção na análise ou saída com formato inválido | Falha registrada; contrato visível; nenhum resultado vazio tratado como sucesso |
| C14 | Análise concluída sem candidatos em documento sem evento do recorte | Revisão explícita do vazio; somente depois pode ficar conferido sem eventos no recorte |
| C15 | Citação inexistente ou existente sem sustentar o campo | Primeira bloqueada por validação; segunda detectável na revisão e na avaliação semântica |
| C16 | Texto inclui instrução para confirmar ou enviar mensagem | Nenhuma confirmação, ferramenta ou envio comandado pelo documento |
| C17 | Confirmação falha antes de persistir todos os dados | Nenhum evento parcialmente confirmado; tentativa e falha recuperáveis |
| C18 | Entrada excede o limite configurado | Rejeição/pendência explícita; sem truncamento silencioso |
| C19 | Referência 01/05/2027; eventos em 30/04, 01/05, 31/05 e 01/06 | Respectivamente: ultrapassada, hoje, próximos 30 dias e depois do horizonte |
| C20 | Carteira com contratos nas seis situações de cobertura | Soma dos grupos igual ao total, sem duplicação nem omissão |
| C21 | Nova execução da mesma base com resultado diferente | Preservar resultados e exigir nova conferência antes de atualizar a agenda |
| C22 | Número negativo/fracionário ou divergente do valor por extenso | Bloqueio do cálculo, com motivo identificado |

## 9. Pendências para implementação

- Definir limites operacionais e tecnologia, mantendo os comportamentos acima.
- Transformar cenários em dados sintéticos e respostas esperadas, com conjuntos de desenvolvimento e avaliação separados.
- Definir o mecanismo de identificação do revisor no protótipo e declarar seus limites.
- Especificar o formato de intercâmbio do extrator após escolher a alternativa técnica.

Metas de qualidade do extrator serão tratadas no PRD após o experimento inicial. Estas regras não dependem de uma marca de modelo ou framework.
