### Tabela Censo Escolar

**Origem:** Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (Inep), disponibilizado de forma tratada pela Base dos Dados.  
**Forma de obtenção:** consulta SQL realizada no Google BigQuery.  
**Formato:** arquivo CSV tabular.  
**Dimensão:** **240.386 linhas × 50 atributos**.  
**Período considerado:** **2019, 2021 e 2023**.

A origem e o processo de obtenção seguem os mesmos utilizados anteriormente no projeto.

A única mudança além das escolha dos anos, foi a remoção da coluna tipo_situacao_funcinamento da tabela censo por ela ser completamente nula.

#### Distribuição temporal

| Ano | Total de registros |
| --- | ---: |
| 2019 | 84.999 |
| 2021 | 79.039 |
| 2023 | 76.348 |
| **Total** | **240.386** |

A distribuição apresenta redução gradual no número de registros entre os três anos, mas mantém volume elevado de observações em todo o recorte.

#### Por estado

| Estado | Registros |
| --- | ---: |
| BA | 62.248 |
| MA | 42.516 |
| CE | 32.680 |
| PE | 32.057 |
| PI | 19.423 |
| PB | 17.625 |
| RN | 15.629 |
| AL | 10.482 |
| SE | 7.726 |
| **Total** | **240.386** |

A Bahia concentra a maior quantidade de registros, seguida por Maranhão, Ceará e Pernambuco. Os nove estados da Região Nordeste permanecem representados na amostra.

#### Rede administrativa

| Rede | Registros |
| --- | ---: |
| Municipal | 174.439 |
| Privada | 43.272 |
| Estadual | 21.973 |
| Federal | 702 |
| **Total** | **240.386** |

Há predominância de escolas da **rede municipal**, que representam a maior parcela da base. As redes privada e estadual aparecem em seguida, enquanto a rede federal apresenta participação reduzida.

#### Localização

| Localização | Registros |
| --- | ---: |
| Rural | 124.191 |
| Urbana | 116.195 |
| **Total** | **240.386** |

A distribuição entre escolas urbanas e rurais é relativamente equilibrada, com uma quantidade ligeiramente maior de registros classificados como rurais.

---

### Tabela IDEB

**Origem:** Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (Inep), disponibilizado de forma tratada pela Base dos Dados.  
**Forma de obtenção:** consulta SQL realizada no Google BigQuery.  
**Formato:** arquivo CSV tabular.  
**Dimensão:** **79.374 linhas × 14 atributos**.  
**Período considerado:** **2019, 2021 e 2023**.

#### Distribuição temporal 

|Ano|Total de registros|
|---|---|
|2019|28.656|
|2021|21.910|
|2023|28.808|
|**Total**|**79.374**|

## 3. Avaliação Inicial de Qualidade

A avaliação inicial da qualidade dos dados tem como objetivo identificar possíveis limitações que possam comprometer as etapas posteriores de análise, integração e modelagem. Foram verificadas características como presença de valores ausentes, duplicidades, consistência das chaves de identificação e ocorrência de valores especiais.

Como as bases atuais já estão restritas aos anos de **2019, 2021 e 2023**, parte do problema anteriormente associado à mudança histórica do esquema do Censo Escolar foi reduzida. Entretanto, ainda existem variáveis com elevada ausência de dados, principalmente aquelas que passaram a ser coletadas depois de 2019.

### 3.1 Investigando duplicidades

#### Censo Escolar

| Verificação | Critério | Quantidade |
| --- | --- | ---: |
| Linhas completamente duplicadas | Todas as colunas possuem os mesmos valores | **0** |
| Duplicidades por escola e ano | Combinação `ano + id_escola` repetida | **0** |

Não foram identificadas duplicidades na base atualizada do Censo Escolar. Cada combinação de **ano e escola** aparece uma única vez. Como o Censo não contém `anos_escolares`, o pipeline associa a cada escola-ano as etapas únicas observadas no IDEB antes de efetuar o cruzamento final pela chave tripla.

#### IDEB

| Verificação | Critério | Quantidade |
| --- | --- | ---: |
| Linhas completamente duplicadas | Todas as colunas possuem os mesmos valores | **0** |
| Repetições por escola e ano | Combinação `ano + id_escola` | **17.049** |
| Duplicidades considerando a etapa | Combinação `ano + id_escola + anos_escolares` | **0** |

Assim como na análise anterior, as repetições encontradas no IDEB **não representam registros duplicados**. Elas ocorrem porque uma mesma escola pode possuir resultados para diferentes etapas de ensino em um mesmo ano.

Ao acrescentar a variável `anos_escolares` à chave, nenhuma duplicidade é encontrada.

---

## 3.2 Consistência das chaves

Também foi verificada a presença de valores ausentes nas variáveis utilizadas para identificar e relacionar os registros.

