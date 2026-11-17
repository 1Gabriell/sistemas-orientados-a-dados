# Próximos passos — Agrupamento das escolas

Registro do planejamento da etapa de **descoberta de padrões** (agrupamento), elaborado em 01/10/2026 e atualizado em 19/10/2026 a partir da base `data/processed/base_integrada.csv` (79.374 linhas × 61 colunas). Antes de aplicar qualquer algoritmo, é necessário construir uma **matriz de atributos** própria para o agrupamento: a base integrada mistura identificadores, contexto, perfil da escola e resultados, repete os atributos do Censo quando a escola tem mais de uma etapa avaliada, e suas variáveis têm escalas muito diferentes (por exemplo, `desktop_aluno` varia de 0 a 1, enquanto `quantidade_matricula_parda` chega a 2.505).

## 1. Unidade de análise e escopo dos atributos

### 1.1 Duplicação dos atributos do Censo entre etapas

A base integrada tem uma linha por **escola × ano × etapa**, porque o IDEB é calculado por etapa. Os atributos do Censo, porém, descrevem a **escola inteira**: quando a escola oferece mais de uma etapa avaliada, o `pipeline_01` repete as mesmas informações do Censo em cada linha, e só os resultados do IDEB mudam.

| Situação | Escolas-ano |
| --- | --- |
| Aparece 1 vez | 45.409 |
| Aparece 2 vezes (quase sempre iniciais + finais) | 16.783 |
| Aparece 3 vezes | 133 |
| **Total de escolas-ano distintas** | **62.325** (em 79.374 linhas) |

Nas 33.965 linhas que pertencem a escolas-ano repetidas, os atributos do Censo são **idênticos em 100% dos casos**. Exemplo (escola 21000190, 2021):

| anos_escolares | biblioteca | matrícula parda | ideb |
| --- | --- | --- | --- |
| finais (6-9) | 0 | 213 | 3,2 |
| iniciais (1-5) | 0 | 213 | 3,3 |

Agrupar as 79.374 linhas diretamente causaria três problemas:

1. **Peso duplicado:** escolas com mais etapas contam duas ou três vezes e puxam os centros dos grupos na sua direção.
2. **Pontos idênticos:** linhas iguais caem sempre no mesmo grupo e inflam métricas de coesão, como a silhueta.
3. **Matrículas da escola, não da etapa:** `quantidade_matricula_*` é o total da escola e não pode ser lido como se descrevesse só os alunos daquela etapa.

### 1.2 Decisões

| Decisão | Escolha | Justificativa |
| --- | --- | --- |
| Unidade do agrupamento | **Escola × ano (62.325 linhas, sem repetição)** | Os atributos do Censo são da escola. Cada escola-ano recebe **um único grupo de perfil**, sem peso duplicado. |
| Etapas oferecidas | Indicadores `oferece_iniciais`, `oferece_finais` e `oferece_medio` | Preserva a informação de quais etapas a escola tem avaliadas, que antes estava implícita na repetição das linhas. |
| Uso do IDEB | Ligar o grupo de volta a cada linha escola × ano × etapa e comparar o IDEB **dentro do grupo e por etapa** | O IDEB não é comparável entre etapas, mas o perfil da escola é o mesmo. Assim se mantém a cadeia perfil → grupo → anomalia. |
| Alternativa descartada | Agrupar cada etapa separadamente | Dentro de uma etapa não há repetição, mas a mesma escola receberia grupos diferentes nos iniciais e nos finais para um perfil idêntico, o que confunde o gestor. |
| Resultados | Não usar `ideb`, `nota_saeb_media_padronizada`, `taxa_aprovacao`, `indicador_rendimento` e `projecao` como atributos | O agrupamento é feito pelo **perfil** da escola. O IDEB entra depois, para caracterizar os grupos e identificar quem destoa dos pares. Incluí-lo tornaria a análise circular. |
| Ano de 2021 | Agrupar cada ano separadamente e comparar a estabilidade, ou agrupar os anos juntos e usar o ano só na interpretação | 2021 foi afetado pela pandemia e tem menos escolas-ano (17.472, contra 22.312 em 2019 e 22.541 em 2023). |

