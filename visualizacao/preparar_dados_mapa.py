"""Prepara as tabelas e a página do mapa de escolas e municípios do Nordeste.

Junta as coordenadas das escolas com o agrupamento conjunto (três anos juntos) e com o
IDEB por etapa. Gera duas tabelas em ``data/processed/visualizacao/`` e a página
``visualizacao/mapa_municipios.html``, com os dados embutidos para que ela abra direto
no navegador, sem servidor.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


CHAVE_ESCOLA_ANO = ["id_escola", "ano"]
ETAPAS = {
    "iniciais (1-5)": "iniciais",
    "finais (6-9)": "finais",
    "todos (1-4)": "medio",
}
NOMES_GRUPOS = {
    0: "Recursos mínimos",
    1: "Espaços sem tecnologia",
    2: "Materiais sem tecnologia",
    3: "Apoio multiprofissional",
    4: "Tecnologia sem espaços",
    5: "Estrutura completa",
}
MARCADOR_DADOS = "/*__DADOS_MAPA__*/null"

# Escolas abaixo do percentil 10 ou acima do percentil 90 do IDEB, dentro de grupo × etapa × ano.
PERCENTIL_INFERIOR = 0.10
PERCENTIL_SUPERIOR = 0.90
# Abaixo deste número de escolas os percentis não são calculados (ex.: grupo 3 no ensino médio).
MINIMO_ESCOLAS_PERCENTIL = 30
CODIGO_FAIXA = {"abaixo": -1, "meio": 0, "acima": 1, "nao_classificado": 9}

LOGGER = logging.getLogger("visualizacao")


def configurar_logs() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def ler(caminho: Path) -> pd.DataFrame:
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    # Códigos de escola e de município são lidos como texto para o cruzamento entre arquivos.
    tipos = {c: "string" for c in ("id_escola", "id_municipio", "id_municipio_censo")}
    return pd.read_csv(caminho, dtype=tipos)


def ideb_por_etapa(ligacao: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por escola-ano, com o IDEB de cada etapa em colunas."""

    ideb = ligacao.assign(etapa=ligacao["anos_escolares"].map(ETAPAS))
    largo = ideb.pivot_table(index=CHAVE_ESCOLA_ANO, columns="etapa", values="ideb")
    largo = largo.reindex(columns=list(ETAPAS.values())).add_prefix("ideb_")
    largo.columns.name = None
    return largo.reset_index()


def montar_escolas(
    atributos: pd.DataFrame,
    grupos: pd.DataFrame,
    ligacao: pd.DataFrame,
    coordenadas: pd.DataFrame,
) -> pd.DataFrame:
    """Todas as escolas-ano da análise, com grupo, IDEB por etapa e coordenadas (quando houver)."""

    escolas = atributos[
        CHAVE_ESCOLA_ANO + ["sigla_uf_censo", "id_municipio_censo", "rede", "tipo_localizacao", "matricula_total"]
    ].rename(columns={"sigla_uf_censo": "sigla_uf", "id_municipio_censo": "id_municipio"})
    escolas["id_municipio"] = escolas["id_municipio"].astype("string")

    escolas = escolas.merge(grupos, on=CHAVE_ESCOLA_ANO, how="left", validate="one_to_one")
    if escolas["cluster"].isna().any():
        raise ValueError("Há escolas-ano sem grupo no agrupamento conjunto")

    escolas = escolas.merge(ideb_por_etapa(ligacao), on=CHAVE_ESCOLA_ANO, how="left", validate="one_to_one")

    coordenadas = coordenadas.rename(
        columns={"id_escola_latitude": "latitude", "id_escola_longitude": "longitude"}
    )[["id_escola", "id_escola_nome", "id_municipio_nome", "latitude", "longitude"]]
    escolas = escolas.merge(coordenadas, on="id_escola", how="left", validate="many_to_one")
    return escolas.sort_values(CHAVE_ESCOLA_ANO).reset_index(drop=True)


