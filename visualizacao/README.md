# Visualização

Esta pasta reúne as etapas de visualização geográfica do projeto: mapas que situam as escolas e os municípios do Nordeste e mostram onde se concentram os grupos de perfil e os resultados do IDEB.

## Entradas

| Arquivo | Conteúdo |
| --- | --- |
| `data/escolas_coordenadas_nordeste.csv` | Latitude e longitude de cada escola (22.928 das 26.233 escolas da análise, 87,4%) |
| `data/processed/atributos_escola_ano.csv` | Município, rede, localização e porte de cada escola-ano |
| `data/processed/ligacao_etapas.csv` | IDEB de cada escola por ano e etapa |
| `data/processed/agrupamento/atribuicoes.csv` | Grupo de cada escola-ano no agrupamento conjunto |
| `data/processed/agrupamento/<ano>/atribuicoes.csv` | Grupo de cada escola no agrupamento feito só com aquele ano |

## Etapas

| Etapa | Arquivo previsto | Situação |
| --- | --- | --- |
| 1. Preparar as tabelas do mapa (escolas e municípios) | `preparar_dados_mapa.py` | Concluída |
| 2. Mapa por município | `mapa_municipios.html` (gerado a partir de `modelo_mapa.html`) | Concluída |
| 3. Camada de escolas | no mesmo mapa, visível a partir do zoom 10 | Concluída |
| 4. Versão estática para o relatório | notebook `notebooks/04_mapas.ipynb` | A fazer |

As tabelas geradas na etapa 1 ficam em `data/processed/visualizacao/`, seguindo a separação entre código e dados adotada no restante do repositório.

## Como gerar e abrir o mapa

A partir da raiz do repositório, depois do pipeline 02 e do agrupamento conjunto:

```bash
python visualizacao/preparar_dados_mapa.py
```

O comando grava `escolas_mapa.csv`, `municipios_mapa.csv` e `relatorio_mapa.json` em `data/processed/visualizacao/` e gera `visualizacao/mapa_municipios.html` (cerca de 7 MB, com os dados embutidos). A página abre direto no navegador, sem servidor; só o mapa de fundo (camada cinza da Esri, com dados do OpenStreetMap) e a biblioteca Leaflet são baixados da internet. O fundo do próprio OpenStreetMap não foi usado porque o servidor dele bloqueia páginas abertas como arquivo local ("Access blocked"). Se o fundo não carregar, a página o remove e mostra um aviso, e os dados continuam visíveis.

Na página:

- **Indicador:** alterna entre **IDEB** (mediana do município na etapa escolhida) e **Grupos** (% das escolas do município no grupo escolhido). Os grupos são os do agrupamento conjunto.
- **Ano:** 2019, 2021 ou 2023.
- **Zoom 10 ou mais:** mostra as escolas. No IDEB, a cor é o IDEB da própria escola; em Grupos, as escolas do grupo escolhido ficam em destaque e as demais em cinza.
- **Destaque P10 / P90 (em Grupos):** mostra as escolas do grupo escolhido com IDEB abaixo do percentil 10 (vermelho) ou acima do percentil 90 (violeta) entre as escolas do mesmo **grupo, etapa e ano**. As duas cores são fixas e iguais em todos os grupos. As escolas destacadas aparecem em qualquer zoom; a partir do zoom 10, as demais escolas do grupo aparecem em cinza. O botão permite ver as duas faixas, só a de baixo ou só a de cima, e a etapa é escolhida no seletor de etapa. Os limites de cada combinação estão em `data/processed/visualizacao/limites_percentis.csv`; combinações com menos de 30 escolas não são classificadas (grupo 3 no ensino médio em 2019 e 2021).
- **Painel lateral:** detalhe do município ou da escola sob o mouse, legenda e os 10 municípios com maiores ou menores valores (só municípios com pelo menos 5 escolas).

As cores usam faixas fixas, iguais nos três anos, para que os anos possam ser comparados: no IDEB, os limites aproximam os quintis das medianas municipais; em Grupos, as faixas são nenhuma escola, até 15%, 15 a 30%, 30 a 50% e 50% ou mais.

## Pontos de atenção

- **Cobertura das escolas:** 12,6% das escolas não têm coordenada, concentradas na Bahia (72,4% de cobertura) e na zona rural (83,8%). No mapa por escola essas regiões ficam sub-representadas.
- **Posição dos municípios:** calculada como a mediana das coordenadas das escolas do município, a mesma nos três anos. 12 dos 1.794 municípios (156 escolas-ano) não têm nenhuma escola com coordenada e ficam de fora do mapa por enquanto; a lista está em `relatorio_mapa.json`.
- **IDEB igual a 10:** existem nos dados (por exemplo, escolas de Mucambo e Pires Ferreira, no Ceará, em 2023, com aprovação de 100% e nota padronizada do Saeb no teto). São candidatos naturais para a detecção de anomalias.
- **IDEB de 2021:** não é comparável com os outros anos por causa da aprovação quase universal durante a pandemia.
