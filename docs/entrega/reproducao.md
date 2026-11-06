# Reproduzir a instalação

Use somente documentos sintéticos. O caminho principal é Windows com Python 3.14.3 acessível como `python`, acesso à internet para dependências e espaço para os ambientes. O modelo local é opcional para o levantamento manual. A reprodução executada está no [registro de validação](../validacao-reproducao.md).

## 1. Obter a versão certa

Em uma pasta nova:

```powershell
git clone --branch codex/reproducao-e-entrega https://github.com/LucasGoulartCouto/radar-obrigacoes-contratuais.git radar-repro
cd radar-repro
python --version
powershell -NoProfile -File scripts/Preparar-Ambiente.ps1
```

Essa branch reúne o código e os materiais sob revisão. Não usar a `main` para representar a versão funcional antes do merge dos PRs. O snapshot funcional reproduzido foi `39befe7e8c3d52fb10a251f93d4515ca27a9ac8e`; o PR desta entrega informa seu HEAD final.

O preparo cria `.tools/bootstrap`, instala uv 0.13.6, cria `.venv`, sincroniza `uv.lock` e migra o banco em `var/`. Não copia dados do computador do autor. Em primeira execução, a carteira começa vazia. Se já houver banco, o preparo cria backup antes de conferir/aplicar as migrações. Não apague o banco para corrigir erro de instalação.

## 2. Iniciar e conferir a carteira vazia

```powershell
powershell -NoProfile -File scripts/Iniciar-Radar.ps1
```

Abra [a interface local](http://127.0.0.1:8501). Sem modelo configurado, o Radar informa a indisponibilidade da IA e mantém o levantamento manual. Cadastre um contrato fictício e recarregue: ele deve permanecer, aguardando documentos/análise. Receber documentos não é concluir a análise.

Se a porta já estiver em uso, escolha outra somente para essa sessão:

```powershell
$env:STREAMLIT_SERVER_PORT = '8503'
powershell -NoProfile -File scripts/Iniciar-Radar.ps1
```

Encerre com `Ctrl+C` no terminal que iniciou a interface. A variável não muda a configuração permanente do projeto. Depois da reprodução, feche esse terminal ou remova a variável com `Remove-Item Env:STREAMLIT_SERVER_PORT`.

## 3. Usar um caso sintético

No contrato cadastrado, receba [DEV-001-base.txt](../../tests/fixtures/contracts/development/documents/DEV-001-base.txt) como documento base. O término explícito é 30/06/2027; o aviso é de 30 dias corridos em relação ao término. O código calcula 31/05/2027.

No caminho manual, informe esses campos e selecione as linhas literais de origem. Salve o levantamento e confira que ainda não existem eventos confirmados. Confirme separadamente depois de ler o texto completo, os valores e os trechos. O responsável é personagem da simulação; não use o nome de Lucas para sugerir revisão real que não ocorreu.

## 4. Habilitar a IA local de desenvolvimento

Siga [IA local](../ia-local.md):

```powershell
powershell -NoProfile -File scripts/Preparar-IA-Local.ps1
powershell -NoProfile -File scripts/Iniciar-Radar.ps1
```

O preparo da IA pode precisar baixar runtime e pesos. O início reutiliza os metadados locais em `.tools/ollama/model.json`. Não há chave/API paga ou troca automática de modelo. Se o runtime já estiver preparado em outro checkout e disponível no mesmo loopback, uma sessão de teste pode informar explicitamente o digest já verificado em `RADAR_LOCAL_MODEL_DIGEST`; isso reutiliza o runtime, não demonstra instalação nova dos pesos.

Na tela, **Analisar documentos** cria uma tentativa. **Usar resultado para conferência** escolhe uma proposta. **Confirmar conferência** é outra ação, vinculada à revisão atual. Uma falha fica no histórico; iniciar nova tentativa exige ação explícita. Não trate abstenção ou falha como ausência de eventos.

## 5. Verificar e preservar

```powershell
powershell -NoProfile -File scripts/Validar-Projeto.ps1
.\.tools\bootstrap\Scripts\uv.exe run --locked radar backup
```

Os comandos verificam lock, código, testes, referências locais e dependências. O backup usa um arquivo novo. Guarde `var/` e seus backups separadamente do clone: eles não entram no Git. A documentação de [continuidade](../agents/continuidade.md) explica o que um clone preserva.

## Alcance comprovado

Na execução de 02/11/2026, a cópia começou sem `.venv`, `.tools`, `.uv-cache` ou `var`. O preparo baixou as dependências, criou banco vazio e os 371 testes passaram no Python dessa cópia. Foram exercitados início sem IA, cadastro persistido, backup no segundo preparo e falha/recuperação com runtime local já existente.

Foi a mesma máquina Windows, com Python já instalado. Não equivale a instalação de sistema operacional limpo, execução por outra pessoa, novo download dos pesos ou validação independente da extração. O [registro](../validacao-reproducao.md) identifica os snapshots, passos e resultados.

Fontes primárias reabertas em 02/11/2026: [uv — sincronização e lock](https://docs.astral.sh/uv/concepts/projects/sync/) e [Streamlit — configuração por sessão](https://docs.streamlit.io/develop/concepts/configuration/options).
