# Atividade 01 — Dados

## 1. Dados escolhidos

Os dados utilizados no projeto foram obtidos por meio da plataforma **Base dos Dados**, utilizando consultas SQL executadas no **Google BigQuery**. Foram utilizadas informações provenientes do **Censo Escolar da Educação Básica** e do **Índice de Desenvolvimento da Educação Básica (IDEB)**, produzidos pelo Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (Inep).

No Censo Escolar, foram selecionados os registros das escolas dos nove estados da Região Nordeste: Alagoas, Bahia, Ceará, Maranhão, Paraíba, Pernambuco, Piauí, Rio Grande do Norte e Sergipe. A consulta contempla atributos relacionados à identificação da escola, localização, dependência administrativa, infraestrutura física, recursos tecnológicos, materiais pedagógicos, profissionais e características das matrículas.

Para o IDEB, também foram selecionadas as escolas do Nordeste, mantendo apenas os registros com valor não nulo para o indicador. Os resultados das consultas foram exportados em arquivos CSV e são integrados utilizando o identificador da escola e o ano como principais chaves de relacionamento.

As consultas utilizadas estão disponíveis no repositório:

- [censo_educacional_nordeste_query.sql](../data/censo_educacional_nordeste_query.sql)
- [ideb_nordeste_sem_nulos_query.sql](../data/ideb_nordeste_sem_nulos_query.sql)

## 2. Caracterização da fonte

A caracterização da fonte tem como objetivo apresentar a origem, a estrutura e as principais características dos dados utilizados no projeto. Nesta etapa, são descritos aspectos como forma de obtenção, formato dos arquivos, dimensão das bases, período de cobertura e organização das informações. Essa descrição é importante para compreender o contexto dos dados e avaliar sua adequação ao problema proposto e ao cruzamento entre o Censo Escolar e o IDEB.

### Tabela Censo Escolar

**Origem:** Inep, disponibilizado de forma tratada pela Base dos Dados.  
**Forma de obtenção:** consulta SQL no Google BigQuery.  
**Formato:** arquivo CSV tabular.  
**Dimensão:** **1.557.932 linhas × 50 atributos**.  
**Período:** 2007 a 2024, com um registro por escola e ano.

#### Distribuição temporal

| Faixa temporal | Total de registros |
| --- | ---: |
| 2007–2012 | 521.405 |
| 2013–2018 | 558.486 |
| 2019–2024 | 478.041 |
| **Total** | **1.557.932** |

#### Por estado

| Estado | Registros |
| --- | ---: |
| BA | 420.295 |
| MA | 262.838 |
| CE | 207.791 |
| PE | 207.476 |
| PI | 133.117 |
| PB | 119.954 |
| RN | 93.102 |
| AL | 65.617 |
| SE | 47.742 |
| **Total** | **1.557.932** |

#### Rede administrativa

| Rede | Registros |
| --- | ---: |
| Municipal | **1.171.722** |
| Privada | 242.138 |
| Estadual | 140.710 |
| Federal | 3.362 |
| **Total** | **1.557.932** |

#### Localização

| Localização | Registros |
| --- | ---: |
| Rural | **884.289** |
| Urbana | 673.643 |
| **Total** | **1.557.932** |

### Tabela IDEB

**Origem:** Inep, disponibilizado de forma tratada pela Base dos Dados.  
**Forma de obtenção:** consulta SQL no Google BigQuery.  
**Formato:** arquivo CSV tabular.  
**Dimensão:** **54.997 linhas × 14 atributos**.  
**Período:** edições bienais de 2005 a 2025, com um registro por escola, ano e etapa de ensino.

#### Distribuição temporal

| Ano | Registros |
| --- | ---: |
| 2005 | 3.778 |
| 2007 | 4.243 |
| 2009 | 5.487 |
| 2011 | 5.035 |
| 2013 | 4.736 |
| 2015 | 4.531 |
| 2017 | 5.403 |
| 2019 | 5.718 |
| 2021 | 4.370 |
| 2023 | 5.711 |
| 2025 | 5.985 |
| **Total** | **54.997** |

#### Por estado

| Estado | Registros |
| --- | ---: |
| BA | 12.906 |
| CE | 9.119 |
| MA | 8.197 |
| PE | 7.631 |
| PB | 4.191 |
| PI | 4.117 |
| AL | 3.275 |
| RN | 3.185 |
| SE | 2.376 |
| **Total** | **54.997** |

