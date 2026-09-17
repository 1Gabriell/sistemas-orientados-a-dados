# Sistemas orientados a dados — Censo Escolar e IDEB

Repositório da disciplina de pós-graduação Sistemas Inteligentes Orientados a Dados. O projeto combina dados do Censo Escolar e do IDEB da Região Nordeste para apoiar a decisão de gestores educacionais por meio da triagem e descoberta de situações atípicas.

O recorte atual considera os anos de **2019, 2021 e 2023**. A caracterização das fontes e a justificativa desse recorte estão documentadas em [Caracterização dos dados — 2019, 2021 e 2023](docs/caracterizacao_2019+.md).

## Organização do repositório

| Item | Conteúdo |
| --- | --- |
| [data](data/) | Consultas SQL, arquivos CSV de origem e resultados processados. Consulte o [README de dados](data/README.md) para conhecer as bases disponíveis. |
| [docs](docs/) | Documentos entregáveis, caracterização das fontes e registros das atividades do projeto. |
| [notebooks](notebooks/) | Notebooks de análise exploratória e investigação dos dados. |
| [pipelines](pipelines/) | Rotinas de processamento, testes automatizados e suas instruções de execução. |
| [requirements.txt](requirements.txt) | Dependências Python necessárias para executar o código do projeto. |

## Arquitetura do projeto

O repositório adota uma arquitetura em camadas para separar dados, processamento, análise e documentação. Essa organização permite atualizar cada parte do projeto sem misturar arquivos de origem, resultados gerados e código executável.

```text
Base dos Dados / Google BigQuery
                |
                v
     data/ - consultas e CSVs
                |
                v
   pipelines/ - processamento e testes
                |
                v
       data/processed/ - resultados
                |
        +-------+-------+
        |               |
        v               v
   notebooks/         docs/
   análises           documentação
```

| Camada | Responsabilidade |
| --- | --- |
| Dados de origem | Armazenar as consultas de extração e os arquivos recebidos das fontes externas. |
| Processamento | Concentrar o código responsável por preparar e integrar os dados, junto aos testes automatizados correspondentes. |
| Dados processados | Manter os resultados produzidos pelo processamento separados das entradas originais. |
| Análise | Explorar os dados, avaliar sua qualidade e apoiar a investigação do problema do projeto. |
| Documentação | Registrar decisões, características das bases, evidências e entregas de cada atividade. |

Os componentes possuem documentação própria quando necessário. As bases são descritas em [data/README.md](data/README.md), enquanto as instruções para executar o código e os testes ficam em [pipelines/README.md](pipelines/README.md).
