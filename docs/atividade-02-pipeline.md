# Atividade 02 - Pipeline de preparação e integração dos dados

## 1 Explicação do pipeline

O pipeline desenvolvido nesta atividade tem como objetivo preparar, validar e integrar os dados do Censo Escolar com os resultados do Índice de Desenvolvimento da Educação Básica (IDEB) para os anos de **2019, 2021 e 2023**. As duas fontes foram obtidas a partir da Base dos Dados e possuem informações complementares: o Censo descreve as características das escolas, enquanto o IDEB apresenta indicadores de rendimento e desempenho educacional.

O programa recebe dois arquivos CSV, verifica se eles possuem a estrutura esperada, padroniza os campos utilizados no relacionamento, valida a qualidade das chaves e produz uma base integrada. Ao final da execução também é gerado um relatório de auditoria contendo as quantidades recebidas, filtradas, relacionadas e gravadas.

A chave da base integrada é:

```text
id_escola + ano + anos_escolares
```

O uso das três colunas é necessário porque uma mesma escola pode possuir resultados de mais de uma etapa de ensino no mesmo ano. Dessa forma, utilizar apenas `id_escola + ano` provocaria repetições no IDEB e impediria a validação correta do relacionamento.

### 1.1 Granularidade das fontes

O arquivo do Censo Escolar possui uma linha para cada combinação de escola e ano. Sua chave é:

```text
id_escola + ano
```

O arquivo do IDEB possui uma linha para cada combinação de escola, ano e etapa de ensino. Sua chave é:

```text
id_escola + ano + anos_escolares
```

Para compatibilizar essas duas granularidades, o pipeline identifica no IDEB quais etapas existem para cada escola e ano e associa essas etapas ao registro correspondente do Censo. Com isso, os atributos escolares, como infraestrutura, recursos e matrículas, são repetidos somente para as etapas efetivamente observadas no IDEB.

Esse procedimento não calcula médias, não agrega etapas e não cria resultados educacionais. Os valores dos indicadores continuam sendo os valores originais do IDEB. Nos arquivos utilizados nesta atividade, todas as observações do IDEB encontraram correspondência no Censo.

## 2 Como executar

Para executar o pipeline é necessário possuir o Python 3.10 ou uma versão mais recente. Os comandos devem ser executados a partir da raiz do repositório.

### 2.1 Preparação do ambiente

No Windows PowerShell, o ambiente pode ser preparado com os seguintes comandos:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

O arquivo `requirements.txt` instala o Pandas, biblioteca utilizada para leitura, transformação, validação e integração das tabelas.

### 2.2 Execução com os caminhos padrão

Com o ambiente preparado, o pipeline pode ser executado por meio do comando:

```powershell
python pipelines/pipeline_01.py
```

Nessa forma de execução, o programa utiliza os arquivos de entrada e saída apresentados na Seção 1.2.

### 2.3 Execução com caminhos personalizados

Também é possível informar outros caminhos pela linha de comando:

```powershell
python pipelines/pipeline_01.py --censo caminho/censo.csv --ideb caminho/ideb.csv --saida caminho/base_integrada.csv --relatorio caminho/relatorio.json
```

Para consultar as opções disponíveis:

```powershell
python pipelines/pipeline_01.py --help
```

Caso seja encontrada uma inconsistência que comprometa a confiabilidade da base, o programa é interrompido com código de erro. A saída definitiva não é substituída por um arquivo parcialmente processado.

## 3 Entradas e saídas

| Tipo | Arquivo | Conteúdo |
| --- | --- | --- |
| Entrada | `data/censo_nordeste_2019+.csv` | Características, infraestrutura, recursos e matrículas das escolas por ano. |
| Entrada | `data/ideb_nordeste_2019+.csv` | Indicadores educacionais por escola, ano e etapa de ensino. |
| Saída | `data/processed/base_integrada.csv` | Base integrada na granularidade escola-ano-etapa. |
| Saída | `data/processed/relatorio_execucao.json` | Relatório com contagens e resultados das validações. |

O código principal está disponível em `pipelines/pipeline_01.py`. Os caminhos apresentados na tabela são os valores padrão, mas podem ser substituídos pelos argumentos de linha de comando descritos na Seção 2.3.

## 4 Passo a passo

O processamento é composto pelas seguintes etapas:

1. Leitura dos arquivos do Censo Escolar e do IDEB.
2. Verificação das colunas obrigatórias de cada fonte.
3. Padronização dos identificadores, do ano e da etapa de ensino.
4. Conversão e validação dos indicadores numéricos do IDEB.
5. Seleção dos anos de 2019, 2021 e 2023.
6. Verificação de valores ausentes nas chaves.
7. Verificação de duplicidades nas chaves do Censo e do IDEB.
8. Identificação das etapas de ensino existentes para cada escola e ano.
9. Expansão controlada dos registros do Censo para a granularidade escola-ano-etapa.
10. Integração 1:1 entre o Censo expandido e o IDEB.
11. Verificação da consistência de estado e município entre as fontes.
12. Validação da chave da base integrada.
13. Gravação do CSV processado e do relatório de auditoria.