#### Etapa de ensino

| `anos_escolares` | `ensino` | Registros | IDEB médio |
| --- | --- | ---: | ---: |
| iniciais (1-5) | fundamental | 29.366 | 4,33 |
| finais (6-9) | fundamental | 21.976 | 3,66 |
| todos (1-4) | médio | 3.655 | 4,03 |

A etapa `todos (1-4)` corresponde ao **ensino médio** e só aparece a partir de 2017.

## 3. Avaliação inicial de qualidade

A avaliação inicial da qualidade dos dados tem como objetivo identificar possíveis limitações que possam comprometer as etapas posteriores de análise e modelagem. Para isso, foram verificadas características como presença de valores ausentes, duplicidades, códigos especiais, consistência das chaves de identificação e disponibilidade das variáveis ao longo do tempo. Essa etapa é especialmente importante neste projeto, pois os dados do Censo Escolar abrangem vários anos e algumas variáveis foram incorporadas à base apenas em períodos mais recentes, o que exige cuidado para diferenciar ausência de informação de ausência real de determinada característica.

### 3.1 Investigando duplicidades

#### Censo Escolar

| Verificação | Critério | Quantidade |
| --- | --- | ---: |
| Linhas completamente duplicadas | Todas as colunas possuem os mesmos valores | **0** |
| Duplicidades por escola e ano | Combinação `ano + id_escola` repetida | **0** |

Não há registros duplicados no Censo Escolar: cada escola aparece uma única vez em cada ano.

#### IDEB

| Verificação | Critério | Quantidade |
| --- | --- | ---: |
| Linhas completamente duplicadas | Todas as colunas possuem os mesmos valores | **0** |
| Repetições por escola e ano | Combinação `ano + id_escola` | **2.497** |
| Duplicidades considerando a etapa | Combinação `ano + id_escola + anos_escolares` | **0** |

As repetições encontradas **não são registros duplicados**. Elas ocorrem porque uma mesma escola pode ter resultado do IDEB para mais de uma etapa de ensino no mesmo ano. Ao incluir `anos_escolares` na chave, nenhuma duplicidade é encontrada.

### 3.2 Ausência de dados

#### Censo Escolar

Os maiores percentuais de valores ausentes são:

| Campo | % ausente |
| --- | ---: |
| `tipo_situacao_funcionamento` | **100,00%** |
| `quantidade_matricula_utiliza_transporte_publico` | **92,31%** |
| `laboratorio_educacao_profissional` | **88,35%** |
| `profissional_assistente_social` | **80,46%** |
| `agua_potavel`, `desktop_aluno`, `internet_alunos`, `quantidade_sala_utilizada_climatizada` | **76,42%** |
| `quantidade_profissional_saude`, `_nutricionista`, `_psicologo`, `_pedagogia` | **76,42%** |
| `material_pedagogico_multimidia`, `_infantil`, `_cientifico`, `_musical`, `_artistica` | **76,42%** |
| `orgao_gremio_estudantil` | **76,42%** |
| `area_verde`, `banheiro_chuveiro`, `dormitorio_aluno`, `refeitorio` | **45,23%** |
| `biblioteca`, `sala_leitura` | **29,95%** |
| Matrículas (sexo e cor/raça), `diurno`, `noturno` | **20,36%** |
| `agua_rede_publica`, `energia_rede_publica`, `esgoto_rede_publica`, `lixo_servico_coleta`, `alimentacao` | **19,81%** |
| `cozinha`, `laboratorio_ciencias`, `laboratorio_informatica`, `quadra_esportes` | **19,36%** |

À primeira vista, isso parece um problema grave de qualidade. Uma análise mais detalhada, porém, mostra que a ausência tem **duas causas diferentes**, descritas a seguir.

#### Registros sem nenhum atributo preenchido

**301.548 registros (19,36% da base)** não possuem nenhum atributo de infraestrutura, recursos, profissionais ou matrículas preenchido: apenas as colunas de identificação (ano, estado, município, escola, rede e localização). É por isso que até as variáveis mais básicas, como `cozinha` e `quadra_esportes`, têm 19,36% de ausência.

