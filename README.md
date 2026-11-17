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

| Funcionalidade | Descrição | Abordagem | Situação |
| --- | --- | --- | --- |
| Descoberta de padrões | Agrupa as escolas por perfil a partir dos próprios dados, sem grupos definidos de antemão, e revela características associadas aos resultados. | K-Means sobre índices de infraestrutura, espaços pedagógicos, tecnologia, materiais, profissionais, porte e etapas oferecidas: **6 grupos** | Primeira versão concluída |
| Detecção de anomalias | Sinaliza escolas que fogem do esperado para o seu grupo de pares, como desempenho destoante, quedas bruscas entre edições do IDEB ou combinações incomuns de características. | Primeira versão: escolas abaixo do percentil 10 e acima do percentil 90 do IDEB dentro de grupo × etapa × ano, exibidas no mapa. Previsto: escore robusto, evolução entre edições, Isolation Forest ou LOF | Em andamento |
| Prioridades de atenção | Combina desempenho, evolução, infraestrutura, tecnologia, recursos humanos e comparação com os pares em um nível de prioridade, sempre acompanhado dos motivos. | Indicadores por dimensão | Prevista |

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
| Atividade 03 — Descoberta de padrões (agrupamento) | Primeira versão concluída | [docs/atividade-03-agrupamento.md](docs/atividade-03-agrupamento.md), [docs/agrupamento-por-ano.md](docs/agrupamento-por-ano.md) e [docs/calculo-dos-destaques.md](docs/calculo-dos-destaques.md) |
| Mapa interativo (IDEB, grupos e destaque P10/P90) | Primeira versão concluída | [visualizacao/README.md](visualizacao/README.md) |
| Detecção de anomalias e prioridades | Em andamento | [docs/proximos_passos.md](docs/proximos_passos.md) |
| Arquitetura do sistema (dados, banco, API e painel) | Próximo passo | — |

### Resultados até aqui

O agrupamento (três anos juntos, 62.325 escolas-ano) encontrou seis perfis de escola, que se repetem quando cada ano é agrupado separadamente (96% a 98% das escolas no mesmo grupo):

| Grupo | Perfil | % das escolas-ano |
| --- | --- | --- |
| 0 | Recursos mínimos | 31% |
| 1 | Espaços sem tecnologia | 16% |
| 2 | Materiais sem tecnologia | 15% |
| 3 | Apoio multiprofissional | 7% |
| 4 | Tecnologia sem espaços | 17% |
| 5 | Estrutura completa | 15% |

O IDEB acompanha o nível de recursos (menor no grupo 0, maior no grupo 5), mas varia muito dentro de cada grupo. Essa variação entre escolas de perfil parecido é a base da detecção de anomalias.

Pontos de atenção que orientam as próximas etapas:

- **valores ausentes:** a maior parte é estrutural (variáveis que o Censo não coletou em todos os anos) e foi excluída da matriz do agrupamento; o restante (3,4% das escolas-ano) é imputado pelo pipeline 02, com indicadores das linhas imputadas;
- **códigos especiais do Inep** (88888 e 9) são convertidos em ausência pelo pipeline 01;
- **grupos como tipologia:** a silhueta é baixa (cerca de 0,14), ou seja, as escolas formam um contínuo; os grupos servem para definir pares comparáveis, não como tipos naturais de escola;
- **IDEB de 2021:** não é comparável com os outros anos por causa da aprovação quase universal durante a pandemia;
- **coordenadas:** 12,6% das escolas não têm latitude e longitude (sobretudo na Bahia e na zona rural) e não aparecem na camada de escolas do mapa;
- **associação não é causa:** ano, UF, rede, localização, etapa e porte da escola afetam ao mesmo tempo a infraestrutura e o IDEB.

## Organização do repositório