def classificar_percentis(escolas: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Classifica o IDEB de cada escola em relação aos pares do mesmo grupo, etapa e ano.

    ``abaixo``: IDEB menor ou igual ao percentil 10; ``acima``: maior ou igual ao
    percentil 90; ``meio``: entre os dois. Os percentis usam todas as escolas da
    combinação, inclusive as sem coordenada. Combinações com menos de
    ``MINIMO_ESCOLAS_PERCENTIL`` escolas ficam como ``nao_classificado``.
    """

    resultado = escolas.copy()
    limites = []
    for etapa in ETAPAS.values():
        coluna = f"ideb_{etapa}"
        faixa = pd.Series(pd.NA, index=resultado.index, dtype="string")
        for (cluster, ano), linhas in resultado.dropna(subset=[coluna]).groupby(["cluster", "ano"]):
            valores = linhas[coluna]
            if len(valores) < MINIMO_ESCOLAS_PERCENTIL:
                faixa.loc[linhas.index] = "nao_classificado"
                limites.append({"cluster": cluster, "ano": ano, "etapa": etapa, "escolas": len(valores),
                                "p10": None, "p90": None, "abaixo": 0, "acima": 0})
                continue
            p10, p90 = valores.quantile([PERCENTIL_INFERIOR, PERCENTIL_SUPERIOR])
            faixa.loc[linhas.index] = "meio"
            faixa.loc[valores.index[valores <= p10]] = "abaixo"
            faixa.loc[valores.index[valores >= p90]] = "acima"
            limites.append({"cluster": cluster, "ano": ano, "etapa": etapa, "escolas": len(valores),
                            "p10": round(float(p10), 2), "p90": round(float(p90), 2),
                            "abaixo": int((valores <= p10).sum()), "acima": int((valores >= p90).sum())})
        resultado[f"faixa_{etapa}"] = faixa
    return resultado, pd.DataFrame(limites).sort_values(["ano", "cluster", "etapa"]).reset_index(drop=True)


def codigo_faixa(valor) -> int | None:
    return None if pd.isna(valor) else CODIGO_FAIXA[valor]


def montar_municipios(escolas: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Resumo por município e ano.

    As contagens, a composição dos grupos e o IDEB usam todas as escolas do município,
    inclusive as sem coordenada. A posição é a mediana das coordenadas das escolas do
    município (cada escola contada uma vez, em qualquer ano) e é a mesma nos três anos;
    municípios sem nenhuma escola com coordenada ficam de fora.
    """

    chave = ["id_municipio", "ano"]
    grupo = escolas.groupby(chave)

    resumo = grupo.agg(
        sigla_uf=("sigla_uf", "first"),
        escolas=("id_escola", "size"),
        escolas_com_coordenada=("latitude", "count"),
        **{f"ideb_{etapa}": (f"ideb_{etapa}", "median") for etapa in ETAPAS.values()},
        **{f"n_{etapa}": (f"ideb_{etapa}", "count") for etapa in ETAPAS.values()},
    )

    composicao = pd.crosstab(
        [escolas["id_municipio"], escolas["ano"]], escolas["cluster"], normalize="index"
    ).reindex(columns=list(NOMES_GRUPOS), fill_value=0)
    composicao.columns = [f"prop_grupo_{c}" for c in composicao.columns]
    resumo = resumo.join(composicao)

    localizadas = escolas.dropna(subset=["latitude"]).drop_duplicates("id_escola")
    posicao = localizadas.groupby("id_municipio").agg(
        id_municipio_nome=("id_municipio_nome", "first"),
        latitude=("latitude", "median"),
        longitude=("longitude", "median"),
    )
    resumo = resumo.reset_index().merge(posicao, on="id_municipio", how="left")
    resumo.insert(1, "id_municipio_nome", resumo.pop("id_municipio_nome"))

    sem_posicao = resumo["latitude"].isna()
    excluidos = (
        resumo.loc[sem_posicao]
        .groupby("id_municipio")
        .agg(sigla_uf=("sigla_uf", "first"), anos=("ano", list), escolas=("escolas", "sum"))
        .reset_index()
        .to_dict(orient="records")
    )
    return resumo.loc[~sem_posicao].reset_index(drop=True), excluidos


def arredondar(valor: float, casas: int) -> float | None:
    return None if pd.isna(valor) else round(float(valor), casas)


def dados_da_pagina(escolas: pd.DataFrame, municipios: pd.DataFrame, limites: pd.DataFrame) -> dict:
    """Estrutura compacta embutida na página: listas em vez de objetos repetidos."""

    lista_municipios = []
    for (id_municipio, nome, uf), linhas in municipios.groupby(
        ["id_municipio", "id_municipio_nome", "sigla_uf"], dropna=False
    ):
        primeira = linhas.iloc[0]
        anos = {}
        for _, linha in linhas.iterrows():
            anos[str(int(linha["ano"]))] = {
                "e": int(linha["escolas"]),
                "c": int(linha["escolas_com_coordenada"]),
                "g": [arredondar(linha[f"prop_grupo_{g}"], 3) for g in NOMES_GRUPOS],
                "i": [arredondar(linha[f"ideb_{e}"], 2) for e in ETAPAS.values()],
                "n": [int(linha[f"n_{e}"]) for e in ETAPAS.values()],
            }
        lista_municipios.append(
            {
                "id": id_municipio,
                "nome": nome if isinstance(nome, str) else id_municipio,
                "uf": uf,
                "lat": arredondar(primeira["latitude"], 5),
                "lon": arredondar(primeira["longitude"], 5),
                "anos": anos,
            }
        )

    localizadas = escolas.dropna(subset=["latitude"])
    lista_escolas = [
        [
            linha.id_escola,
            linha.id_escola_nome if isinstance(linha.id_escola_nome, str) else "",
            int(linha.ano),
            round(float(linha.latitude), 5),
            round(float(linha.longitude), 5),
            linha.rede,
            linha.tipo_localizacao,
            int(linha.cluster),
            arredondar(linha.ideb_iniciais, 1),
            arredondar(linha.ideb_finais, 1),
            arredondar(linha.ideb_medio, 1),
            linha.id_municipio,
            codigo_faixa(linha.faixa_iniciais),
            codigo_faixa(linha.faixa_finais),
            codigo_faixa(linha.faixa_medio),
        ]
        for linha in localizadas.itertuples(index=False)
    ]
    ordem_etapas = list(ETAPAS.values())
    lista_limites = [
        [int(l.ano), int(l.cluster), ordem_etapas.index(l.etapa), arredondar(l.p10, 2), arredondar(l.p90, 2), int(l.escolas)]
        for l in limites.itertuples(index=False)
    ]

    return {
        "grupos": [NOMES_GRUPOS[g] for g in NOMES_GRUPOS],
        "etapas": ["Anos iniciais", "Anos finais", "Ensino médio"],
        "anos": sorted(int(a) for a in escolas["ano"].unique()),
        "municipios": lista_municipios,
        "escolas": lista_escolas,
        "limites": lista_limites,
        "minimoPercentil": MINIMO_ESCOLAS_PERCENTIL,
    }


def gerar_pagina(modelo: Path, saida: Path, dados: dict) -> None:
    html = modelo.read_text(encoding="utf-8")
    if MARCADOR_DADOS not in html:
        raise ValueError(f"Marcador {MARCADOR_DADOS!r} não encontrado em {modelo}")
    conteudo = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    saida.write_text(html.replace(MARCADOR_DADOS, conteudo), encoding="utf-8")


def salvar_csv(df: pd.DataFrame, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho, index=False, encoding="utf-8")


def executar(processados: Path, coordenadas: Path, modelo: Path, pagina: Path) -> None:
    LOGGER.info("===== PREPARAÇÃO DO MAPA =====")
    atributos = ler(processados / "atributos_escola_ano.csv")
    grupos = ler(processados / "agrupamento" / "atribuicoes.csv")
    ligacao = ler(processados / "ligacao_etapas.csv")
    coords = ler(coordenadas)
    coords = coords.dropna(subset=["id_escola_latitude", "id_escola_longitude"])

    escolas = montar_escolas(atributos, grupos, ligacao, coords)
    escolas, limites = classificar_percentis(escolas)
    municipios, excluidos = montar_municipios(escolas)
    LOGGER.info(
        "Escolas-ano: %s, com coordenada: %s (%.1f%%)",
        f"{len(escolas):,}",
        f"{escolas['latitude'].notna().sum():,}",
        100 * escolas["latitude"].notna().mean(),
    )
    LOGGER.info(
        "Municípios no mapa: %s; deixados de fora por não terem escola com coordenada: %s",
        municipios["id_municipio"].nunique(),
        len(excluidos),
    )

    destino = processados / "visualizacao"
    salvar_csv(escolas, destino / "escolas_mapa.csv")
    salvar_csv(municipios, destino / "municipios_mapa.csv")
    salvar_csv(limites, destino / "limites_percentis.csv")
    (destino / "relatorio_mapa.json").write_text(
        json.dumps(
            {
                "executado_em_utc": datetime.now(timezone.utc).isoformat(),
                "agrupamento": "conjunto (três anos juntos)",
                "escolas_ano": len(escolas),
                "escolas_ano_com_coordenada": int(escolas["latitude"].notna().sum()),
                "municipios_no_mapa": int(municipios["id_municipio"].nunique()),
                "posicao_do_municipio": "mediana das coordenadas das escolas do município",
                "municipios_excluidos_sem_coordenada": excluidos,
                "percentis": {
                    "inferior": PERCENTIL_INFERIOR,
                    "superior": PERCENTIL_SUPERIOR,
                    "recorte": "grupo × etapa × ano",
                    "minimo_escolas": MINIMO_ESCOLAS_PERCENTIL,
                    "escolas_etapa_abaixo": int(limites["abaixo"].sum()),
                    "escolas_etapa_acima": int(limites["acima"].sum()),
                    "combinacoes_nao_classificadas": limites.loc[limites["p10"].isna(), ["cluster", "ano", "etapa", "escolas"]].to_dict(orient="records"),
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    gerar_pagina(modelo, pagina, dados_da_pagina(escolas, municipios, limites))
    LOGGER.info("Tabelas gravadas em %s", destino)
    LOGGER.info("Página gerada: %s (%.1f MB)", pagina, pagina.stat().st_size / 1e6)
    LOGGER.info("===== PREPARAÇÃO FINALIZADA =====")


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepara as tabelas e a página do mapa.")
    parser.add_argument("--processados", type=Path, default=Path("data/processed"))
    parser.add_argument("--coordenadas", type=Path, default=Path("data/escolas_coordenadas_nordeste.csv"))
    parser.add_argument("--modelo", type=Path, default=Path("visualizacao/modelo_mapa.html"))
    parser.add_argument("--pagina", type=Path, default=Path("visualizacao/mapa_municipios.html"))
    return parser


def main() -> None:
    configurar_logs()
    argumentos = criar_parser().parse_args()
    try:
        executar(argumentos.processados, argumentos.coordenadas, argumentos.modelo, argumentos.pagina)
    except (FileNotFoundError, ValueError) as erro:
        LOGGER.error("Preparação interrompida: %s", erro)
        raise SystemExit(1) from erro


if __name__ == "__main__":
    main()
