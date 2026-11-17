# Agrupamento separado por ano — 2019, 2021 e 2023

## 1 Objetivo

Verificar se os perfis de escola encontrados no [agrupamento conjunto](atividade-03-agrupamento.md), que junta os três anos, também aparecem quando o K-Means é aplicado **a cada ano separadamente**. Se os mesmos grupos surgirem em cada ano, a tipologia não depende de misturar os anos e pode ser usada com segurança para comparar escolas dentro de cada edição do IDEB.

## 2 Como foi feito

- **Entrada:** a mesma matriz gerada pelo `pipeline_02_atributos.py` (`data/processed/atributos_escola_ano.csv`), filtrada por ano.
- **Ajuste por ano:** a padronização (`StandardScaler`), a ponderação por dimensão, o PCA (90% da variância, 13 componentes nos três anos) e o K-Means foram ajustados **só com as escolas de cada ano**.
- **Configuração igual à do agrupamento conjunto:** conjunto de atributos `indices`, ponderação por dimensão e **k = 6**, para que os anos sejam comparáveis. Os grupos são numerados em ordem crescente do índice de tecnologia, o que mantém a mesma numeração entre os anos.
- **Execução:** `python modelos/agrupamento.py --ano 2019` (e o mesmo para 2021 e 2023).

| Ano | Resultados | Notebook |
| --- | --- | --- |
| 2019 | `data/processed/agrupamento/2019/` | [03_agrupamento_2019.ipynb](../notebooks/03_agrupamento_2019.ipynb) |
| 2021 | `data/processed/agrupamento/2021/` | [03_agrupamento_2021.ipynb](../notebooks/03_agrupamento_2021.ipynb) |
| 2023 | `data/processed/agrupamento/2023/` | [03_agrupamento_2023.ipynb](../notebooks/03_agrupamento_2023.ipynb) |

Cada pasta tem os mesmos três arquivos do agrupamento conjunto: `atribuicoes.csv` (grupo de cada escola), `perfis_clusters.csv` (perfil e IDEB por grupo) e `metricas.json` (métricas, estabilidade e comparações).

**Limitação:** a matriz de entrada foi preparada com os três anos juntos. Os limites da winsorização e a lista de variáveis quase constantes foram calculados sobre a base inteira, e não ano a ano. Como as distribuições são parecidas entre os anos, o efeito esperado é pequeno.

## 3 Escolha de k em cada ano

| k | Silhueta 2019 | Silhueta 2021 | Silhueta 2023 | Davies-Bouldin 2019 | Davies-Bouldin 2021 | Davies-Bouldin 2023 |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | 0,208 | 0,209 | 0,210 | 1,85 | 1,84 | 1,83 |
| 5 | 0,144 | 0,144 | **0,136** | 2,01 | 1,97 | 1,99 |
| **6** | **0,149** | **0,146** | 0,133 | 1,85 | 1,83 | **1,91** |
| 7 | 0,147 | **0,146** | 0,117 | **1,78** | **1,82** | 2,08 |

- As métricas são praticamente iguais às do agrupamento conjunto: silhueta baixa em todos os k e em todos os anos. As escolas formam um contínuo em cada ano, não só quando os anos são juntados.
- O k = 2 tem sempre a maior silhueta, mas só separa escolas com mais e com menos recursos.
- Entre k = 5 e 7, as diferenças são pequenas. O k = 6 é o melhor ou está empatado com o melhor em 2019 e 2021, e em 2023 tem o menor Davies-Bouldin, com silhueta só 0,003 abaixo de k = 5. O k = 6 foi mantido nos três anos.

## 4 Estabilidade em cada ano

| Verificação | 2019 | 2021 | 2023 |
| --- | --- | --- | --- |
| ARI entre sementes | 0,998 a 0,999 | 0,995 a 1,000 | 0,995 a 0,998 |
| ARI entre reamostragens | 0,968 a 0,982 | 0,947 a 0,987 | 0,953 a 0,978 |
| ARI `StandardScaler` × `RobustScaler` | 0,24 | 0,17 | 0,49 |
| ARI K-Means × Ward (amostra) | 0,44 | 0,29 | 0,36 |
| HDBSCAN (amostra) | 2 grupos, 3% de ruído | 2 grupos, 1% de ruído | 2 grupos, 15% de ruído |

