# Pipelines

Esta pasta reúne os programas de preparação e integração dos dados utilizados no projeto. O `pipeline_01.py` combina informações do Censo Escolar e do IDEB para os anos de 2019, 2021 e 2023. O `pipeline_02_atributos.py` lê a base integrada, sem alterá-la, e gera a matriz de atributos por escola e ano usada no agrupamento.

## Como executar o pipeline 01

Os comandos abaixo devem ser executados a partir da raiz do repositório, pois os caminhos padrão das entradas e saídas são relativos a ela.

### Preparação do ambiente

É necessário utilizar Python 3.10 ou uma versão mais recente.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Execução com os caminhos padrão

```powershell
python pipelines/pipeline_01.py
```

O comando utiliza os seguintes arquivos:

| Tipo | Caminho padrão |
| --- | --- |
| Entrada do Censo | `data/censo_nordeste_2019+.csv` |
| Entrada do IDEB | `data/ideb_nordeste_2019+.csv` |
| Base integrada | `data/processed/base_integrada.csv` |
| Relatório de auditoria | `data/processed/relatorio_execucao.json` |

### Execução com caminhos personalizados

```powershell
python pipelines/pipeline_01.py --censo caminho/censo.csv --ideb caminho/ideb.csv --saida caminho/base_integrada.csv --relatorio caminho/relatorio.json
```

Para consultar todas as opções disponíveis:

```powershell
python pipelines/pipeline_01.py --help
```

## Como executar o pipeline 02

O pipeline 02 depende da base integrada gerada pelo pipeline 01:

```powershell
python pipelines/pipeline_02_atributos.py
```

| Tipo | Caminho padrão |
| --- | --- |
| Entrada | `data/processed/base_integrada.csv` (somente leitura) |
| Matriz de atributos por escola-ano | `data/processed/atributos_escola_ano.csv` |
| Ligação com as etapas e o IDEB | `data/processed/ligacao_etapas.csv` |
| Relatório de auditoria | `data/processed/relatorio_atributos.json` |

As colunas excluídas por ausência estrutural e o limiar de remoção das variáveis quase constantes podem ser alterados com `--excluir` e `--limiar-quase-constante`. Consulte `python pipelines/pipeline_02_atributos.py --help`.

## Como executar o agrupamento

Depois do pipeline 02:

```powershell
python modelos/agrupamento.py
```

Os resultados são gravados em `data/processed/agrupamento/` (`atribuicoes.csv`, `perfis_clusters.csv` e `metricas.json`). O número de grupos, o conjunto de atributos e a ponderação por dimensão podem ser alterados com `--k`, `--conjunto` e `--sem-ponderacao`. Com `--ano 2019` (ou 2021, 2023), o agrupamento é feito só com as escolas daquele ano e os resultados vão para `data/processed/agrupamento/<ano>/`. A execução leva alguns minutos, pois o K-Means é ajustado para k de 2 a 10 e repetido nas análises de estabilidade.

## Como executar os testes

Os testes estão armazenados junto ao pipeline e também devem ser executados a partir da raiz do repositório:

```powershell
python -m unittest discover -s pipelines/tests -v
```