As validações são utilizadas para impedir que problemas de estrutura, tipo, domínio ou relacionamento sejam propagados para a base final.

## 5 Fluxo passo a passo

### 5.1 Definição do recorte e das chaves

No início do programa são definidos os anos válidos e as chaves utilizadas no processamento. O Censo é validado por `id_escola + ano`, enquanto o IDEB e a base integrada são validados por `id_escola + ano + anos_escolares`.

Essa separação representa a diferença de granularidade existente entre as fontes e evita tratar como duplicidade legítimas observações de etapas de ensino diferentes.

### 5.2 Leitura dos arquivos

A função `ler_csv` verifica se o arquivo informado existe e utiliza o Pandas para carregá-lo. Os campos `id_escola` e `id_municipio` são lidos como texto, pois funcionam como identificadores e não como medidas numéricas.

Os nomes das colunas também têm seus espaços externos removidos. Depois da leitura, o programa registra no log a quantidade de linhas e colunas de cada fonte.

### 5.3 Verificação das colunas obrigatórias

A função `validar_colunas` compara as colunas recebidas com a estrutura mínima esperada. No Censo são obrigatórios `ano`, `id_escola` e `id_municipio`. No IDEB também são exigidos a etapa de ensino e os principais indicadores utilizados no projeto.

Se uma coluna obrigatória estiver ausente, a execução é interrompida antes das transformações e do cruzamento.

### 5.4 Padronização das chaves

A função `padronizar_chaves` realiza as seguintes transformações:

- converte `id_escola` e `id_municipio` para texto;
- remove espaços no início e no final dos identificadores;
- transforma textos vazios em valores ausentes;
- converte `ano` para um tipo inteiro que admite valores ausentes;
- remove espaços externos de `anos_escolares`;
- converte os valores de `anos_escolares` para letras minúsculas.

Por exemplo, uma etapa registrada como `" Finais (6-9) "` passa a ser representada como `"finais (6-9)"`. Essa padronização reduz o risco de duas chaves equivalentes serem tratadas como diferentes apenas por causa da escrita.

### 5.5 Padronização e validação dos indicadores

A função `padronizar_e_validar_numericos_ideb` converte os indicadores do IDEB para valores numéricos e verifica seus domínios.

| Indicador | Intervalo aceito |
| --- | ---: |
| `taxa_aprovacao` | 0 a 100 |
| `indicador_rendimento` | 0 a 1 |
| `nota_saeb_media_padronizada` | 0 a 10 |
| `ideb` | 0 a 10 |
| `projecao`, quando presente | 0 a 10 |

Um texto que não possa ser convertido em número ou um valor fora do intervalo aceito interrompe o pipeline. Valores originalmente ausentes permanecem ausentes: não é realizada imputação pela média, substituição por zero ou qualquer outro preenchimento automático.

### 5.6 Aplicação do recorte temporal

A função `filtrar_anos` mantém somente os registros de 2019, 2021 e 2023. A quantidade de registros fora desse recorte é armazenada para inclusão no relatório de execução.

Se nenhum registro permanecer depois do filtro, o pipeline é interrompido. Nos arquivos atuais, as duas entradas já estavam limitadas aos três anos selecionados e, por isso, nenhum registro foi removido nessa etapa.

### 5.7 Validação das chaves originais

A função `validar_chave` verifica duas condições:

1. nenhuma das colunas da chave pode possuir valor ausente;
2. a combinação das colunas da chave não pode estar duplicada.

No Censo, a verificação é realizada por `id_escola + ano`. No IDEB, é realizada por `id_escola + ano + anos_escolares`.

### 5.8 Compatibilização da granularidade

A função `preparar_granularidade_censo` realiza a principal transformação estrutural do pipeline. Primeiro são extraídas do IDEB as combinações únicas de escola, ano e etapa. Em seguida, essas combinações são relacionadas ao Censo por escola e ano.

Considere uma escola com um único registro no Censo:

```text
id_escola = 100 | ano = 2023 | biblioteca = 1
```

Se o IDEB possuir resultados para duas etapas dessa escola:

```text
id_escola = 100 | ano = 2023 | anos_escolares = iniciais (1-5)
id_escola = 100 | ano = 2023 | anos_escolares = finais (6-9)
```

O Censo passa a ser representado na granularidade das duas etapas:

```text
id_escola = 100 | ano = 2023 | anos_escolares = iniciais (1-5) | biblioteca = 1
id_escola = 100 | ano = 2023 | anos_escolares = finais (6-9)   | biblioteca = 1
```

O atributo `biblioteca` é repetido porque descreve a escola naquele ano. Os resultados educacionais não são repetidos nessa etapa, pois ainda permanecem no arquivo do IDEB.

O relacionamento utilizado para levar o Censo à nova granularidade é validado como muitos-para-um: várias etapas do IDEB podem apontar para um único registro de escola e ano no Censo.

### 5.9 Auditoria das correspondências