| Base | Campo | Valores ausentes |
| --- | --- | ---: |
| Censo | `ano` | **0** |
| Censo | `id_escola` | **0** |
| IDEB | `ano` | **0** |
| IDEB | `id_escola` | **0** |
| IDEB | `anos_escolares` | **0** |

Dessa forma, as principais chaves necessárias para o cruzamento estão completamente preenchidas.

Isso é especialmente importante porque a base final usa **`id_escola + ano + anos_escolares`** como chave. O Censo é inicialmente relacionado às etapas do IDEB por escola e ano apenas para compatibilizar a granularidade; em seguida, o cruzamento final entre as duas visões é executado e validado pelas três colunas.

---

## 3.3 Ausência de dados

Mesmo após restringir a análise aos anos mais recentes, algumas variáveis ainda apresentam percentuais elevados de valores ausentes.

Os maiores percentuais encontrados no **Censo Escolar** são:

| Campo | % ausente |
| --- | ---: |
| `quantidade_matricula_utiliza_transporte_publico` | **75,10%** |
| `laboratorio_educacao_profissional` | **74,88%** |
| `profissional_assistente_social` | **49,44%** |
| Variáveis relacionadas às matrículas e turnos | **23,92%** |
| Grande parte das variáveis de infraestrutura, tecnologia e profissionais | **23,29%** |

No caso das três primeiras variáveis, parte do elevado percentual pode ser explicada pelo período em que passaram a ser disponibilizadas. No levantamento anterior, o assistente social aparecia a partir de 2020, laboratório de educação profissional a partir de 2022 e transporte público dos alunos a partir de 2023.

### Disponibilidade nos anos selecionados

| Variável | 2019 | 2021 | 2023 |
| --- | --- | --- | --- |
| `profissional_assistente_social` | Ausente | Disponível | Disponível |
| `laboratorio_educacao_profissional` | Ausente | Ausente | Disponível |
| `quantidade_matricula_utiliza_transporte_publico` | Ausente | Ausente | Disponível |

Isso explica uma parte importante dos percentuais globais de ausência.

Por exemplo, `laboratorio_educacao_profissional` possui dados apenas em 2023 dentro da amostra selecionada. Portanto, seu percentual elevado de valores ausentes **não deve ser interpretado simplesmente como falha de preenchimento**.

O mesmo ocorre com a utilização de transporte público, disponível apenas no último ano do recorte.

---

### Valores ausentes nas demais variáveis

Um comportamento diferente é observado em diversas variáveis de infraestrutura, recursos tecnológicos, profissionais e materiais pedagógicos.

Apesar de estarem disponíveis nos três anos, elas apresentam aproximadamente:

- **26,06% de ausência em 2019**;
- **22,61% em 2021**;
- **20,91% em 2023**.

Quando os três anos são considerados conjuntamente, o percentual fica próximo de **23,29%**.

Entre essas variáveis encontram-se, por exemplo, `agua_potavel`, `biblioteca`, `laboratorio_informatica`, `internet_alunos`, `desktop_aluno`, `quantidade_profissional_psicologo`, `quantidade_profissional_nutricionista`, `area_verde`, `refeitorio` e materiais pedagógicos.

Nesse caso, como as variáveis existem nos três anos, **não é adequado atribuir automaticamente os valores nulos à mudança de esquema temporal**. Será necessário investigar nas próximas etapas quais características dos registros estão associadas a essas ausências antes de decidir por remoção, imputação ou outro tratamento.

Isso representa uma diferença importante em relação à primeira avaliação do projeto, na qual grande parte dos nulos era provocada por variáveis ainda inexistentes nos anos mais antigos. O documento original já apontava essa mudança de esquema como uma das principais causas de ausência.

---

### Ausência de dados no IDEB

A base do IDEB apresenta uma quantidade significativamente menor de valores ausentes.

| Campo | % ausente |
| --- | ---: |
| `projecao` | **41,87%** |
| `id_escola_nome` | **0,40%** |
| Demais campos | **0,00%** |

As principais variáveis utilizadas para análise de desempenho estão completamente preenchidas, incluindo:

`taxa_aprovacao`, `indicador_rendimento`, `nota_saeb_media_padronizada` e `ideb`.

Dessa forma, a ausência encontrada em `projecao` não inviabiliza a utilização dos resultados observados do IDEB.

---

## 3.4 Valores especiais

Na análise anterior foram encontradas ocorrências do valor **8888** em variáveis relacionadas à quantidade de profissionais.

Nas bases atualizadas de **2019, 2021 e 2023, não foram encontradas ocorrências do valor 8888**.

Isso elimina um dos problemas identificados anteriormente e evita a necessidade, nesse recorte, de tratar esse código antes das análises.

Também não foram encontrados valores negativos nas variáveis numéricas do Censo Escolar.
