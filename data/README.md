# Dados do projeto

Tabelas CSV e consultas SQL do Censo Escolar e do IDEB para o **Nordeste**, obtidas no Google BigQuery pela **Base dos Dados**, com origem no **Inep**. O sufixo `2019+` indica o recorte de **2019, 2021 e 2023**.

## Tabelas de origem no BigQuery

- [Censo Escolar — tabela `escola`](https://console.cloud.google.com/bigquery?p=basedosdados&d=br_inep_censo_escolar&t=escola&page=table&project=estudos-dados-500323&ws=!1m6!1m5!4m3!1sbasedosdados!2sbr_inep_censo_escolar!3sescola!23sLEGACY_URL_PARAM)
- [IDEB — tabela `escola`](https://console.cloud.google.com/bigquery?p=basedosdados&d=br_inep_ideb&t=escola&page=table&project=estudos-dados-500323&ws=!1m6!1m5!4m3!1sbasedosdados!2sbr_inep_ideb!3sescola!23sLEGACY_URL_PARAM)

## Tabelas disponíveis

| Arquivo | Descrição |
| --- | --- |
| [censo_educacional_nordeste.csv](censo_educacional_nordeste.csv) | Base histórica de infraestrutura, recursos e matrículas escolares, com 50 atributos(Não está presente, pois o arquivo é muito grande para o repositório, mas é possível obter através da query). |
| [censo_nordeste_2019+.csv](censo_nordeste_2019+.csv) | Censo no recorte atualizado: **240.386 registros × 50 atributos**. |
| [ideb_nordeste.csv](ideb_nordeste.csv) | IDEB, projeções e identificação das escolas, com 12 atributos e valores ausentes em `ideb`. |
| [ideb_nordeste_sem_nulos.csv](ideb_nordeste_sem_nulos.csv) | Versão com indicadores de aprovação, rendimento e desempenho, com 14 atributos e registros anteriores a 2019. |
| [ideb_nordeste_2019+.csv](ideb_nordeste_2019+.csv) | IDEB no recorte atualizado: **79.374 registros × 14 atributos**. |

## Consultas SQL

| Arquivo | Filtros |
| --- | --- |
| [censo_educacional_nordeste_query.sql](censo_educacional_nordeste_query.sql) | Censo do Nordeste, sem restrição de ano. |
| [censo_nodeste_2019+_query.sql](censo_nodeste_2019+_query.sql) | Censo do Nordeste em 2019, 2021 e 2023. |
| [ideb_nordeste_sem_nulos_query.sql](ideb_nordeste_sem_nulos_query.sql) | IDEB do Nordeste em 2019, 2021 e 2023, com `ideb` preenchido. |
| [ideb_nordeste_2019+.sql](ideb_nordeste_2019+.sql) | IDEB do Nordeste em 2019, 2021 e 2023, com `ideb` preenchido. |


A chave da base integrada é **`id_escola + ano + anos_escolares`**. Como o arquivo do Censo tem granularidade de escola e ano e não possui `anos_escolares`, o pipeline associa primeiro a cada registro do Censo as etapas únicas observadas no IDEB. O cruzamento final é então validado como 1:1 pelas três colunas. Veja o [README principal](../README.md) e a [caracterização e avaliação de qualidade](../docs/caracterizacao_2019+.md) para mais detalhes.