Durante a compatibilização são calculadas três medidas:

- quantidade de chaves do IDEB sem registro correspondente no Censo;
- quantidade de escolas-ano do Censo sem observação correspondente no IDEB;
- quantidade de registros do Censo depois da expansão por etapa.

Essas medidas permitem distinguir uma expansão decorrente das diferentes etapas de uma exclusão provocada pela ausência de correspondência entre as fontes.

### 5.10 Integração final

A função `integrar` cruza o Censo expandido com o IDEB por meio da chave tripla:

```text
id_escola + ano + anos_escolares
```

O relacionamento é validado como 1:1. Isso significa que cada linha do Censo na granularidade escola-ano-etapa pode ser associada a apenas uma linha do IDEB e vice-versa.

Quando uma coluna existe nas duas fontes, são utilizados os sufixos `_censo` e `_ideb`. Por exemplo:

- `sigla_uf_censo` e `sigla_uf_ideb`;
- `id_municipio_censo` e `id_municipio_ideb`;
- `id_municipio_nome_censo` e `id_municipio_nome_ideb`.

Depois do cruzamento, estado e município são comparados. Uma divergência geográfica interrompe o pipeline, pois indicaria que o mesmo identificador de escola foi relacionado a localidades diferentes.

### 5.11 Validação e organização da saída

A chave tripla é validada novamente após a integração. Em seguida, suas três colunas são posicionadas no início da tabela, facilitando a identificação de cada observação.

O resultado mantém os atributos das duas fontes. Não são realizadas agregações, normalizações estatísticas, codificações de categorias ou imputações de valores ausentes.

### 5.12 Gravação dos resultados

O CSV e o relatório são inicialmente gravados em arquivos temporários. Somente depois que a escrita é concluída esses arquivos substituem os destinos definitivos.

Esse procedimento reduz o risco de deixar uma saída incompleta caso a execução seja interrompida durante a gravação. O relatório JSON registra o horário da execução, os caminhos utilizados, as contagens das entradas, os anos selecionados, as chaves, a auditoria do cruzamento e as verificações da saída.

## 6 Evidências da execução

O pipeline foi executado com os arquivos atuais do Censo Escolar e do IDEB. O relatório gerado apresenta os seguintes resultados:

| Medida | Resultado |
| --- | ---: |
| Registros recebidos do Censo | 240.386 |
| Registros recebidos do IDEB | 79.374 |
| Registros do Censo fora do recorte temporal | 0 |
| Registros do IDEB fora do recorte temporal | 0 |
| Chaves do IDEB sem correspondência no Censo | 0 |
| Escolas-ano do Censo sem correspondência no IDEB | 178.061 |
| Registros do Censo após expansão por etapa | 79.374 |
| Registros produzidos | 79.374 |
| Colunas produzidas | 61 |
| Duplicidades na chave final | 0 |
| Valores ausentes na chave final | 0 |

Dos 240.386 registros originais do Censo, 62.325 correspondem a pares de escola e ano que aparecem no IDEB. Depois da associação das etapas, esses registros passam a formar 79.374 observações. A diferença de 17.049 linhas representa etapas adicionais de ensino para escolas que possuem mais de um resultado no mesmo ano.

Os 178.061 registros de escola e ano do Censo sem observação no IDEB não fazem parte da base integrada. Isso ocorre porque a finalidade da saída é reunir as características do Censo com resultados educacionais efetivamente observados no IDEB.

Todas as 79.374 observações do IDEB encontraram correspondência no Censo. A base final não apresentou duplicidades nem valores ausentes na chave `id_escola + ano + anos_escolares`, confirmando que o relacionamento preservou a granularidade definida para o projeto.

As evidências completas e recalculáveis de cada execução ficam armazenadas em `data/processed/relatorio_execucao.json`.

## 7 Registro das principais decisões técnicas

Ao fazer a exeucução do pipeline, ficou mais claro ao tentar tornar o processo automático, alguns gargalos que antes não tão bem enxergados, como por exemplo, a necessidade de uma chave final definitiva como `id_escola + ano + anos_escolares`, pois escola e ano não identificam de forma única as observações do IDEB, já que na tabela IDEB são divididos por etapas do ensino. Além disso,
os anos, etapas e indicadores são padronizados antes do cruzamento para reduzir as diferenças no formato e não gerar conflito no momento do cruzamento das duas tabelas.

Quando temos valores ausentes nos indicadores eles ainda são preservados, a inputação automática se necessária, será definida em um futuro pipeline de acordo com os modelos de IA que serão utilizados.
Os atributos escolares são repetidos por etapa, mas os indicadores educacionais não são agregados nem recalculados, não é feito uma média entre ele por exemplo.
Outro ponto é que os identificadores estão sendo tratados como texto para preservar sua função de chave e evitar interpretação como medidas contínuas.

Não foram mantidas na tabela final, escolas do censo que não possuem correspodência na tabela IDEB, pois a ideia inicial é aplicar modelos não supervisionados para identificar padrões e semelhanças entre as escolas. 

 
 

 