As colunas devem ser separadas em quatro papéis:

| Papel | Colunas |
| --- | --- |
| Identificação | `id_escola`, `id_escola_nome`, município e as colunas `*_ideb` duplicadas (`sigla_uf_ideb`, `id_municipio_ideb` etc.) |
| Contexto | `rede`, `tipo_localizacao`, `sigla_uf_censo` |
| Atributos do agrupamento | Infraestrutura, tecnologia, profissionais, materiais pedagógicos, turnos, porte, composição das matrículas e etapas oferecidas |
| Resultados (fora do modelo) | `ideb`, `nota_saeb_media_padronizada`, `taxa_aprovacao`, `indicador_rendimento`, `projecao` |

## 2. Novo pipeline de preparação (`pipeline_02_atributos.py`)

O `pipeline_01.py` **não será alterado**. A base `data/processed/base_integrada.csv` já gerada por ele é a **entrada** de um pipeline novo, que aplica as modificações necessárias para o agrupamento e grava os resultados em arquivos separados. Assim a base integrada continua sendo o registro auditável da Atividade 02, e todas as decisões de preparação para os modelos ficam concentradas em um só lugar.

```text
pipeline_01.py  →  base_integrada.csv  →  pipeline_02_atributos.py  →  atributos_escola_ano.csv
 (inalterado)     (entrada, só leitura)                                ligacao_etapas.csv
                                                                       relatorio_atributos.json
```

Sequência de operações do pipeline:

1. Ler a base integrada e validar que os atributos do Censo são idênticos entre as etapas de uma mesma escola-ano (falhar com erro se não forem).
2. Criar os indicadores `oferece_*` e **remover a duplicação**, mantendo uma linha por `id_escola + ano`.
3. Excluir as colunas com ausência estrutural e imputar os demais ausentes (seção 2.1).
4. Aplicar as demais transformações (seção 2.2).
5. Gravar a matriz por escola-ano, a tabela de ligação com as etapas e o relatório.

### 2.1 Valores ausentes

Um diagnóstico da base integrada mostrou que a ausência **não é aleatória: ela depende do ano**. Algumas variáveis só passaram a ser coletadas pelo Censo depois de 2019, então a ausência é estrutural e não pode ser "preenchida" como se fosse um erro de registro. As contagens abaixo já consideram a base sem duplicação (62.325 escolas-ano).

| Variáveis | Escolas-ano com ausência | Padrão observado | Tratamento |
| --- | --- | --- | --- |
| `laboratorio_educacao_profissional`, `quantidade_matricula_utiliza_transporte_publico` | 39.784 (63,8%) | 100% ausentes em 2019 e 2021; coletadas só em 2023 | **Excluir** do agrupamento. Imputar dois terços de uma coluna inventaria dados. Além disso, 99,3% das escolas têm 0 em `laboratorio_educacao_profissional`. |
| `profissional_assistente_social` | 22.312 (35,8%) | 100% ausente em 2019; completa em 2021 e 2023 | **Excluir** se os anos forem agrupados juntos; pode ser mantida se 2021 e 2023 forem agrupados separadamente. 95% das escolas têm valor 0, então a variável quase não diferencia escolas. |
| Cinco variáveis `material_pedagogico_*` | 2.102 (3,4%) | Só em 2019, sempre as cinco juntas; distribuição parecida entre redes e localizações | Imputação em duas etapas (abaixo) + coluna indicadora `materiais_imputados`. |
| `orgao_gremio_estudantil` | 482 (0,8%) | Só em 2019 | Mesma imputação em duas etapas + coluna indicadora. |
| `quantidade_profissional_pedagogia` | 28 (0,04%) | Isolados | Mediana do grupo de pares (é contagem, não categoria). |
| `id_escola_nome` | — | Identificação | Nenhum tratamento: não entra no modelo. |

