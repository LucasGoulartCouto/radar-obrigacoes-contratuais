# ADR-004 — Tecnologias da primeira aplicação local

**Status: aceito por Lucas em 01/11/2026; fundação implementada.** Após a apresentação da combinação Python, Streamlit, SQLite, SQLAlchemy, Alembic, uv, pytest e Ruff, Lucas respondeu “concordo” e pediu uma proposta posterior de evolução. O ambiente isolado foi preparado e verificado; versões e alcance estão no [registro de validação](../validacao-fundacao.md). O aceite não comprova as funcionalidades documentais ainda não implementadas.

## Contexto e critérios

Precisamos executar no Windows, mostrar evidência ao lado de campos revisáveis, manter histórico persistente, publicar confirmações de forma atômica e reproduzir o ambiente. A primeira versão é local, com baixa concorrência de escrita e dados sintéticos pequenos. Não há requisito atual de API pública, hospedagem ou cliente separado.

## Decisão

| Responsabilidade | Opção escolhida | Motivo no nosso recorte |
|---|---|---|
| Linguagem | Python, usando a série 3.14 disponível como primeira candidata | Permite concentrar regras, interface e acesso a dados na mesma linguagem; compatibilidade do conjunto ainda será testada |
| Interface | Streamlit servido no endereço local do computador | Permite construir a tarefa de conferência em Python, com formulários e evidências próximas dos campos |
| Armazenamento | SQLite em arquivo local | Atende a persistência da simulação sem configurar um servidor de banco separado |
| Acesso a dados | SQLAlchemy, série compatível a fixar | Mantém consultas, mapeamentos e transações no módulo de persistência; a aplicação continua usando interfaces próprias |
| Evolução de esquema | Alembic | Permite versionar mudanças do banco e verificar atualizações preservando os dados |
| Ambiente e dependências | uv, com `pyproject.toml` e arquivo de dependências resolvidas | Permite isolar o projeto e repetir versões escolhidas, após resolver e testar a instalação |
| Verificação | pytest e Ruff | Cenários de negócio, integração com o banco e verificações de código; outras ferramentas só entrarão por necessidade concreta |

Pydantic ou outro validador de fronteira poderá ser avaliado ao definir o formato do extrator. Nenhum fornecedor de IA, framework de agentes, banco vetorial ou serviço de nuvem integra a decisão base.

## Alternativas por camada

| Escolha | Alternativas viáveis | Por que a proposta parece adequada agora |
|---|---|---|
| Interface Streamlit | FastAPI com páginas HTML; interface desktop; linha de comando | A tarefa principal é conferir campos e texto no mesmo fluxo. Streamlit reduz o trabalho de composição de uma interface em Python neste recorte. FastAPI com templates continua viável se precisarmos de maior controle da interação |
| SQLite | PostgreSQL local; arquivos JSON/CSV | O banco local atende as relações e transações necessárias sem operação de servidor. Arquivos isolados exigiriam implementar coordenação entre histórico, revisão e agenda. PostgreSQL ganha relevância com outros requisitos de operação e concorrência |
| SQLAlchemy | Módulo `sqlite3` diretamente | `sqlite3` reduz dependências; SQLAlchemy oferece uma organização conveniente para consultas e transações em um modelo que terá várias entidades. A mudança futura de banco ainda exigiria testes e possivelmente mudanças específicas |
| Alembic | Scripts SQL numerados; recriação do banco | Scripts SQL seriam viáveis; Alembic acompanha o acesso proposto por SQLAlchemy. Recriar o banco como rotina perderia histórico e não atende à evolução da simulação persistente |
| uv | `venv` e `pip` com versões fixadas | Ambas atendem um ambiente isolado. uv é a recomendação para centralizar resolução e execução; sua instalação ainda precisa ser feita e validada |

Essa comparação é uma avaliação de engenharia para este projeto, não um benchmark entre ferramentas.

## Cuidados que fazem parte da proposta

