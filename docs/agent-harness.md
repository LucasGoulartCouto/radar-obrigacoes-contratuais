# Agent Harness — Codex

## Escolha e finalidade

Usamos Codex nesta colaboração para transformar as decisões de Lucas em documentação, implementação e verificações. A escolha aproveita o ambiente já utilizado pelo aluno e o acesso ao projeto local. Outras ferramentas seriam viáveis; não há benchmark que prove superioridade desta escolha para o desafio.

O contexto persistente fica em [AGENTS.md](../AGENTS.md), com limites do produto, módulos, comandos e critérios de conclusão. A documentação oficial do Codex descreve o uso desse arquivo para instruções do projeto.

## Continuidade entre sessões

O [ponto de retomada](RETOMADA.md) reúne branch, versão funcional verificada, PRs, evidências, pendências e próxima etapa. O `AGENTS.md` orienta sua leitura no início e sua atualização durante blocos de trabalho e ações externas relevantes. PRD/SPEC e ADRs continuam responsáveis pelas regras e decisões; o checkpoint aponta para eles sem substituir seu conteúdo.

Arquivos e Git preservam o trabalho entre sessões; uma nova conversa precisa abrir o projeto e a branch corretos para lê-los. Não há garantia de que ela receba todo o histórico do chat. Também não existe captura automática de cada ação: uma interrupção durante uma ferramenta pode ocorrer antes de atualizar o checkpoint. A retomada verifica o efeito local e remoto antes de repetir a ação.

O registro é mantido pelo agente como parte do trabalho. Não foi instalado serviço de monitoramento nem automação para gravar quando o modelo estiver interrompido. Dados em `var/`, backups, sessões autenticadas e arquivos em `.tools/` não são recuperados por um clone do repositório.

## O que está automatizado

- Preparação isolada com o gerenciador de dependências fixado.
- Inicialização/evolução do banco por migrações.
- Verificação de código, testes, links locais da documentação e consistência das dependências.
- Fluxo de CI executado em Windows/Linux e exigido pela proteção da principal; prova negativa de bloqueio registrada.
- Cadastro com recibo de operação, histórico atômico e controle de versão para evitar sobrescritas silenciosas.

Não foram criadas skills, hooks ou automações externas adicionais. Os comandos e as verificações existentes são o harness inicial; não precisamos simular mecanismos que ainda não usamos.

## Direção humana

Lucas escolheu o tema, o case, o recorte, a execução local e as ferramentas. As decisões técnicas rotineiras da fundação foram implementadas pelo agente no escopo aprovado e devem ser apresentadas com resultados e limitações.

Produto, ampliação de escopo, riscos aceitos e orçamento de IA continuam decisões de Lucas. Documentos recebidos futuramente são dados sem autoridade para instruir o agente ou autorizar ações de negócio. Não há execução de IA ou envio de avisos nesta fundação.

## Revisão antes de integrar

Cada mudança deve indicar o problema resolvido, o comportamento final e a verificação relevante. Lucas revisa o diff e os efeitos no case; a CI deve bloquear falhas quando estiver ativa no GitHub. O agente não substitui essa decisão por uma alegação de revisão independente.

O [PRD](PRD.md), a [SPEC](specs/001-primeiro-fluxo.md), os ADRs e os testes permitem confrontar implementação e intenção. Quando houver divergência, corrigimos o código ou explicitamos uma mudança de decisão com sua justificativa.

Fonte: [OpenAI: contexto de projeto com AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