As colunas excluídas **continuam na `base_integrada.csv`**; apenas não entram na matriz do agrupamento. A lista de colunas excluídas deve ser **configurável** no pipeline e registrada no relatório, para que possa ser revista caso o agrupamento passe a ser feito só com 2023 (quando as três colunas estão completas) ou só com 2021 e 2023 (quando `profissional_assistente_social` está completa).

**Por que excluir as colunas e não as linhas:** manter essas colunas exigiria descartar os anos inteiros em que elas não existem (um ou dois terços da base) para salvar variáveis que, além disso, quase não variam entre as escolas.

**Imputação em duas etapas para as variáveis binárias de 2019:**

1. **Valor da própria escola em outro ano** (de preferência 2021, o ano mais próximo). A mesma escola costuma manter os mesmos materiais e o mesmo grêmio de uma edição para a outra, então esse valor é a melhor estimativa disponível. Isso resolve a maior parte dos casos: 1.817 das 2.102 escolas-ano sem materiais (86%) e 417 das 482 sem grêmio (87%).
2. **Moda do grupo de pares** (`ano × rede × tipo_localizacao`) para o que restar (285 escolas-ano em materiais e 65 em grêmio), ou seja, escolas que só aparecem em 2019.

**Por que a moda (e não a média ou a mediana)?** As variáveis são binárias (0 = não tem, 1 = tem). A média produziria valores como 0,74, que não correspondem a nenhuma escola real e criariam um nível intermediário artificial que o K-Means trataria como uma posição real no espaço. A moda devolve sempre um valor válido (0 ou 1): o mais provável para aquele tipo de escola. Para variáveis binárias, a mediana coincide com a moda, então não oferece vantagem.

**Limites da moda e como mitigá-los:**

- Ela empurra os imputados para a categoria majoritária e reduz a variabilidade. Por exemplo, em `material_pedagogico_cientifico`, 84% das escolas têm valor 0, então toda escola imputada pela moda global receberia 0. Calcular a moda **dentro do grupo de pares** reduz esse viés, porque escolas urbanas estaduais e rurais municipais têm modas diferentes.
- Como a moda é só o recurso da etapa 2, ela atinge poucas linhas, com efeito desprezível no agrupamento.
- A coluna indicadora permite verificar depois se as escolas imputadas se concentram em algum grupo, e repetir o agrupamento sem elas como teste de sensibilidade.
- O relatório do pipeline registra quantas linhas foram preenchidas em cada etapa da imputação e em cada coluna.

### 2.2 Demais transformações e normalização

A maioria dos algoritmos previstos mede **distância** entre escolas, e sem normalização as variáveis de maior escala dominam essa distância. Na matriz atual, `quantidade_matricula_parda` vai até 2.505 enquanto `biblioteca` vale 0 ou 1: sem tratamento, o agrupamento seria basicamente por **tamanho da escola**.

| Modelo | Precisa de normalização? | Motivo |
| --- | --- | --- |
| K-Means, Ward (hierárquico) | **Sim** | Baseados em distância euclidiana. |
| HDBSCAN, LOF | **Sim** | Baseados em densidade e vizinhança, ou seja, em distância. |
| PCA | **Sim** | Sem padronização, os componentes só capturam as variáveis de maior variância. |
| Isolation Forest | Não | Usa cortes por árvore em cada variável; a escala não importa. |

Aplicar o `StandardScaler` direto não basta. Um diagnóstico da matriz sem duplicação (62.325 escolas-ano) mostrou três problemas que precisam ser tratados **antes** do scaler, no `pipeline_02`:

**1. Contagens muito assimétricas.** As matrículas têm assimetria entre 2 e 31, e `quantidade_profissional_pedagogia` tem mediana 1, percentil 99 igual a 10 e máximo 398 (provável erro de registro). Média e desvio-padrão são puxados por esses extremos. Tratamento:

- converter as contagens em **razões e proporções** (matrículas por raça/cor como % do total, profissionais por 100 alunos), lembrando que as matrículas são da escola inteira, não da etapa;
- aplicar `log1p` no porte (total de matrículas) e nas contagens restantes;
- **limitar os extremos aos percentis 1 e 99** (winsorização), registrando no relatório quantas linhas foram afetadas em cada coluna.

