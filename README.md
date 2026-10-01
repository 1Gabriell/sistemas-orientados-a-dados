# Sistema de Apoio à Gestão Educacional — Censo Escolar e IDEB

Repositório do projeto da disciplina de pós-graduação **Sistemas Inteligentes Orientados a Dados** (PGCOMP · UFBA · 2026.2). O projeto desenvolve um sistema de apoio à decisão para gestores educacionais da Região Nordeste. O sistema identifica **anomalias**, descobre **padrões** e define **prioridades de atenção** entre as escolas, a partir da integração do Censo Escolar com o IDEB.

## O projeto

| Pergunta | Resposta |
| --- | --- |
| Qual problema existe? | Entre milhares de escolas, o gestor não consegue ver quais fogem do padrão do seu perfil nem por quê. Ordenar as escolas pelo menor IDEB ignora o contexto de cada uma. |
| Quem sente o problema? | Gestores educacionais das redes municipais e estaduais. O sistema apoia a decisão, mas não decide por eles. |
| Quais dados ajudam? | Censo Escolar (240.386 escolas-ano × 50 atributos) e IDEB (79.374 registros × 14 atributos) de 2019, 2021 e 2023, integrados em uma base de 79.374 linhas × 61 colunas. |
| Que decisão é apoiada? | Onde concentrar a atenção: escolas anômalas em relação aos seus pares, priorizadas com motivos explícitos e situadas nos padrões descobertos. |

## Funcionalidades previstas

As três funcionalidades trabalham em conjunto: **perfil da escola → padrão do grupo → anomalia → prioridade explicada**.

| Funcionalidade | Descrição | Abordagem prevista |
| --- | --- | --- |
| Detecção de anomalias | Sinaliza escolas que fogem do esperado para o seu grupo de pares, como desempenho destoante, quedas bruscas entre edições do IDEB ou combinações incomuns de características. | Isolation Forest, LOF ou métodos baseados em distância |
| Descoberta de padrões | Agrupa as escolas por perfil a partir dos próprios dados, sem grupos definidos de antemão, e revela características associadas aos resultados. | Agrupamento (*clustering*) |
| Prioridades de atenção | Combina desempenho, evolução, infraestrutura, tecnologia, recursos humanos e comparação com os pares em um nível de prioridade, sempre acompanhado dos motivos. | Indicadores por dimensão |

## Recorte e dados

Os dados vêm do **Censo Escolar da Educação Básica** e do **IDEB**, produzidos pelo Inep e obtidos por meio da [Base dos Dados](https://basedosdados.org/) no Google BigQuery. O recorte considera as escolas dos nove estados do Nordeste nos anos de **2019, 2021 e 2023** pelos seguintes motivos:

- várias variáveis relevantes (água potável, internet, profissionais e materiais pedagógicos) só passam a ser coletadas pelo Censo a partir de 2019;
- 19,36% dos registros do Censo de 2007 a 2024 não têm nenhum atributo além da identificação, e nenhum deles aparece no IDEB;
- os três anos coincidem com as edições bienais do IDEB, o que permite o cruzamento direto sem interpolação.

A base integrada tem como chave `id_escola + ano + anos_escolares` e reúne apenas escolas com desempenho observado no IDEB. A caracterização completa das fontes e a justificativa do recorte estão em [Caracterização dos dados — 2019, 2021 e 2023](docs/caracterizacao_2019+.md).

## Situação atual

| Etapa | Situação | Documento |
| --- | --- | --- |
| Atividade 01 — Escolha e caracterização dos dados | Concluída | [docs/atividade-01-dados.md](docs/atividade-01-dados.md) |
| Atividade 02 — Pipeline de preparação e integração | Concluída | [docs/atividade-02-pipeline.md](docs/atividade-02-pipeline.md) |
| Arquitetura do sistema (dados, banco, API e painel) | Próximo passo | — |
| Modelos de anomalias, padrões e prioridades | Próximo passo | — |

Pontos de atenção que orientam as próximas etapas:

- cerca de 23% de valores ausentes em variáveis de infraestrutura, tecnologia e profissionais, que precisam ser entendidos antes de qualquer remoção ou imputação;
- códigos especiais do Inep (88888 e 9) que são convertidos em ausência pelo pipeline;
- associação não é causa: ano, UF, rede, localização, etapa e porte da escola afetam ao mesmo tempo a infraestrutura e o IDEB.

## Organização do repositório

| Item | Conteúdo |
| --- | --- |
| [data](data/) | Consultas SQL, arquivos CSV de origem e resultados processados. Consulte o [README de dados](data/README.md) para conhecer as bases disponíveis. |
| [docs](docs/) | Documentos entregáveis, caracterização das fontes e registros das atividades do projeto. |
| [notebooks](notebooks/) | Notebooks de análise exploratória e investigação dos dados. |
| [pipelines](pipelines/) | Rotinas de processamento, testes automatizados e suas instruções de execução. |
| [requirements.txt](requirements.txt) | Dependências Python necessárias para executar o código do projeto. |

## Requisitos

| Requisito | Versão ou condição | Finalidade |
| --- | --- | --- |
| Python | 3.10 ou superior | Executar o processamento e os testes automatizados. |
| `pip` | Compatível com a versão instalada do Python | Instalar as dependências declaradas em `requirements.txt`. |
| Pandas | 2.0 ou superior e inferior a 4.0 | Ler, validar, transformar e integrar os dados tabulares. |
| Ambiente virtual | Recomendado | Isolar as dependências do projeto das demais instalações do sistema. |
| Jupyter Notebook ou editor compatível | Opcional | Abrir e executar os arquivos da pasta `notebooks/`. |

Os arquivos CSV necessários para o processamento já estão organizados na pasta `data/`. O acesso ao Google BigQuery não é necessário para trabalhar com os dados existentes; ele é necessário apenas caso se deseje executar novamente as consultas SQL de extração.

As dependências obrigatórias são instaladas a partir de `requirements.txt`. As instruções de preparação do ambiente, execução do código e testes estão em [pipelines/README.md](pipelines/README.md).

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