| Período | Registros vazios por ano | % do ano |
| --- | ---: | ---: |
| 2007–2010 | 0 | 0,00% |
| 2011–2018 | 21.497 a 27.046 | 22,09% a 29,59% |
| 2019 | 22.152 | 26,06% |
| 2021 | 17.873 | 22,61% |
| 2023 | 15.968 | 20,91% |
| 2024 | 14.595 | 19,45% |

Nenhum desses registros aparece no IDEB. Como `tipo_situacao_funcionamento` está totalmente nulo na extração, não é possível confirmar pela base atual, mas o padrão é compatível com escolas paralisadas ou extintas, que continuam cadastradas no Censo sem informar dados do ano.

#### Mudança de esquema ao longo do tempo

Descontados os registros vazios, a ausência restante é explicada quase inteiramente pelo ano em que cada variável passou a ser coletada.

| Variável / grupo | Primeiro ano com dados |
| --- | --- |
| rede, localização, água, energia, esgoto, lixo, cozinha, alimentação, laboratórios de ciências e informática, quadra, turnos e matrículas | **2007** |
| biblioteca e sala de leitura | **2009** |
| área verde, banheiro com chuveiro, dormitório e refeitório | **2012** |
| água potável | **2019** |
| salas climatizadas | **2019** |
| desktop para aluno e internet para alunos | **2019** |
| profissionais de saúde, nutricionista, psicólogo e pedagogia | **2019** |
| materiais pedagógicos (multimídia, infantil, científico, musical e artístico) | **2019** |
| grêmio estudantil | **2019** |
| assistente social | **2020** |
| laboratório de educação profissional | **2022** |
| transporte público dos alunos | **2023** |
| `tipo_situacao_funcionamento` | nenhum ano |

Considerando apenas **2019–2024** e excluindo os registros vazios (**367.330 registros**), praticamente todas as variáveis ficam completas:

| Campo | % ausente em 2019–2024, sem registros vazios |
| --- | ---: |
| `tipo_situacao_funcionamento` | 100,00% |
| `quantidade_matricula_utiliza_transporte_publico` | 67,40% |
| `laboratorio_educacao_profissional` | 50,60% |
| `profissional_assistente_social` | 17,11% |
| Matrículas (sexo e cor/raça), `diurno`, `noturno` | 0,83% |
| Demais variáveis | 0,00% |

Os três percentuais restantes também são efeito de esquema: essas variáveis ainda não existiam em parte dos anos do intervalo. Isso confirma que a alta ausência representa uma **mudança do esquema do Censo Escolar ao longo do tempo**, somada aos registros sem informação, e não falha de preenchimento das variáveis.

#### IDEB

| Campo | % ausente |
| --- | ---: |
| `projecao` | **40,19%** |
| `id_escola_nome` | **1,79%** |
| Demais campos | **0,00%** |

As variáveis de desempenho (`taxa_aprovacao`, `indicador_rendimento`, `nota_saeb_media_padronizada` e `ideb`) estão completas.

### 3.3 Valores especiais

#### Código 88888 nas quantidades de profissionais

Algumas colunas de quantidade apresentam o valor **88888**, que não é uma quantidade real, e sim um código especial do Inep. Todas as ocorrências de valores acima de 1.000 nessas colunas são esse código.

| Variável | Ocorrências |
| --- | ---: |
| `quantidade_profissional_saude` | 447 |
| `quantidade_profissional_nutricionista` | 27 |
| `quantidade_profissional_psicologo` | 67 |
| `quantidade_profissional_pedagogia` | **1.048** |

O código aparece em todos os anos de 2019 a 2024. No notebook, ele é substituído por valor ausente antes das análises, pois mantê-lo distorceria médias e correlações.

#### Código 9 em variáveis binárias

Variáveis que deveriam assumir apenas 0 ou 1 também apresentam o valor **9**, fora do domínio esperado. Todas as ocorrências estão em **2019**.

| Variável | Ocorrências |
| --- | ---: |
| `orgao_gremio_estudantil` | 2.168 |
| `material_pedagogico_multimidia` | 9.526 |
| `material_pedagogico_infantil` | 9.526 |
| `material_pedagogico_cientifico` | 9.526 |
| `material_pedagogico_musical` | 9.526 |
| `material_pedagogico_artistica` | 9.526 |

Esse valor deve ser tratado como "não informado", e não como presença do recurso. Caso contrário, qualquer média calculada sobre essas colunas em 2019 fica inflada.