- Dentro de cada ano, a partição é reprodutível: a mesma configuração gera praticamente os mesmos grupos. 2021, com menos escolas, varia um pouco mais entre reamostragens.
- A sensibilidade ao escalonador é maior por ano do que no conjunto (ARI de 0,52 no conjunto). O motivo é o mesmo: o `RobustScaler` não reescala as variáveis binárias raras. O resultado depende, portanto, da escolha do `StandardScaler`.
- Como no conjunto, o HDBSCAN só encontra duas regiões densas, separadas pela presença de psicólogo.

## 5 Comparação com o agrupamento conjunto

| Ano | ARI com o conjunto | Escolas no mesmo grupo nas duas versões |
| --- | --- | --- |
| 2019 | 0,947 | 97,8% |
| 2021 | 0,941 | 97,1% |
| 2023 | 0,904 | 95,8% |

**Os mesmos seis perfis aparecem em cada ano, com a mesma numeração.** Nas tabelas cruzadas dos notebooks (seção 4), cada grupo do ano corresponde quase inteiramente ao grupo de mesmo número no conjunto. As maiores trocas são pequenas, como 231 escolas do grupo 0 de 2023 que no conjunto ficam no grupo 1.

**Isso esclarece um resultado anterior.** No agrupamento conjunto, a estabilidade "entre anos" foi baixa nos pares com 2021 (ARI de 0,54 a 0,61). Uma verificação adicional mostrou a causa: quando o K-Means é ajustado só com as escolas de 2021, mas na escala calculada com os três anos juntos, ele **não forma o grupo de apoio multiprofissional** e, em vez disso, divide o grupo de recursos mínimos em dois. Em 2021 só 5% das escolas tinham psicólogo, contra 8% no conjunto, e nessa escala o grupo não se sustenta. Com a escala do próprio ano, a presença de psicólogo volta a se destacar e o grupo reaparece. Ou seja, **os perfis são estáveis no tempo; o grupo de apoio multiprofissional é o único sensível à escala** e é o mais frágil da tipologia.

## 6 Perfis e tamanhos dos grupos por ano

| Grupo | Nome | 2019 | 2021 | 2023 |
| --- | --- | --- | --- | --- |
| 0 | Recursos mínimos | 7.314 (32,8%) | 5.704 (32,6%) | 6.530 (29,0%) |
| 1 | Espaços sem tecnologia | 3.748 (16,8%) | 2.791 (16,0%) | 3.361 (14,9%) |
| 2 | Materiais sem tecnologia | 3.191 (14,3%) | 2.606 (14,9%) | 3.305 (14,7%) |
| 3 | Apoio multiprofissional | 1.457 (6,5%) | 887 (5,1%) | 1.847 (8,2%) |
| 4 | Tecnologia sem espaços | 3.658 (16,4%) | 3.049 (17,5%) | 3.802 (16,9%) |
| 5 | Estrutura completa | 2.944 (13,2%) | 2.435 (13,9%) | 3.696 (16,4%) |

Os destaques de cada grupo, em desvios-padrão em relação à média do próprio ano, se repetem nos três anos. O cálculo está explicado em [Cálculo dos destaques dos grupos](calculo-dos-destaques.md).

| Grupo | Destaques (2019 / 2021 / 2023) |
| --- | --- |
| 0 | Espaços −0,8 / −0,8 / −0,9; tecnologia −0,7 / −0,8 / −0,8; materiais −0,7 nos três; porte −0,6 nos três |
| 1 | Espaços +0,8 / +0,8 / +0,7; tecnologia −0,4 / −0,5 / −0,5 |
| 2 | Materiais +1,3 / +1,2 / +1,2; tecnologia −0,4 nos três |
| 3 | Psicólogo +3,5 / +4,2 / +2,8; nutricionista +1,7 / +1,9 / +1,7 |
| 4 | Tecnologia +1,2 / +1,1 / +1,0 |
| 5 | Espaços +1,4 / +1,4 / +1,3; tecnologia +1,4 / +1,3 / +1,3; materiais +1,1 nos três; ensino médio +1,2 / +1,3 / +1,0 |

