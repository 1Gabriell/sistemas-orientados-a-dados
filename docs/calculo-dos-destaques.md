# Cálculo dos destaques dos grupos

Este documento explica como são calculados os "destaques" usados para descrever os grupos do agrupamento, como na tabela abaixo, retirada de [Agrupamento separado por ano](agrupamento-por-ano.md):

| Grupo | Destaques (2019 / 2021 / 2023) |
| --- | --- |
| 0 | Espaços −0,8 / −0,8 / −0,9; tecnologia −0,7 / −0,8 / −0,8; materiais −0,7 nos três; porte −0,6 nos três |
| 3 | Psicólogo +3,5 / +4,2 / +2,8; nutricionista +1,7 / +1,9 / +1,7 |
| 5 | Espaços +1,4 / +1,4 / +1,3; tecnologia +1,4 / +1,3 / +1,3; materiais +1,1 nos três; ensino médio +1,2 / +1,3 / +1,0 |

Os mesmos valores aparecem nos mapas de calor dos notebooks `02_agrupamento.ipynb` e `03_agrupamento_<ano>.ipynb`.

## 1 Resumo

Cada destaque responde à pergunta: **"quanto o grupo se afasta da escola média, numa régua comum a todos os atributos?"** O cálculo tem quatro passos:

```text
1. valor de cada escola       →  o atributo (índice, presença ou porte)
2. média do grupo             →  média do atributo entre as escolas do grupo
3. média e desvio-padrão      →  das escolas de referência (do ano, ou dos três anos no agrupamento conjunto)
4. destaque                   →  (média do grupo − média de referência) / desvio-padrão de referência
```

O resultado é uma **distância em desvios-padrão** (escore z):

- o **sinal** diz se o grupo está acima (+) ou abaixo (−) da média;
- o **tamanho** diz o quanto, numa escala que vale igual para todos os atributos;
- **0** significa que o grupo é típico naquele atributo.

## 2 Passo 1: o valor de cada escola

Os atributos dos destaques são de três tipos.

### 2.1 Índices por dimensão (espaços, tecnologia, materiais, infraestrutura)

Cada índice é a **média de itens binários** do Censo (1 = a escola tem o item, 0 = não tem), ou seja, a proporção dos itens da dimensão que a escola possui. O cálculo é feito no `pipeline_02_atributos.py`.

| Índice | Itens que compõem | Valores possíveis |
| --- | --- | --- |
| `indice_espacos_pedagogicos` | biblioteca, sala de leitura, laboratório de ciências, quadra de esportes, área verde | 0; 0,2; 0,4; 0,6; 0,8; 1 |
| `indice_tecnologia` | laboratório de informática, computador de mesa para alunos, internet para alunos | 0; 0,33; 0,67; 1 |
| `indice_materiais` | materiais pedagógicos multimídia, infantil, científico, musical e artístico | 0; 0,2; 0,4; 0,6; 0,8; 1 |
| `indice_infraestrutura_basica` | água potável, água da rede, energia da rede, esgoto da rede, coleta de lixo, banheiro com chuveiro, cozinha, refeitório | 0 a 1, em passos de 0,125 |

**Exemplo:** a escola 21000034, em 2019, tem biblioteca, laboratório de ciências, quadra e área verde, mas não tem sala de leitura:

```text
indice_espacos_pedagogicos = (1 + 0 + 1 + 1 + 1) / 5 = 0,8
```

### 2.2 Variáveis de presença (psicólogo, nutricionista, ensino médio)

São variáveis 0/1 usadas diretamente:

| Variável | Vale 1 quando |
| --- | --- |
| `tem_psicologo` | a escola tem pelo menos um psicólogo |
| `tem_nutricionista` | a escola tem pelo menos um nutricionista |
| `oferece_medio` | a escola tem resultado do IDEB no ensino médio naquele ano |

### 2.3 Porte

O porte é o logaritmo do total de matrículas:

```text
porte_log = ln(1 + matrículas)
```

