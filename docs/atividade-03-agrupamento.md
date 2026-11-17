# Atividade 03 - Descoberta de padrões: agrupamento das escolas por perfil

## 1 Objetivo

Agrupar as escolas do Nordeste por **perfil** (infraestrutura, tecnologia, materiais, profissionais, porte, composição das matrículas e etapas oferecidas), sem grupos definidos de antemão, e caracterizar os grupos pelo IDEB de cada etapa. Os grupos servem como **pares comparáveis** para a próxima funcionalidade, a detecção de anomalias.

O planejamento e a justificativa de cada decisão estão em [Próximos passos](proximos_passos.md). Este documento registra o que foi implementado e os resultados.

## 2 Fluxo

```text
pipeline_01.py  →  base_integrada.csv  →  pipeline_02_atributos.py  →  atributos_escola_ano.csv  →  modelos/agrupamento.py  →  agrupamento/
 (inalterado)        (79.374 linhas)                                    ligacao_etapas.csv                                       atribuicoes.csv
                                                                        relatorio_atributos.json                                 perfis_clusters.csv
                                                                                                                                 metricas.json
```

A interpretação, com gráficos, está no notebook [02_agrupamento.ipynb](../notebooks/02_agrupamento.ipynb).

## 3 Preparação dos atributos (`pipeline_02_atributos.py`)

| Etapa | Resultado na base atual |
| --- | --- |
| Validação | Atributos do Censo idênticos entre as etapas de todas as 16.916 escolas-ano com mais de uma etapa. O pipeline interrompe a execução se isso deixar de ser verdade. |
| Remoção da duplicação | 79.374 linhas → **62.325 escolas-ano**, com os indicadores `oferece_iniciais`, `oferece_finais` e `oferece_medio`. |
| Ausência estrutural | Excluídas `laboratorio_educacao_profissional`, `quantidade_matricula_utiliza_transporte_publico` e `profissional_assistente_social`. |
| Imputação — materiais pedagógicos | 2.102 escolas-ano: 1.817 pelo valor da própria escola em outro ano e 285 pela moda dos pares (`ano × rede × tipo_localizacao`). Indicador `materiais_imputados`. |
| Imputação — grêmio estudantil | 482 escolas-ano: 417 pela própria escola e 65 pela moda dos pares. Indicador `gremio_imputado`. |
| Imputação — profissionais | 38 escolas-ano: 30 pela própria escola e 8 pela mediana dos pares. Indicador `profissionais_imputados`. |
| Razões e proporções | Porte (`log1p` das matrículas), proporção feminina, proporções por raça/cor, pedagogos por 100 alunos (`log1p`) e salas climatizadas (`log1p`). |
| Profissionais raros | Saúde, nutricionista e psicólogo viram indicadores de presença (`tem_*`). A razão por aluno ficava inflada em escolas pequenas, já que um profissional compartilhado pela rede é registrado em cada escola. |
| Winsorização (p1–p99) | Aplicada às 10 variáveis contínuas; entre 536 e 1.248 linhas limitadas por coluna. |
| Quase constantes (≥ 98% com o mesmo valor) | Removidas `energia_rede_publica`, `cozinha`, `dormitorio_aluno`, `alimentacao`, `diurno` e `tem_profissional_saude`. |
| Índices por dimensão | `indice_infraestrutura_basica`, `indice_espacos_pedagogicos`, `indice_tecnologia` e `indice_materiais` (proporção dos itens presentes). |

Em relação ao planejamento, a imputação dos profissionais também passou a usar primeiro o valor da própria escola em outro ano, como nas variáveis binárias, e só depois a mediana dos pares.

## 4 Modelagem (`modelos/agrupamento.py`)

| Aspecto | Escolha |
| --- | --- |
| Atributos | Conjunto `indices`: 21 atributos (os 4 índices no lugar das binárias que eles resumem, mais as demais variáveis). |
| Escala | `StandardScaler` ajustado com os três anos juntos. |
| Ponderação | Cada coluna multiplicada por 1/√(número de colunas da sua dimensão). |
| Redução | PCA com 90% da variância: 13 componentes. |
| Algoritmo | K-Means com k = 6 (`n_init = 10`, semente fixa). Grupos numerados em ordem crescente do índice de tecnologia. |

### 4.1 Escolha de k

| k | Silhueta | Davies-Bouldin | Calinski-Harabasz | Menor grupo |
| --- | --- | --- | --- | --- |
| 2 | 0,213 | 1,84 | 17.148 | 24.295 |
| 3 | 0,136 | 2,34 | 11.615 | 17.039 |
| 4 | 0,132 | 2,22 | 9.863 | 10.464 |
| 5 | 0,137 | 2,04 | 8.894 | 4.421 |
| **6** | **0,140** | **1,87** | 8.286 | 4.298 |
| 7 | 0,124 | 2,04 | 7.482 | 4.228 |
| 8 | 0,122 | 1,98 | 6.910 | 4.197 |