#### Valores extremos do IDEB

O IDEB varia de 0,2 a 10,0 (média 4,04 e mediana 3,90). Há 162 registros com IDEB igual ou superior a 9, em geral com taxa de aprovação de 100% e nota padronizada próxima de 9. Não são erros de formato, mas são valores atípicos que merecem verificação antes da modelagem.

## 4. Dicionário mínimo

A separação dos campos em grupos foi feita para facilitar a organização e a interpretação dos dados. Assim, variáveis de **identificação e controle** ajudam a localizar e diferenciar as escolas; variáveis de **infraestrutura** representam as condições físicas e de serviços disponíveis; variáveis de **recursos pedagógicos e tecnológicos** descrevem os meios oferecidos para apoio ao ensino; variáveis de **recursos humanos** indicam a presença de profissionais especializados; e variáveis relacionadas às **matrículas** ajudam a caracterizar o perfil e o porte das escolas. Essa divisão também facilita etapas posteriores de seleção de atributos, análise exploratória e modelagem.

### Identificação e controle

| Campo | Significado | Tipo | Observação |
| --- | --- | --- | --- |
| `ano` | Ano de referência | inteiro | chave temporal |
| `sigla_uf` | Estado | categórico | variável de controle |
| `id_municipio` | Município | código | não tratar como número contínuo |
| `id_escola` | Escola | código | chave de junção |
| `rede` | Dependência administrativa | categórico | municipal, estadual, federal ou privada |
| `tipo_localizacao` | Urbana/rural | categórico | importante variável explicativa |
| `tipo_situacao_funcionamento` | Situação de funcionamento | categórico | totalmente nulo na extração atual |
| `anos_escolares` | Etapa do IDEB | categórico | vem da base IDEB; `todos (1-4)` = ensino médio |

### Infraestrutura básica

Os valores dos campos abaixo são 0 ou 1, sendo 1 para possuindo e 0 para não possuindo.

| Campo | Significado |
| --- | --- |
| `agua_potavel` | Escola possui água potável |
| `agua_rede_publica` | Água proveniente da rede pública |
| `energia_rede_publica` | Energia elétrica de rede pública |
| `esgoto_rede_publica` | Ligação à rede pública de esgoto |
| `lixo_servico_coleta` | Serviço de coleta de lixo |
| `cozinha` | Existência de cozinha |
| `refeitorio` | Existência de refeitório |
| `banheiro_chuveiro` | Existência de banheiro com chuveiro |
| `dormitorio_aluno` | Existência de dormitório para alunos |
| `area_verde` | Existência de área verde |
| `alimentacao` | Oferta de alimentação escolar |

### Infraestrutura pedagógica e tecnológica

Os valores dos campos abaixo são 0 ou 1, sendo 1 para possuindo e 0 para não possuindo, exceto quando indicado.

| Campo | Significado |
| --- | --- |
| `biblioteca` | Existência de biblioteca |
| `sala_leitura` | Existência de sala de leitura |
| `laboratorio_ciencias` | Laboratório de ciências |
| `laboratorio_informatica` | Laboratório de informática |
| `laboratorio_educacao_profissional` | Laboratório de educação profissional |
| `quadra_esportes` | Quadra de esportes |
| `desktop_aluno` | Disponibilidade de desktop para aluno |
| `internet_alunos` | Internet disponível aos alunos |
| `material_pedagogico_multimidia`, `_infantil`, `_cientifico`, `_musical`, `_artistica` | Disponibilidade de materiais pedagógicos (0, 1 ou 9 = não informado em 2019) |
| `orgao_gremio_estudantil` | Existência de grêmio estudantil (0, 1 ou 9 = não informado em 2019) |
| `quantidade_sala_utilizada_climatizada` | **Quantidade** de salas climatizadas utilizadas (inteiro, de 0 a 230) |

### Recursos humanos

| Campo | Significado | Tipo |
| --- | --- | --- |
| `quantidade_profissional_saude` | Quantidade de profissionais de saúde | inteiro (88888 = código especial) |
| `quantidade_profissional_nutricionista` | Quantidade de nutricionistas | inteiro (88888 = código especial) |
| `quantidade_profissional_psicologo` | Quantidade de psicólogos | inteiro (88888 = código especial) |
| `quantidade_profissional_pedagogia` | Quantidade de profissionais de pedagogia | inteiro (88888 = código especial) |
| `profissional_assistente_social` | Presença de assistente social | binário (0 ou 1) |

