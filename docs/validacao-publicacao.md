# Validação da publicação e da proteção da principal

Verificação realizada em 01/11/2026, após autorização explícita de Lucas para publicar o projeto, abrir o PR e configurar CI/proteção.

## 1. Publicação e conteúdo

- [Repositório público](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais).
- [PR #1 da fundação](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/pull/1), da branch `feat/fundacao-local` para `main`, mantido aberto para revisão de Lucas.
- Documentação publicada antes da implementação; o código permanece no PR enquanto não houver integração.
- As árvores Git publicadas foram comparadas com os snapshots locais: documentação `2056afc9f2489c5c98ac1556eac6aa201bc1ed9b` e fundação `4557b46d94c6d024fc30bef474040dba210bb766`.

O conector publicou commits com novos identificadores, mantendo o conteúdo. O snapshot local de documentação `148b5e6` corresponde à árvore do commit remoto `d389ec2`; a fundação local `444dfe7` corresponde à árvore do commit remoto `86992dc`. O histórico original foi preservado em branches locais de arquivo; as branches de trabalho foram alinhadas ao remoto.

## 2. CI positiva

A [execução inicial 41306712660](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/actions/runs/41306712660), para o commit remoto `86992dc`, terminou com sucesso nos dois jobs:

| Job | Evidência |
|---|---|
| `qualidade (ubuntu-latest)` | [Job aprovado](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/actions/runs/41306712660/job/124848490098) |
| `qualidade (windows-latest)` | [Job aprovado](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/actions/runs/41306712660/job/124848490839) |

Os jobs executam a instalação fixada, Ruff, formatação, pytest, links locais e verificação das dependências. A fundação tem 34 casos de teste automatizados; isso não representa cobertura dos cenários documentais ainda não implementados.

## 3. Regra aplicada à main

Exigir PR, dois checks obrigatórios com origem GitHub Actions, branch atualizada, resolução de conversas e histórico linear. Force push e exclusão da principal ficaram desabilitados. As regras se aplicam também ao administrador; a leitura da branch pela API confirmou `protected: true` e aplicação dos checks a `everyone`.

Não foi exigido um segundo aprovador inexistente. A revisão humana de Lucas é uma etapa distinta e permanece pendente.

## 4. Prova negativa controlada

Foi criado temporariamente na branch do PR o arquivo `tests/unit/test_branch_protection_probe.py`, com uma falha explícita de teste. O commit `1d630d6` gerou a [execução negativa 41307069366](https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais/actions/runs/41307069366).

Os dois jobs falharam no pytest. O GitHub informou `mergeable_state: blocked`; na interface, os checks estavam marcados como obrigatórios e o botão de integração estava desabilitado. A principal não recebeu o código da prova.

O arquivo foi removido pelo commit `3e85319`. A árvore voltou exatamente a `4557b46d94c6d024fc30bef474040dba210bb766`, igual à fundação anterior à prova. O histórico dos testes permanece disponível nas execuções e no PR, sem deixar uma falha intencional no código final.

## 5. Limites

PR publicado e checks automáticos não equivalem a revisão humana concluída. A integração do PR não foi realizada pelo agente. Esta verificação também não comprova segurança de produção, desempenho sob carga, autenticação de usuários ou qualidade de extração por IA.

Os dados técnicos observados estão em [publicacao-github.json](evidencias/publicacao-github.json). As configurações da plataforma podem mudar depois desta verificação; os links identificam as execuções observadas.