| Item | Conteúdo |
| --- | --- |
| [data](data/) | Consultas SQL, arquivos CSV de origem e resultados processados. Consulte o [README de dados](data/README.md) para conhecer as bases disponíveis. |
| [docs](docs/) | Documentos entregáveis, caracterização das fontes e registros das atividades do projeto. |
| [notebooks](notebooks/) | Notebooks de análise exploratória, investigação dos dados e interpretação do agrupamento. |
| [modelos](modelos/) | Modelos ajustados sobre a matriz de atributos, como o agrupamento das escolas por perfil. |
| [visualizacao](visualizacao/) | Preparação dos dados e página do mapa interativo de escolas e municípios (IDEB e grupos). |
| [pipelines](pipelines/) | Rotinas de processamento, testes automatizados e suas instruções de execução. |
| [requirements.txt](requirements.txt) | Dependências Python necessárias para executar o código do projeto. |

## Requisitos

| Requisito | Versão ou condição | Finalidade |
| --- | --- | --- |
| Python | 3.10 ou superior | Executar o processamento e os testes automatizados. |
| `pip` | Compatível com a versão instalada do Python | Instalar as dependências declaradas em `requirements.txt`. |
| Pandas | 2.0 ou superior e inferior a 4.0 | Ler, validar, transformar e integrar os dados tabulares. |
| scikit-learn | 1.5 ou superior e inferior a 2.0 | Padronizar os atributos e ajustar os modelos de agrupamento. |
| Ambiente virtual | Recomendado | Isolar as dependências do projeto das demais instalações do sistema. |
| Jupyter Notebook ou editor compatível | Opcional | Abrir e executar os arquivos da pasta `notebooks/`. |
| Navegador com acesso à internet | Opcional | Abrir o mapa interativo; o mapa de fundo e a biblioteca Leaflet são carregados da internet. |

Os arquivos CSV necessários para o processamento já estão organizados na pasta `data/`. O acesso ao Google BigQuery não é necessário para trabalhar com os dados existentes; ele é necessário apenas caso se deseje executar novamente as consultas SQL de extração.

As dependências obrigatórias são instaladas a partir de `requirements.txt`. As instruções de preparação do ambiente, execução do código e testes estão em [pipelines/README.md](pipelines/README.md).

## Como executar

A partir da raiz do repositório, com o ambiente virtual ativo:

```bash
python pipelines/pipeline_01.py               # Censo + IDEB → data/processed/base_integrada.csv
python pipelines/pipeline_02_atributos.py     # base integrada → matriz de atributos por escola-ano
python modelos/agrupamento.py                 # agrupamento conjunto → data/processed/agrupamento/
python modelos/agrupamento.py --ano 2023      # agrupamento de um único ano → data/processed/agrupamento/2023/
python visualizacao/preparar_dados_mapa.py    # tabelas e página visualizacao/mapa_municipios.html
python -m unittest discover -s pipelines/tests -v
```

Cada etapa usa os resultados da anterior, que já estão versionados em `data/processed/`; não é preciso executar tudo para abrir os notebooks ou o mapa.

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
       data/processed/ - resultados  <------+
                |                           |
        +-------+--------+---------+        |
        |                |         |        |
        v                v         v        |
   notebooks/        modelos/   visualizacao/
   análises          agrupamento   mapa interativo
        |                |         |
        +-------+--------+---------+
                |
                v
             docs/ - documentação
```

| Camada | Responsabilidade |
| --- | --- |
| Dados de origem | Armazenar as consultas de extração e os arquivos recebidos das fontes externas. |
| Processamento | Concentrar o código responsável por preparar e integrar os dados, junto aos testes automatizados correspondentes. |
| Dados processados | Manter os resultados produzidos pelo processamento separados das entradas originais. |
| Modelos | Ajustar os modelos sobre os dados processados (hoje, o agrupamento) e gravar os resultados em `data/processed/`. |
| Visualização | Combinar os resultados em páginas para consulta, como o mapa interativo de escolas e municípios. |
| Análise | Explorar os dados, avaliar sua qualidade e interpretar os resultados dos modelos. |
| Documentação | Registrar decisões, características das bases, evidências e entregas de cada atividade. |

Os componentes possuem documentação própria quando necessário. As bases são descritas em [data/README.md](data/README.md), as instruções para executar o código e os testes ficam em [pipelines/README.md](pipelines/README.md), e o mapa é descrito em [visualizacao/README.md](visualizacao/README.md).