**2. Variáveis binárias raras explodem após a padronização.** Uma variável 0/1 com proporção *p* de valores 1, depois de padronizada, dá às escolas com valor 1 o valor (1 − p) / √(p(1 − p)). Para `dormitorio_aluno` (p = 0,4%), isso equivale a **cerca de 16 desvios-padrão**: essa única coluna dominaria a distância e criaria um grupo só de "escolas com dormitório". Por isso, as variáveis **quase constantes** (menos de 1–2% em uma das categorias) devem ser removidas da matriz do agrupamento:

| Quase sempre 0 | Quase sempre 1 |
| --- | --- |
| `dormitorio_aluno` (0,4% com valor 1) | `energia_rede_publica` (99,9%) |
| `quantidade_profissional_saude` (percentil 99 = 0) | `alimentacao` (99,7%), `diurno` (99,3%), `cozinha` (98,3%) |

Essas variáveis quase não diferenciam escolas, mas continuam úteis como **sinal de anomalia** (por exemplo, uma escola sem energia da rede pública) na funcionalidade de detecção de anomalias. O limiar de remoção deve ser configurável e registrado no relatório.

**3. Desequilíbrio entre dimensões.** Há cerca de 20 binárias de infraestrutura e materiais contra poucas variáveis de recursos humanos e porte. Depois da padronização todas as colunas pesam igual, então a dimensão com mais colunas pesa mais. Duas saídas, a serem comparadas:

- usar os **índices por dimensão** (por exemplo, proporção de itens de infraestrutura presentes, de 0 a 1), que também servem para a funcionalidade de prioridades;
- ou ponderar cada coluna por 1/√(número de colunas da sua dimensão), para que cada dimensão contribua igualmente para a distância.

**Demais transformações:**

| Problema nos dados | Tratamento previsto | Onde |
| --- | --- | --- |
| Variáveis categóricas (`rede`, `tipo_localizacao`) | One-hot, ou usá-las para estratificar a análise em vez de agrupar por elas. | `pipeline_02` |
| Escalas diferentes | Padronizar com `StandardScaler`. | Modelagem |
| Redundância entre atributos | Reduzir com PCA. | Modelagem |

**Sequência completa:**

```text
pipeline_02 (escala original, interpretável)
  razões/proporções → log1p → winsorização p1–p99 → remoção de quase constantes → índices por dimensão
        │
modelagem (ajustado junto com o modelo)
  StandardScaler → (ponderação por dimensão) → PCA → K-Means / Ward / HDBSCAN
```

A padronização e o PCA ficam na etapa de modelagem, e não no pipeline. Assim a matriz de atributos mantém os valores na escala original, legíveis para interpretar os grupos, e as transformações dependentes dos dados são ajustadas junto com o modelo. Dois cuidados:

- **Ajustar o scaler com todos os anos juntos.** Se for ajustado ano a ano, a mesma escola com a mesma infraestrutura teria valores padronizados diferentes em 2019 e 2023, distorcendo a comparação de estabilidade entre anos. No agrupamento não há separação entre treino e teste, então ajustar sobre a matriz inteira não causa vazamento de dados.
- **Usar o `StandardScaler` como padrão e o `RobustScaler` como teste de sensibilidade.** Após `log1p` e winsorização, a diferença deve ser pequena; se os grupos mudarem muito, ainda há extremos influenciando o resultado.

## 3. Estrutura proposta no repositório