A silhueta é baixa em todos os valores de k: as escolas **não formam grupos naturalmente separados**, e os perfis variam de forma contínua. Os grupos devem ser lidos como uma **tipologia** útil para definir pares, e não como tipos naturais. O k = 2 só separa escolas com mais e com menos recursos. Entre k = 3 e 8, o k = 6 tem a maior silhueta, o menor Davies-Bouldin e grupos interpretáveis.

A comparação entre os conjuntos de atributos (avaliação exploratória feita antes da troca dos profissionais por presença, k de 2 a 8) favoreceu índices com ponderação: silhueta de 0,13 a 0,21, contra 0,07 a 0,14 nas demais combinações.

### 4.2 Estabilidade e robustez

| Verificação | ARI | Leitura |
| --- | --- | --- |
| Sementes diferentes | 0,998 a 0,999 | Partição praticamente idêntica. |
| Reamostragens (bootstrap) | 0,979 a 0,985 | Não depende da amostra. |
| Modelos ajustados em anos diferentes | 0,85 (2019→2023); 0,61 (2019→2021); 0,54 (2021→2023) | Os anos de 2019 e 2023 produzem grupos parecidos. Os pares com 2021 são menos estáveis porque a presença de profissionais oscilou: nutricionistas em 21% das escolas em 2019, 13% em 2021 e 16% em 2023; psicólogos em 8%, 5% e 11%. A tipologia final é ajustada com os três anos juntos, o que aplica a mesma régua a todas as escolas. |
| `StandardScaler` × `RobustScaler` | 0,52 | Sensibilidade moderada, causada sobretudo pelas binárias com menos de 25% de valores 1, que o `RobustScaler` deixa sem reescalar (intervalo interquartil zero). |
| K-Means × Ward (amostra de 10.000) | 0,32 | Algoritmos diferentes particionam o contínuo de formas diferentes. |
| HDBSCAN (amostra de 10.000) | — | Só 2 regiões densas, separadas basicamente pela presença de psicólogo; o restante do espaço não tem fronteiras naturais. |

## 5 Resultados

| Grupo | Nome proposto | Escolas-ano | Perfil | IDEB mediano (iniciais / finais / médio) |
| --- | --- | --- | --- | --- |
| 0 | Recursos mínimos | 19.488 (31%) | Pequenas (mediana de 191 matrículas), 93% municipais, 60% rurais; os menores índices de espaços, tecnologia e materiais. | 4,8 / 4,0 / 3,4 |
| 1 | Espaços sem tecnologia | 9.850 (16%) | Maiores e urbanas; biblioteca, sala de leitura e quadra, mas pouca tecnologia e poucos materiais. | 5,2 / 4,4 / 3,8 |
| 2 | Materiais sem tecnologia | 9.080 (15%) | Municipais, com o maior índice de materiais pedagógicos e pouca tecnologia. | 5,2 / 4,5 / 3,8 |
| 3 | Apoio multiprofissional | 4.298 (7%) | Todas com psicólogo e 78% com nutricionista; nas demais dimensões, próximas da média. 98% municipais; o grupo cresce em 2023. | 5,0 / 4,3 / 4,0 |
| 4 | Tecnologia sem espaços | 10.499 (17%) | Computadores e internet para os alunos, mas poucos espaços pedagógicos e materiais. | 5,1 / 4,5 / 3,9 |
| 5 | Estrutura completa | 9.110 (15%) | Maiores, 91% urbanas, 63% estaduais; os maiores índices em todas as dimensões, grêmio e ensino médio. | 5,4 / 4,7 / 4,3 |

Principais leituras:

- O IDEB acompanha o nível de recursos: o grupo 0 tem as menores medianas em todas as etapas, e o grupo 5 as maiores. Os grupos 1 a 4 têm IDEB parecido, apesar de perfis diferentes.
- **Associação não é causa:** os grupos também diferem em rede, localização e porte, que afetam ao mesmo tempo a infraestrutura e o IDEB.
- A dispersão do IDEB **dentro** de cada grupo é grande. Essa dispersão é a base da detecção de anomalias.
- Os três anos se distribuem de forma equilibrada entre os grupos, e as escolas com materiais imputados representam no máximo 6% de um grupo (grupo 0).

## 6 Limitações e pontos em aberto

- **Apoio multiprofissional:** a presença de psicólogo é rara (8% das escolas) e, depois da padronização, pesa o suficiente para formar um grupo próprio. Isso pode refletir um perfil real, como redes que contratam psicólogos e nutricionistas, mas também deixa esse grupo menos estável entre os anos.
- **Contexto fora do agrupamento:** `rede`, `tipo_localizacao` e UF não entram como atributos. Os grupos já se diferenciam por eles (por exemplo, 63% de escolas estaduais no grupo 5), mas sem que o modelo seja forçado a separá-los.
- **Nomes dos grupos:** são uma proposta e devem ser revistos com conhecimento do domínio.

## 7 Como executar

A partir da raiz do repositório:

```bash
python pipelines/pipeline_02_atributos.py
python modelos/agrupamento.py
python -m unittest discover -s pipelines/tests -v
```

O agrupamento leva alguns minutos. Depois, abra o notebook `notebooks/02_agrupamento.ipynb`.