### Matrículas e turnos

| Campo | Significado | Tipo |
| --- | --- | --- |
| `quantidade_matricula_feminino`, `_masculino`, `_nao_declarada` | Matrículas por sexo | inteiro |
| `quantidade_matricula_branca`, `_preta`, `_parda`, `_amarela`, `_indigena` | Matrículas por cor/raça | inteiro |
| `quantidade_matricula_utiliza_transporte_publico` | Matrículas que utilizam transporte público | inteiro |
| `diurno`, `noturno` | Funcionamento nos turnos diurno e noturno | binário (0 ou 1) |

### Desempenho (IDEB)

| Campo | Significado | Tipo |
| --- | --- | --- |
| `ensino` | Nível de ensino (fundamental ou médio) | categórico |
| `taxa_aprovacao` | Taxa de aprovação da etapa (%) | decimal |
| `indicador_rendimento` | Indicador de rendimento (fluxo) | decimal entre 0 e 1 |
| `nota_saeb_media_padronizada` | Nota média padronizada no Saeb | decimal |
| `ideb` | Índice de Desenvolvimento da Educação Básica | decimal entre 0 e 10 |
| `projecao` | Meta projetada para a escola | decimal (40,19% ausente) |

## 5. Cruzamento Tabela Censo × Tabela IDEB

A base do Censo cobre **2007–2024**, enquanto o IDEB possui dados nos anos:

2005, 2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021, 2023 e 2025

Os anos comuns são, portanto:

2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021 e 2023

São **9 edições do IDEB** disponíveis para integração.

### Resultado do cruzamento

O relacionamento foi feito por `ano + id_escola`.

O uso dessa chave funciona porque no Censo existe somente uma linha para cada escola em cada ano. Já no IDEB podem existir diferentes etapas para a mesma escola, então cada linha do Censo pode corresponder a mais de uma linha do IDEB (relação muitos-para-um).

#### Correspondência por ano

| Ano | Registros IDEB | Escolas distintas | Registros encontrados no Censo |
| --- | ---: | ---: | --- |
| 2007 | 4.243 | 4.000 | **4.243 — 100%** |
| 2009 | 5.487 | 5.233 | **5.487 — 100%** |
| 2011 | 5.035 | 4.811 | **5.035 — 100%** |
| 2013 | 4.736 | 4.519 | **4.736 — 100%** |
| 2015 | 4.531 | 4.329 | **4.531 — 100%** |
| 2017 | 5.403 | 5.187 | **5.403 — 100%** |
| 2019 | 5.718 | 5.453 | **5.718 — 100%** |
| 2021 | 4.370 | 4.210 | **4.370 — 100%** |
| 2023 | 5.711 | 5.454 | **5.711 — 100%** |
| **Total** | **45.234** | **43.196 escola-ano** | **45.234 — 100%** |

Todas as 45.234 observações de IDEB nos anos comuns foram encontradas no Censo, correspondendo a 43.196 combinações únicas de escola e ano. Nenhuma delas corresponde a um registro vazio do Censo.

Após o cruzamento, o IDEB médio por rede é de 5,52 na rede privada (51 registros), 5,24 na federal (58), 4,13 na municipal (35.397) e 3,58 na estadual (9.728). A baixa quantidade de escolas privadas e federais indica que o IDEB por escola cobre principalmente a rede pública.

Para o projeto vamos priorizar os dados mais recentes, de 2019 em diante, já que a partir desse ano a maioria das colunas já é coletada e, excluídos os registros vazios, quase não apresenta valores nulos.

## 6. Amostra utilizada

Para as primeiras aplicações do projeto, foi definido um recorte temporal composto pelos anos de **2019, 2021 e 2023**. A escolha desses anos foi feita com base na disponibilidade e na completude das variáveis do Censo Escolar, uma vez que diversos atributos relevantes para a análise, especialmente relacionados à infraestrutura, recursos tecnológicos, materiais pedagógicos e profissionais da escola, passam a ser coletados a partir de 2019.