```text
pipelines/
  pipeline_01.py                # inalterado: gera a base_integrada.csv
  pipeline_02_atributos.py      # novo: base_integrada → matriz de atributos por escola-ano
  tests/test_atributos.py
modelos/
  agrupamento.py                # ajuste, escolha de k e rotulagem dos grupos
notebooks/
  02_agrupamento.ipynb          # escolha de k, perfis e visualizações
data/processed/
  base_integrada.csv            # entrada do pipeline_02 (não é sobrescrita)
  atributos_escola_ano.csv      # uma linha por id_escola + ano: atributos + oferece_* + indicadores de imputação
  ligacao_etapas.csv            # id_escola, ano, anos_escolares + resultados do IDEB (para ligar os grupos às etapas)
  relatorio_atributos.json      # duplicatas removidas, colunas excluídas, imputações, winsorização e quase constantes removidas
  agrupamento/
    atribuicoes.csv             # id_escola, ano, cluster
    perfis_clusters.csv         # média dos atributos por cluster e IDEB por cluster e etapa
    metricas.json               # silhueta, Davies-Bouldin, k escolhido
docs/atividade-03-agrupamento.md
```

Dependência a adicionar ao `requirements.txt`: **`scikit-learn`**, que ainda não está instalado no ambiente virtual (`numpy` e `matplotlib` já estão).

## 4. Algoritmos e avaliação

| Aspecto | Abordagem |
| --- | --- |
| Algoritmo de partida | K-Means sobre os dados padronizados (seção 2.2) e reduzidos com PCA. |
| Comparações | Agrupamento hierárquico (Ward) em uma amostra e HDBSCAN, que encontra grupos de formato irregular e marca pontos como ruído, o que se conecta à detecção de anomalias. |
| Escolha do número de grupos (k) | Silhueta, Davies-Bouldin, Calinski-Harabasz e curva do cotovelo. |
| Estabilidade | Índice de Rand ajustado (ARI) entre execuções com sementes ou amostras diferentes e entre os anos. |
| Interpretação | Perfil médio de cada grupo e distribuição do IDEB dentro de cada grupo, **separada por etapa**, que é o que interessa ao gestor. |

## 5. Situação

Os passos abaixo foram executados; os resultados estão em [Atividade 03 — Agrupamento](atividade-03-agrupamento.md).

| Passo | Situação |
| --- | --- |
| Adicionar `scikit-learn` ao `requirements.txt` | Concluído |
| Implementar o `pipeline_02_atributos.py` e os testes (validação entre etapas, uma linha por escola-ano, sem ausentes, prioridade da própria escola na imputação, winsorização e quase constantes) | Concluído: 6 testes novos, todos passando junto com os 4 do pipeline 01 |
| Implementar `modelos/agrupamento.py` (K-Means, métricas por k, estabilidade, Ward, HDBSCAN, StandardScaler × RobustScaler) | Concluído |
| Criar o notebook `02_agrupamento.ipynb` | Concluído |
| Ligar os grupos às etapas e analisar o IDEB por grupo e etapa | Concluído |
| Registrar decisões e resultados em `docs/atividade-03-agrupamento.md` e atualizar o README | Concluído |

Ajuste em relação ao plano: os profissionais (contagens) também passam primeiro pela imputação com o valor da própria escola em outro ano, e só o restante usa a mediana dos pares.

## 6. Decisões tomadas e pontos em aberto

Decisões tomadas em 19/10/2026, após a primeira rodada:

- **Profissionais raros:** nutricionista, psicólogo e profissional de saúde passaram de razão por 100 alunos para indicadores de presença. A razão ficava inflada em escolas pequenas e formava um grupo artificial. Pedagogos continuam como razão.
- **Número de grupos:** k = 6.
- **Contexto (`rede`, `tipo_localizacao`, UF):** fora dos atributos do agrupamento; usado só na interpretação.

Pontos em aberto:

1. **Grupo "apoio multiprofissional":** com a troca para presença, a presença de psicólogo (8% das escolas) passou a formar um grupo próprio, menos estável entre os anos (ARI de 0,54 a 0,61 nos pares com 2021). Avaliar se é um perfil útil para o gestor ou se esses indicadores devem ter peso menor.
2. **Nomes dos grupos:** revisar com conhecimento do domínio.
3. **Próxima funcionalidade:** detecção de anomalias usando os grupos como pares (IDEB e evolução entre edições dentro de grupo × etapa).