O logaritmo é usado porque o número de matrículas é muito assimétrico: poucas escolas têm milhares de alunos e a maioria tem algumas centenas. Na escala logarítmica, a diferença entre 100 e 200 alunos pesa o mesmo que a diferença entre 1.000 e 2.000.

## 3 Passo 2: a média do grupo

Para cada grupo, calcula-se a média simples do atributo entre as suas escolas. É a coluna `media_<atributo>` do `perfis_clusters.csv`.

- Para um **índice**, a média do grupo é o índice médio. Por exemplo, o grupo 0 de 2019 tem `indice_espacos_pedagogicos` médio de 0,08: em média, as escolas do grupo têm menos de 1 dos 5 espaços.
- Para uma variável de **presença**, a média é a **proporção de escolas que têm o item**. Por exemplo, no grupo 3 de 2019, `tem_psicologo` tem média 1,00 (todas as escolas têm psicólogo) e `tem_nutricionista` tem média 0,88 (88% têm nutricionista).
- Para o **porte**, a média está em escala logarítmica. Para voltar a matrículas, aplica-se `e^x − 1`. A média do grupo 0 de 2019 é 5,26, o que corresponde a cerca de **192 matrículas**.

## 4 Passo 3: a média e o desvio-padrão de referência

A referência é o conjunto de **todas as escolas** que participaram do agrupamento:

- nos notebooks **por ano** e na tabela acima: todas as escolas **daquele ano**;
- no notebook do **agrupamento conjunto**: todas as escolas dos três anos.

O desvio-padrão mede o quanto as escolas costumam variar em torno da média. Valores de 2019:

| Atributo | Média de 2019 | Desvio-padrão de 2019 |
| --- | --- | --- |
| Espaços pedagógicos | 0,272 | 0,242 |
| Tecnologia | 0,364 | 0,380 |
| Materiais | 0,247 | 0,242 |
| Tem psicólogo | 0,077 | 0,267 |
| Tem nutricionista | 0,209 | 0,407 |
| Porte (log) | 5,665 (≈ 288 matrículas) | 0,705 |
| Oferece ensino médio | 0,165 | 0,371 |

## 5 Passo 4: o destaque

```text
destaque = (média do grupo − média de referência) / desvio-padrão de referência
```

Dividir pelo desvio-padrão é o que põe atributos de escalas diferentes na mesma régua. Sem isso, não seria possível comparar uma diferença de 0,4 no porte (escala logarítmica) com uma diferença de 0,2 num índice que vai de 0 a 1.

### 5.1 Exemplos com os valores de 2019

| Grupo | Atributo | Média do grupo | Média do ano | Desvio-padrão | Cálculo | Destaque |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | Espaços pedagógicos | 0,082 | 0,272 | 0,242 | (0,082 − 0,272) / 0,242 | **−0,79** |
| 0 | Tecnologia | 0,085 | 0,364 | 0,380 | (0,085 − 0,364) / 0,380 | **−0,74** |
| 0 | Porte (log) | 5,263 | 5,665 | 0,705 | (5,263 − 5,665) / 0,705 | **−0,57** |
| 2 | Materiais | 0,554 | 0,247 | 0,242 | (0,554 − 0,247) / 0,242 | **+1,26** |
| 3 | Tem psicólogo | 1,000 | 0,077 | 0,267 | (1,000 − 0,077) / 0,267 | **+3,46** |
| 3 | Tem nutricionista | 0,880 | 0,209 | 0,407 | (0,880 − 0,209) / 0,407 | **+1,65** |
| 5 | Espaços pedagógicos | 0,609 | 0,272 | 0,242 | (0,609 − 0,272) / 0,242 | **+1,39** |
| 5 | Oferece ensino médio | 0,603 | 0,165 | 0,371 | (0,603 − 0,165) / 0,371 | **+1,18** |

Nas tabelas dos documentos, os valores são arredondados para uma casa decimal: −0,79 aparece como −0,8, e +3,46 como +3,5.

### 5.2 Traduzindo de volta para a escala original

O destaque é útil para comparar, mas a escala original costuma ser mais fácil de explicar a um gestor:

