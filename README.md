# Sistemas orientados a dados — Censo Escolar e IDEB

Repositório da disciplina de pós-graduação Sistemas Inteligentes Orientados a Dados. O projeto combina dados do Censo Escolar e do IDEB da Região Nordeste para apoiar a decisão de gestores educacionais por meio da triagem e descoberta de situações atípicas.

## Organização do repositório

| Pasta | Conteúdo |
| --- | --- |
| [docs](docs/) | Documentos entregáveis do projeto, incluindo a caracterização das bases e a avaliação inicial da qualidade dos dados. |
| [data](data/) | Tabelas utilizadas no projeto, em formato CSV, e consultas SQL executadas no Google BigQuery sobre os dados disponibilizados pela Base dos Dados. Consulte o [README de dados](data/README.md) para conhecer os arquivos. |
| [notebooks](notebooks/) | Notebooks utilizados no projeto até o momento. |
| [src](src/) | Código executável do pipeline de preparação, validação e integração. |

O recorte atualizado considera os anos de **2019, 2021 e 2023**. A descrição desse recorte está em [Caracterização dos dados — 2019, 2021 e 2023](docs/caracterizacao_2019+.md).

## Pipeline da Atividade 02

O programa recebe os dois CSVs de origem, padroniza e valida os dados, ajusta a granularidade e gera uma base integrada confiável. A chave da base final é, obrigatoriamente:

```text
id_escola + ano + anos_escolares
```

Usar somente `id_escola + ano` seria incorreto: no IDEB, uma escola pode ter resultados de mais de uma etapa no mesmo ano. Nos arquivos atuais, isso corresponde a 17.049 repetições por escola e ano. A chave tripla não possui duplicidades.

### Como a granularidade é compatibilizada

O CSV do Censo possui uma linha por `id_escola + ano` e não contém a coluna `anos_escolares`. Já o IDEB possui uma linha por escola, ano e etapa. Por isso, antes do cruzamento final, o pipeline:

1. extrai do IDEB as combinações únicas de `id_escola + ano + anos_escolares`;
2. associa essas etapas aos registros do Censo por `id_escola + ano`, com validação muitos-para-um;
3. passa a ter uma visão do Censo na granularidade escola–ano–etapa;
4. cruza essa visão com o IDEB usando as três colunas e exige uma relação 1:1.

Esse procedimento replica para cada etapa apenas os atributos escolares do Censo, como infraestrutura e matrículas. Nenhum valor de IDEB é agregado, descartado ou inventado.

### Passo a passo

1. Leitura de `data/censo_nordeste_2019+.csv` e `data/ideb_nordeste_2019+.csv`.
2. Verificação das colunas obrigatórias.
3. Padronização de `ano`, identificadores, `anos_escolares` e indicadores numéricos.
4. Filtro dos anos 2019, 2021 e 2023.
5. Validação de valores ausentes nas chaves.
6. Validação de duplicidades no Censo por `id_escola + ano` e no IDEB pela chave tripla.
7. Validação dos domínios dos indicadores (por exemplo, IDEB entre 0 e 10 e aprovação entre 0 e 100).
8. Expansão controlada do Censo para a granularidade escola–ano–etapa.
9. Cruzamento 1:1 por `id_escola + ano + anos_escolares`.
10. Verificação de consistência de UF e município entre as fontes.
11. Validação final da chave e gravação do CSV processado e do relatório de auditoria.

### Como executar

É necessário Python 3.10 ou mais recente. Na raiz do repositório:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python src/pipeline.py
```

Os caminhos podem ser alterados pela linha de comando:

```powershell
python src/pipeline.py --censo caminho/censo.csv --ideb caminho/ideb.csv --saida caminho/base_integrada.csv --relatorio caminho/relatorio.json
```

Para consultar todas as opções:

```powershell
python src/pipeline.py --help
```

### Entradas e saídas

| Tipo | Caminho padrão | Conteúdo |
| --- | --- | --- |
| Entrada | `data/censo_nordeste_2019+.csv` | Infraestrutura, recursos e matrículas por escola e ano. |
| Entrada | `data/ideb_nordeste_2019+.csv` | Indicadores educacionais por escola, ano e etapa. |
| Saída | `data/processed/base_integrada.csv` | Base integrada na granularidade da chave tripla. |
| Saída | `data/processed/relatorio_execucao.json` | Contagens, descartes, correspondências e resultado das validações. |

O pipeline encerra com código de erro e não substitui a saída final se encontrar colunas ausentes, chaves nulas ou duplicadas, tipos inválidos, indicadores fora dos domínios aceitos ou divergências geográficas entre as fontes.

### Evidência da execução com os arquivos atuais

| Medida | Resultado |
| --- | ---: |
| Registros recebidos do Censo | 240.386 |
| Registros recebidos do IDEB | 79.374 |
| Chaves do IDEB sem correspondência no Censo | 0 |
| Registros produzidos | 79.374 |
| Duplicidades na chave final | 0 |
| Valores ausentes na chave final | 0 |

Os números são recalculados em toda execução e ficam registrados em `data/processed/relatorio_execucao.json`.
