"""Agrupamento das escolas por perfil a partir da matriz gerada pelo pipeline 02.

A padronização, a ponderação por dimensão e o PCA são ajustados aqui, junto com o
modelo, usando todos os anos juntos. O IDEB não entra no agrupamento: ele é ligado
aos grupos depois, por etapa, para caracterizá-los.
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import HDBSCAN, AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import RobustScaler, StandardScaler


CHAVE_ESCOLA_ANO = ["id_escola", "ano"]
ETAPAS = {
    "iniciais (1-5)": "iniciais",
    "finais (6-9)": "finais",
    "todos (1-4)": "medio",
}

K_PADRAO = 6
FAIXA_K = range(2, 11)
VARIANCIA_PCA = 0.90
TAMANHO_AMOSTRA = 10_000
SEMENTE = 0

LOGGER = logging.getLogger("agrupamento")


@dataclass
class Preparacao:
    colunas: list[str]
    pesos: np.ndarray
    escalonador: StandardScaler | RobustScaler
    pca: PCA

    def transformar(self, df: pd.DataFrame) -> np.ndarray:
        return self.pca.transform(self.escalonador.transform(df[self.colunas]) * self.pesos)


def configurar_logs() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def carregar(
    matriz: Path, relatorio: Path, ligacao: Path
) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    for caminho in (matriz, relatorio, ligacao):
        if not caminho.is_file():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {caminho}. Execute antes o pipeline 02."
            )
    df = pd.read_csv(matriz, dtype={"id_escola": "string"})
    etapas = pd.read_csv(ligacao, dtype={"id_escola": "string"})
    auditoria = json.loads(relatorio.read_text(encoding="utf-8"))
    return df, auditoria, etapas


def selecionar_atributos(auditoria: dict, conjunto: str) -> dict[str, str]:
    """Retorna os atributos do conjunto escolhido e a dimensão de cada um.

    ``itens`` usa cada variável separadamente; ``indices`` troca as variáveis
    binárias cobertas por um índice pelo próprio índice da dimensão.
    """

    itens: dict[str, str] = auditoria["atributos_itens"]
    if conjunto == "itens":
        return dict(itens)
    if conjunto != "indices":
        raise ValueError(f"Conjunto de atributos desconhecido: {conjunto}")

    indices: dict[str, list[str]] = auditoria["atributos_indices"]
    cobertos = {item for componentes in indices.values() for item in componentes}
    atributos = {c: d for c, d in itens.items() if c not in cobertos}
    for indice in indices:
        atributos[indice] = indice.removeprefix("indice_")
    return atributos


def pesos_por_dimensao(atributos: dict[str, str]) -> np.ndarray:
    """Peso 1/√n por coluna, em que n é o número de colunas da sua dimensão."""

    contagem = pd.Series(atributos).value_counts()
    return np.array([1 / np.sqrt(contagem[d]) for d in atributos.values()])


def preparar(
    df: pd.DataFrame,
    atributos: dict[str, str],
    ponderar: bool = True,
    escalonador: str = "standard",
) -> tuple[np.ndarray, Preparacao]:
    colunas = list(atributos)
    pesos = pesos_por_dimensao(atributos) if ponderar else np.ones(len(colunas))
    modelo_escala = StandardScaler() if escalonador == "standard" else RobustScaler()
    escalado = modelo_escala.fit_transform(df[colunas]) * pesos
    pca = PCA(VARIANCIA_PCA, random_state=SEMENTE).fit(escalado)
    preparacao = Preparacao(colunas, pesos, modelo_escala, pca)
    return pca.transform(escalado), preparacao


def amostra_indices(n: int, tamanho: int = TAMANHO_AMOSTRA) -> np.ndarray:
    rng = np.random.default_rng(SEMENTE)
    return rng.choice(n, size=min(n, tamanho), replace=False)


def avaliar_k(z: np.ndarray, faixa: range = FAIXA_K) -> pd.DataFrame:
    """Calcula as métricas internas do K-Means para cada número de grupos."""

    amostra = amostra_indices(len(z))
    linhas = []
    for k in faixa:
        modelo = KMeans(k, n_init=10, random_state=SEMENTE).fit(z)
        rotulos = modelo.labels_
        linhas.append(
            {
                "k": k,
                "inercia": float(modelo.inertia_),
                # A silhueta é O(n²); por isso é calculada sobre uma amostra fixa.
                "silhueta": float(silhouette_score(z[amostra], rotulos[amostra])),
                "davies_bouldin": float(davies_bouldin_score(z, rotulos)),
                "calinski_harabasz": float(calinski_harabasz_score(z, rotulos)),
                "menor_grupo": int(np.bincount(rotulos).min()),
            }
        )
    return pd.DataFrame(linhas)


def ajustar_kmeans(z: np.ndarray, k: int) -> KMeans:
    return KMeans(k, n_init=10, random_state=SEMENTE).fit(z)


def ordenar_grupos(df: pd.DataFrame, rotulos: np.ndarray, coluna: str) -> np.ndarray:
    """Renumera os grupos em ordem crescente de ``coluna`` para facilitar a leitura."""

    medias = pd.Series(df[coluna].to_numpy()).groupby(rotulos).mean().sort_values()
    mapa = {antigo: novo for novo, antigo in enumerate(medias.index)}
    return np.vectorize(mapa.get)(rotulos)


def avaliar_estabilidade(
    df: pd.DataFrame, z: np.ndarray, rotulos: np.ndarray, k: int, repeticoes: int = 3
) -> dict:
    """ARI entre sementes, entre reamostragens e entre modelos ajustados em anos diferentes."""

    rng = np.random.default_rng(SEMENTE)
    sementes = [
        adjusted_rand_score(rotulos, KMeans(k, n_init=10, random_state=s).fit_predict(z))
        for s in range(1, repeticoes + 1)
    ]
    reamostragens = []
    for s in range(repeticoes):
        indices = rng.choice(len(z), size=len(z), replace=True)
        modelo = KMeans(k, n_init=10, random_state=s).fit(z[indices])
        reamostragens.append(adjusted_rand_score(rotulos, modelo.predict(z)))

    # Com um único ano (agrupamento separado por ano) não há comparação entre anos.
    anos = sorted(df["ano"].unique())
    entre_anos = {}
    for i, ano_origem in enumerate(anos):
        for ano_destino in anos[i + 1 :]:
            origem = ajustar_kmeans(z[df["ano"].to_numpy() == ano_origem], k)
            destino = ajustar_kmeans(z[df["ano"].to_numpy() == ano_destino], k)
            previsto = origem.predict(z[df["ano"].to_numpy() == ano_destino])
            entre_anos[f"{ano_origem}->{ano_destino}"] = float(
                adjusted_rand_score(destino.labels_, previsto)
            )

    return {
        "ari_entre_sementes": [round(float(v), 4) for v in sementes],
        "ari_entre_reamostragens": [round(float(v), 4) for v in reamostragens],
        "ari_entre_anos": {k_: round(v, 4) for k_, v in entre_anos.items()},
    }


def comparar_algoritmos(z: np.ndarray, rotulos: np.ndarray, k: int) -> dict:
    """Compara o K-Means com Ward e HDBSCAN em uma amostra fixa."""

    amostra = amostra_indices(len(z))
    ward = AgglomerativeClustering(k, linkage="ward").fit_predict(z[amostra])
    hdbscan = HDBSCAN(min_cluster_size=100, min_samples=20, copy=True).fit_predict(z[amostra])
    grupos_hdbscan = int(hdbscan.max() + 1)
    return {
        "tamanho_amostra": len(amostra),
        "ward": {
            "silhueta": round(float(silhouette_score(z[amostra], ward)), 4),
            "ari_com_kmeans": round(float(adjusted_rand_score(rotulos[amostra], ward)), 4),
        },
        "hdbscan": {
            "min_cluster_size": 100,
            "grupos": grupos_hdbscan,
            "fracao_ruido": round(float((hdbscan == -1).mean()), 4),
        },
    }


def comparar_escalonadores(
    df: pd.DataFrame, atributos: dict[str, str], rotulos: np.ndarray, k: int, ponderar: bool
) -> float:
    z_robusto, _ = preparar(df, atributos, ponderar, escalonador="robust")
    return round(float(adjusted_rand_score(rotulos, ajustar_kmeans(z_robusto, k).labels_)), 4)


def montar_perfis(
    df: pd.DataFrame, etapas: pd.DataFrame, atributos: list[str]
) -> pd.DataFrame:
    """Perfil médio dos atributos, composição do contexto e IDEB por grupo e etapa."""

    grupos = df.groupby("cluster")
    perfis = grupos[atributos].mean().add_prefix("media_")
    perfis.insert(0, "escolas_ano", grupos.size())
    perfis.insert(1, "matricula_mediana", grupos["matricula_total"].median())

    for coluna, prefixo in (("rede", "rede"), ("tipo_localizacao", "localizacao"), ("ano", "ano")):
        composicao = pd.crosstab(df["cluster"], df[coluna], normalize="index")
        composicao.columns = [f"prop_{prefixo}_{str(c).lower()}" for c in composicao.columns]
        perfis = perfis.join(composicao)

    imputacao = [c for c in df if c.endswith("_imputados") or c.endswith("_imputado")]
    perfis = perfis.join(grupos[imputacao].mean().add_prefix("prop_"))

    ideb = etapas.merge(df[CHAVE_ESCOLA_ANO + ["cluster"]], on=CHAVE_ESCOLA_ANO, how="inner")
    ideb["etapa"] = ideb["anos_escolares"].map(ETAPAS)
    resumo = ideb.groupby(["cluster", "etapa"])["ideb"].agg(["count", "mean", "median", "std"])
    resumo = resumo.unstack("etapa")
    resumo.columns = [f"ideb_{estatistica}_{etapa}" for estatistica, etapa in resumo.columns]
    resumo = resumo.rename(columns=lambda c: c.replace("ideb_count_", "n_etapa_"))
    return perfis.join(resumo).reset_index()


def descrever_grupos(perfis: pd.DataFrame, df: pd.DataFrame, atributos: list[str]) -> dict:
    """Resumo automático: os atributos mais acima e mais abaixo da média geral."""

    medias = perfis.set_index("cluster")[[f"media_{a}" for a in atributos]]
    medias.columns = atributos
    padronizado = (medias - df[atributos].mean()) / df[atributos].std()
    descricoes = {}
    for cluster, linha in padronizado.iterrows():
        ordenado = linha.sort_values()
        descricoes[int(cluster)] = {
            "acima_da_media": {a: round(float(v), 2) for a, v in ordenado[::-1][:3].items()},
            "abaixo_da_media": {a: round(float(v), 2) for a, v in ordenado[:3].items()},
        }
    return descricoes


def salvar_csv(df: pd.DataFrame, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    df.to_csv(temporario, index=False, encoding="utf-8")
    temporario.replace(caminho)


def salvar_json(dados: dict, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    temporario.replace(caminho)


def executar(
    matriz: Path,
    relatorio: Path,
    ligacao: Path,
    saida: Path,
    k: int,
    conjunto: str,
    ponderar: bool,
    ano: int | None = None,
) -> None:
    LOGGER.info("===== AGRUPAMENTO DAS ESCOLAS =====")
    df, auditoria, etapas = carregar(matriz, relatorio, ligacao)
    if ano is not None:
        df = df[df["ano"] == ano].reset_index(drop=True)
        etapas = etapas[etapas["ano"] == ano].reset_index(drop=True)
        if df.empty:
            raise ValueError(f"Nenhuma escola-ano encontrada para {ano}")
        saida = saida / str(ano)
        LOGGER.info("Agrupamento restrito ao ano %s: %s escolas", ano, f"{len(df):,}")
    atributos = selecionar_atributos(auditoria, conjunto)
    LOGGER.info("Conjunto '%s': %s atributos, ponderação por dimensão: %s", conjunto, len(atributos), ponderar)

    z, preparacao = preparar(df, atributos, ponderar)
    LOGGER.info("PCA: %s componentes explicam %.0f%% da variância", preparacao.pca.n_components_, 100 * VARIANCIA_PCA)

    metricas_k = avaliar_k(z)
    LOGGER.info("Métricas calculadas para k de %s a %s", FAIXA_K.start, FAIXA_K.stop - 1)

    modelo = ajustar_kmeans(z, k)
    rotulos = ordenar_grupos(df, modelo.labels_, "indice_tecnologia" if conjunto == "indices" else "porte_log")
    df = df.assign(cluster=rotulos)
    LOGGER.info("K-Means ajustado com k=%s: tamanhos %s", k, np.bincount(rotulos).tolist())

    estabilidade = avaliar_estabilidade(df, z, rotulos, k)
    algoritmos = comparar_algoritmos(z, rotulos, k)
    ari_robusto = comparar_escalonadores(df, atributos, rotulos, k, ponderar)
    LOGGER.info("Estabilidade: %s", estabilidade)

    perfis = montar_perfis(df, etapas, list(atributos))
    descricoes = descrever_grupos(perfis, df, list(atributos))

    salvar_csv(df[CHAVE_ESCOLA_ANO + ["cluster"]], saida / "atribuicoes.csv")
    salvar_csv(perfis, saida / "perfis_clusters.csv")
    salvar_json(
        {
            "executado_em_utc": datetime.now(timezone.utc).isoformat(),
            "entrada": str(matriz),
            "anos": sorted(int(a) for a in df["ano"].unique()),
            "escolas_ano": len(df),
            "conjunto_atributos": conjunto,
            "atributos": atributos,
            "ponderacao_por_dimensao": ponderar,
            "escalonador": (
                "StandardScaler ajustado com todos os anos"
                if ano is None
                else f"StandardScaler ajustado só com {ano}"
            ),
            "pca": {
                "variancia_alvo": VARIANCIA_PCA,
                "componentes": int(preparacao.pca.n_components_),
            },
            "k_escolhido": k,
            "silhueta_k_escolhido": round(
                float(metricas_k.set_index("k").loc[k, "silhueta"]), 4
            ) if k in metricas_k["k"].values else None,
            "tamanhos_grupos": np.bincount(rotulos).tolist(),
            "metricas_por_k": metricas_k.round(4).to_dict(orient="records"),
            "estabilidade": estabilidade,
            "comparacao_algoritmos": algoritmos,
            "ari_standard_vs_robust": ari_robusto,
            "descricao_grupos": descricoes,
        },
        saida / "metricas.json",
    )
    LOGGER.info("Resultados gravados em %s", saida)
    LOGGER.info("===== AGRUPAMENTO FINALIZADO =====")


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agrupa as escolas por perfil (K-Means).")
    parser.add_argument("--matriz", type=Path, default=Path("data/processed/atributos_escola_ano.csv"))
    parser.add_argument("--relatorio", type=Path, default=Path("data/processed/relatorio_atributos.json"))
    parser.add_argument("--ligacao", type=Path, default=Path("data/processed/ligacao_etapas.csv"))
    parser.add_argument("--saida", type=Path, default=Path("data/processed/agrupamento"))
    parser.add_argument("--k", type=int, default=K_PADRAO, help="Número de grupos")
    parser.add_argument("--conjunto", choices=["indices", "itens"], default="indices")
    parser.add_argument(
        "--sem-ponderacao",
        action="store_true",
        help="Não pondera as colunas por 1/√(número de colunas da dimensão)",
    )
    parser.add_argument(
        "--ano",
        type=int,
        help="Agrupa só as escolas deste ano e grava os resultados em <saida>/<ano>/",
    )
    return parser


def main() -> None:
    configurar_logs()
    argumentos = criar_parser().parse_args()
    try:
        executar(
            argumentos.matriz,
            argumentos.relatorio,
            argumentos.ligacao,
            argumentos.saida,
            argumentos.k,
            argumentos.conjunto,
            not argumentos.sem_ponderacao,
            argumentos.ano,
        )
    except (FileNotFoundError, ValueError) as erro:
        LOGGER.error("Agrupamento interrompido: %s", erro)
        raise SystemExit(1) from erro


if __name__ == "__main__":
    main()