| Destaque | Em desvios-padrão | Na escala original |
| --- | --- | --- |
| Grupo 0, espaços | −0,8 | Em média, 0,4 dos 5 espaços, contra 1,4 na escola média |
| Grupo 0, porte | −0,6 | Cerca de 192 matrículas, contra 288 na escola média |
| Grupo 3, psicólogo | +3,5 | 100% das escolas têm psicólogo, contra 8% no geral |
| Grupo 5, ensino médio | +1,2 | 60% oferecem ensino médio, contra 17% no geral |

## 6 Por que o psicólogo tem destaques tão altos e tão variáveis

Para uma variável 0/1 em que uma fração *p* das escolas tem valor 1, o desvio-padrão é aproximadamente √(p × (1 − p)). Num grupo em que **todas** as escolas têm o item, o destaque fica:

```text
destaque = (1 − p) / √(p × (1 − p))
```

Quanto mais raro o item (*p* pequeno), maior o destaque de quem o tem:

| Ano | Escolas com psicólogo (*p*) | Destaque do grupo 3 |
| --- | --- | --- |
| 2019 | 7,7% | (1 − 0,077) / √(0,077 × 0,923) ≈ **+3,5** |
| 2021 | 5,5% | (1 − 0,055) / √(0,055 × 0,945) ≈ **+4,2** |
| 2023 | 11,3% | (0,997 − 0,113) / 0,316 ≈ **+2,8** |

Por isso o destaque do psicólogo muda de ano para ano, enquanto os outros quase não mudam. **A diferença está na raridade do psicólogo em cada ano, e não no grupo**: nos três anos, praticamente 100% das escolas do grupo 3 têm psicólogo. Esse destaque não deve ser lido como "o grupo 3 é 3,5 vezes mais diferente" do que um grupo com destaque +1; ele reflete o fato de o item ser raro.

## 7 Como ler os destaques

Uma referência prática, sem valor de corte oficial:

| Destaque (em módulo) | Leitura |
| --- | --- |
| menos de 0,3 | O grupo é típico naquele atributo |
| 0,3 a 0,8 | Diferença moderada |
| acima de 0,8 | Diferença marcante, que caracteriza o grupo |

Cuidados na leitura:

- **É uma média do grupo, não de cada escola.** Um grupo com destaque −0,8 em tecnologia pode ter algumas escolas com os três itens. O destaque descreve o grupo como um todo.
- **A régua depende da referência.** Nos notebooks por ano, a referência é o próprio ano; no notebook do conjunto, são os três anos juntos. Os valores podem diferir um pouco entre as duas versões.
- **O destaque não é o que o modelo usa internamente.** O K-Means trabalha sobre os atributos padronizados, ponderados por dimensão e reduzidos com PCA. O destaque é uma medida **descritiva**, calculada depois, só para interpretar os grupos.
- **O destaque não fica gravado em arquivo.** Ele é calculado nos notebooks a partir do `perfis_clusters.csv` (média do grupo) e do `atributos_escola_ano.csv` (média e desvio-padrão de referência).

## 8 Como reproduzir

A partir da raiz do repositório:

```python
import pandas as pd

ano = 2019
matriz = pd.read_csv("data/processed/atributos_escola_ano.csv", dtype={"id_escola": "string"})
grupos = pd.read_csv(f"data/processed/agrupamento/{ano}/atribuicoes.csv", dtype={"id_escola": "string"})
escolas = matriz[matriz["ano"] == ano].merge(grupos, on=["id_escola", "ano"])

atributos = ["indice_espacos_pedagogicos", "indice_tecnologia", "indice_materiais",
             "tem_psicologo", "tem_nutricionista", "porte_log", "oferece_medio"]

media_grupo = escolas.groupby("cluster")[atributos].mean()   # passo 2
media_ano = escolas[atributos].mean()                         # passo 3
desvio_ano = escolas[atributos].std()                         # passo 3
destaques = (media_grupo - media_ano) / desvio_ano            # passo 4
print(destaques.round(1))
```

Para o agrupamento conjunto, basta usar `data/processed/agrupamento/atribuicoes.csv` e não filtrar por ano.