O destaque do psicólogo no grupo 3 muda mais que os outros porque a presença de psicólogo variou entre os anos (8%, 5% e 11% das escolas). Quanto mais rara a presença, maior a distância de quem tem psicólogo em relação à média.

Mudanças ao longo do tempo:

- **Recursos mínimos** caiu de 32,8% das escolas em 2019 para 29,0% em 2023.
- **Estrutura completa** subiu de 13,2% para 16,4%.
- **Apoio multiprofissional** caiu em 2021 (5,1%) e cresceu em 2023 (8,2%), acompanhando a presença de psicólogos.

Como cada ano tem a própria escala, essas proporções comparam a posição relativa das escolas dentro de cada ano, e não níveis absolutos de recursos. Para medir a evolução absoluta, o agrupamento conjunto, com uma única régua, é mais adequado.

## 7 IDEB por grupo, etapa e ano

IDEB mediano (anos iniciais / anos finais / ensino médio):

| Grupo | 2019 | 2021 | 2023 |
| --- | --- | --- | --- |
| 0 · Recursos mínimos | 4,7 / 3,9 / 3,2 | 4,7 / 4,2 / 3,3 | 4,9 / 4,1 / 3,5 |
| 1 · Espaços sem tecnologia | 5,1 / 4,2 / 3,6 | 5,2 / 4,7 / 3,9 | 5,3 / 4,4 / 3,8 |
| 2 · Materiais sem tecnologia | 5,1 / 4,3 / 3,7 | 5,1 / 4,7 / 4,0 | 5,2 / 4,5 / 4,0 |
| 3 · Apoio multiprofissional | 4,8 / 4,0 / — | 4,9 / 4,5 / — | 5,2 / 4,4 / 4,0 |
| 4 · Tecnologia sem espaços | 5,2 / 4,4 / 3,8 | 5,1 / 4,6 / 4,0 | 5,2 / 4,4 / 3,9 |
| 5 · Estrutura completa | 5,5 / 4,5 / 4,1 | 5,4 / 4,9 / 4,3 | 5,5 / 4,7 / 4,3 |

O "—" indica células com poucas observações (9 escolas em 2019 e 13 em 2021), que não devem ser interpretadas.

- **A ordem se repete nos três anos:** o grupo 0 tem as menores medianas e o grupo 5 as maiores, em todas as etapas. Os grupos 1 a 4 ficam próximos entre si.
- **O IDEB de 2021 não é comparável aos outros anos.** A taxa de aprovação mediana chegou a 100% nos anos iniciais e a 99% nos finais (contra 94% e 90% em 2019), o que eleva o indicador de rendimento e, com ele, o IDEB, sem melhora no Saeb. Por isso os anos finais de 2021 parecem melhores.
- **Associação não é causa:** os grupos também diferem em rede, localização e porte.

## 8 Conclusões

1. **A tipologia é robusta no tempo.** Agrupando cada ano separadamente, aparecem os mesmos seis perfis, com 96% a 98% das escolas no mesmo grupo do agrupamento conjunto.
2. **O grupo de apoio multiprofissional é o mais frágil.** Ele depende de uma variável rara (presença de psicólogo) e desaparece quando 2021 é agrupado na escala dos três anos. Ao usá-lo como grupo de pares, convém tratá-lo com cautela.
3. **Para a detecção de anomalias, as duas versões servem e se complementam:**
   - o agrupamento **por ano** compara cada escola com os pares da mesma edição, com a escala daquele ano, o que é adequado para encontrar escolas que destoam em um ano específico;
   - o agrupamento **conjunto** usa uma régua única, o que é adequado para acompanhar a evolução de uma escola entre as edições.
4. **O IDEB de 2021 deve ser comparado só dentro de 2021**, por causa da aprovação quase universal no ano da pandemia.