Além disso, esses três anos podem ser diretamente relacionados aos dados do IDEB, que possui periodicidade bienal. Dessa forma, 2019, 2021 e 2023 formam um conjunto temporal consistente entre as duas fontes, permitindo o cruzamento por `ano` e `id_escola` sem a necessidade de interpolação ou associação entre anos distintos.

Esse recorte busca equilibrar **qualidade dos dados, disponibilidade das variáveis e compatibilidade entre as fontes**, permitindo que as primeiras análises sejam realizadas sobre uma amostra mais completa e comparável. Em etapas posteriores, caso seja necessário ampliar a análise histórica, poderão ser incorporados anos anteriores com um conjunto reduzido de atributos que apresentem cobertura adequada ao longo do tempo.

A caracterização detalhada desse recorte está em [caracterizacao_2019+.md](caracterizacao_2019+.md).

## 7. Síntese técnica

**1. Disponibilidade dos dados.**

Os dados necessários para o projeto estão disponíveis e apresentam elevada compatibilidade para integração. O Censo Escolar contém 1.557.932 registros de escolas nordestinas entre 2007 e 2024, enquanto o arquivo do IDEB possui 54.997 observações entre 2005 e 2025. Considerando os anos existentes simultaneamente nas duas fontes, é possível realizar o cruzamento para 2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021 e 2023. Foram obtidas 45.234 observações de IDEB nesses anos e todas encontraram correspondência no Censo Escolar por meio das variáveis `ano` e `id_escola`.

**2. Principal problema identificado.**

O principal problema identificado é a mudança na disponibilidade das variáveis do Censo Escolar ao longo do tempo. Embora algumas características estejam disponíveis desde 2007, outras aparecem somente a partir de 2009, 2012, 2019, 2020, 2022 ou 2023. Além disso, 19,36% dos registros do Censo não possuem nenhum atributo preenchido além da identificação. Dessa forma, o elevado percentual de valores ausentes não representa falha no preenchimento das variáveis, e sim a combinação de alterações no esquema do Censo com registros de escolas sem informação no ano.

**3. Informações indisponíveis.**

Algumas informações relevantes não estão disponíveis durante todo o período analisado. Variáveis relacionadas a profissionais de saúde, psicologia, nutrição e pedagogia, água potável, salas climatizadas, acesso à internet e desktop pelos alunos, materiais pedagógicos e grêmio estudantil aparecem somente a partir de 2019. A variável de assistente social aparece a partir de 2020, o laboratório de educação profissional a partir de 2022 e a utilização de transporte público pelos estudantes somente a partir de 2023. Além disso, `tipo_situacao_funcionamento` encontra-se totalmente ausente na extração atual, o que impede confirmar se os registros vazios são de escolas paralisadas ou extintas. Há ainda códigos especiais que precisam ser tratados como ausência: 88888 nas quantidades de profissionais e 9 nas variáveis de materiais pedagógicos e grêmio estudantil em 2019.

**4. Alteração no escopo.**

A análise dos dados não inviabiliza o problema proposto, mas levou à definição de um recorte temporal mais específico para as primeiras aplicações do projeto. Foram selecionados os anos de **2019, 2021 e 2023**, por apresentarem maior completude das variáveis do Censo Escolar e, ao mesmo tempo, coincidirem com os anos de divulgação do IDEB, que possui periodicidade bienal.

Com essa delimitação, torna-se possível utilizar um conjunto mais amplo e detalhado de atributos, incluindo informações sobre infraestrutura, acesso à internet, profissionais especializados, materiais pedagógicos e características das matrículas, mantendo compatibilidade direta entre as duas fontes. Assim, o escopo inicial do projeto passa a priorizar uma análise mais recente e com maior riqueza de variáveis, deixando a ampliação para anos anteriores como uma possibilidade futura, caso seja necessário trabalhar com um conjunto mais reduzido e historicamente consistente de atributos.

**5. Principal risco.**

O principal risco relacionado aos dados é combinar períodos com estruturas de informação diferentes ou interpretar valores ausentes e códigos especiais como ausência ou presença da característica analisada. Também existe risco de confusão entre associação e causalidade, já que fatores como ano, estado, rede administrativa, localização da escola, etapa de ensino e tamanho da escola podem estar relacionados simultaneamente à infraestrutura disponível e ao desempenho no IDEB. Esses fatores deverão ser considerados nas etapas posteriores de análise e modelagem.