- Streamlit reexecuta o código da tela em interações. Submissões devem chamar casos de uso explícitos; rerenderizar uma tela não pode confirmar eventos, repetir extrações pagas ou duplicar registros.
- Estado de sessão serve para rascunhos, navegação e filtros. Documentos, resultados e confirmações vivem no banco.
- Compartilhar configuração ou uma fábrica de conexões não significa compartilhar uma transação entre telas. A sessão de banco deve ter duração limitada ao caso de uso.
- Verificaremos o controle transacional do driver SQLite e a ativação de chaves estrangeiras em cada conexão, conforme a documentação do SQLAlchemy.
- SQLite tem um escritor por vez. Escritas curtas e tratamento explícito de bloqueio atendem a proposta; não manter transação de escrita aberta enquanto aguarda um extrator.
- O serviço da interface ficará no endereço de loopback local. A demonstração inicial não pressupõe exposição na rede.

## Evidência local disponível

No diagnóstico anterior à implementação, foram verificados Python **3.14.3**, SQLite **3.50.4** e Git **2.53.0.windows.2**. As ferramentas faltantes foram então instaladas em diretórios isolados do projeto: uv em `.tools/bootstrap` e dependências em `.venv`. As versões resolvidas constam em `uv.lock`.

A documentação consultada lista suporte à série 3.14. Nesta etapa, a compatibilidade da fundação foi verificada também por execução local, 34 testes e uma segunda instalação usando o wheel gerado e o mesmo lock/cache. Isso não equivale a validação em Linux ou do produto completo.

## Como validar antes de iniciar o produto

1. Preparar um ambiente isolado e resolver as dependências, sem alterar os pacotes globais de outros projetos.
2. Abrir uma página local mínima e verificar formulário com texto e campos, inclusive reexecução e reenvio.
3. Criar um banco temporário por migração; confirmar integridade referencial e rollback de uma operação interrompida.
4. Verificar uma tentativa de confirmação desatualizada e uma submissão repetida, usando banco em arquivo temporário.
5. Testar uma migração com dados e um backup/restauração de referência.
6. Registrar as versões que funcionaram e tornar a instalação reproduzível.

Essas verificações orientaram a fundação. Foram executadas para cadastro, edições, transações e pacote; o teste de migração cobre criação/reexecução do esquema inicial. Confirmação de obrigação/revisão documental e evolução para outro esquema ainda exigirão verificações próprias. Se houver incompatibilidade futura, registraremos o resultado e a alteração necessária.

## Limites e condição para rever

A interface precisa ser avaliada pelo fluxo de revisão, não apenas por exibir uma tabela. Se o modelo de interação do Streamlit atrapalhar conferência, navegação ou testes, rever a interface mantendo o núcleo de negócio separado. Se houver necessidade de vários escritores remotos, reavaliar persistência e forma de implantação.

Uma eventual API de IA poderá acrescentar tráfego externo e custo; isso será uma decisão própria, com teto e medição. A base local escolhida pode ser desenvolvida sem contratar hospedagem.

Lucas também solicitou uma proposta posterior de evolução para escala e desempenho. Essa entrega está registrada no [plano de evolução](../evolucao-arquitetural.md); não implica implantação de infraestrutura adicional agora.

## Fontes primárias consultadas nesta etapa

- [Streamlit: instalação e versões de Python](https://docs.streamlit.io/get-started/installation/command-line).
- [Streamlit: formulários](https://docs.streamlit.io/develop/concepts/architecture/forms) e [estado de sessão](https://docs.streamlit.io/develop/concepts/architecture/session-state).
- [SQLite: usos adequados e concorrência](https://www.sqlite.org/whentouse.html).
- [SQLAlchemy: SQLite, transações e chaves estrangeiras](https://docs.sqlalchemy.org/en/21/dialects/sqlite.html).
- [Alembic: migrações](https://alembic.sqlalchemy.org/en/latest/).
- [uv: resolução e sincronização de dependências](https://docs.astral.sh/uv/concepts/projects/sync/).
- [pytest: integração do projeto](https://docs.pytest.org/en/stable/explanation/goodpractices.html) e [Ruff](https://docs.astral.sh/ruff/).
- [FastAPI: páginas com templates](https://fastapi.tiangolo.com/advanced/templates/), alternativa considerada para a interface.
