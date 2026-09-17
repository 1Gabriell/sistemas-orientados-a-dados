# Pipelines

Esta pasta reúne os programas de preparação e integração dos dados utilizados no projeto. O `pipeline_01.py` combina informações do Censo Escolar e do IDEB para os anos de 2019, 2021 e 2023.

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

## Como executar os testes

Os testes estão armazenados junto ao pipeline e também devem ser executados a partir da raiz do repositório:

```powershell
python -m unittest discover -s pipelines/tests -v
```
