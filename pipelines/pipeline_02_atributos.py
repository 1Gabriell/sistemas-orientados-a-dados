"""Pipeline 02 de preparação da matriz de atributos para o agrupamento das escolas.

Lê a base integrada gerada pelo pipeline 01, sem alterá-la, e produz uma matriz com
uma linha por escola e ano. A padronização e o PCA não são feitos aqui: a matriz
mantém a escala original para que os grupos possam ser interpretados.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


CHAVE_ESCOLA_ANO = ["id_escola", "ano"]
CHAVE_ETAPA = ["id_escola", "ano", "anos_escolares"]

COLUNAS_CONTEXTO = ["sigla_uf_censo", "id_municipio_censo", "rede", "tipo_localizacao"]

BINARIAS_CENSO = [
    "agua_potavel",
    "agua_rede_publica",
    "energia_rede_publica",
    "esgoto_rede_publica",
    "lixo_servico_coleta",
    "area_verde",
    "banheiro_chuveiro",
    "biblioteca",
    "cozinha",
    "dormitorio_aluno",
    "laboratorio_ciencias",
    "laboratorio_informatica",
    "laboratorio_educacao_profissional",
    "quadra_esportes",
    "refeitorio",
    "sala_leitura",
    "desktop_aluno",
    "internet_alunos",
    "profissional_assistente_social",
    "alimentacao",
    "material_pedagogico_multimidia",
    "material_pedagogico_infantil",
    "material_pedagogico_cientifico",
    "material_pedagogico_musical",
    "material_pedagogico_artistica",
    "orgao_gremio_estudantil",
    "diurno",
    "noturno",
]

# Profissionais raros, muitas vezes compartilhados pela rede: a razão por aluno ficaria
# inflada em escolas pequenas, então entram como presença (tem / não tem).
PROFISSIONAIS_PRESENCA = {
    "quantidade_profissional_saude": "tem_profissional_saude",
    "quantidade_profissional_nutricionista": "tem_nutricionista",
    "quantidade_profissional_psicologo": "tem_psicologo",
}
PROFISSIONAIS_RAZAO = {
    "quantidade_profissional_pedagogia": "profissional_pedagogia_100_alunos",
}
PROFISSIONAIS = {**PROFISSIONAIS_PRESENCA, **PROFISSIONAIS_RAZAO}

MATRICULAS_SEXO = ["quantidade_matricula_feminino", "quantidade_matricula_masculino"]
MATRICULAS_RACA = {
    "quantidade_matricula_branca": "prop_raca_branca",
    "quantidade_matricula_preta": "prop_raca_preta",
    "quantidade_matricula_parda": "prop_raca_parda",
    "quantidade_matricula_amarela": "prop_raca_amarela",
    "quantidade_matricula_indigena": "prop_raca_indigena",
    "quantidade_matricula_nao_declarada": "prop_raca_nao_declarada",
}

CONTAGENS_CENSO = [
    "quantidade_sala_utilizada_climatizada",
    *PROFISSIONAIS,
    *MATRICULAS_SEXO,
    *MATRICULAS_RACA,
    "quantidade_matricula_utiliza_transporte_publico",
]

ATRIBUTOS_CENSO = BINARIAS_CENSO + CONTAGENS_CENSO

RESULTADOS_IDEB = [
    "ensino",
    "taxa_aprovacao",
    "indicador_rendimento",
    "nota_saeb_media_padronizada",
    "ideb",
    "projecao",
]

ETAPAS = {
    "iniciais (1-5)": "oferece_iniciais",
    "finais (6-9)": "oferece_finais",
    "todos (1-4)": "oferece_medio",
}

# Variáveis que o Censo não coletou em todos os anos do recorte (ausência estrutural).
COLUNAS_EXCLUIDAS_PADRAO = [
    "laboratorio_educacao_profissional",
    "quantidade_matricula_utiliza_transporte_publico",
    "profissional_assistente_social",
]

# Colunas imputadas que compartilham o mesmo indicador de imputação.
INDICADORES_IMPUTACAO = {
    "material_pedagogico_multimidia": "materiais_imputados",
    "material_pedagogico_infantil": "materiais_imputados",
    "material_pedagogico_cientifico": "materiais_imputados",
    "material_pedagogico_musical": "materiais_imputados",
    "material_pedagogico_artistica": "materiais_imputados",
    "orgao_gremio_estudantil": "gremio_imputado",
    **{coluna: "profissionais_imputados" for coluna in PROFISSIONAIS},
}

GRUPO_PARES = ["ano", "rede", "tipo_localizacao"]

# Índices por dimensão: proporção dos itens presentes, de 0 a 1.
DIMENSOES_INDICES = {
    "indice_infraestrutura_basica": [
        "agua_potavel",
        "agua_rede_publica",
        "energia_rede_publica",
        "esgoto_rede_publica",
        "lixo_servico_coleta",
        "banheiro_chuveiro",
        "cozinha",
        "refeitorio",
    ],
    "indice_espacos_pedagogicos": [
        "biblioteca",
        "sala_leitura",
        "laboratorio_ciencias",
        "quadra_esportes",
        "area_verde",
    ],
    "indice_tecnologia": ["laboratorio_informatica", "desktop_aluno", "internet_alunos"],
    "indice_materiais": [
        "material_pedagogico_multimidia",
        "material_pedagogico_infantil",
        "material_pedagogico_cientifico",
        "material_pedagogico_musical",
        "material_pedagogico_artistica",
    ],
}

# Dimensão de cada atributo da matriz, usada na ponderação e na escolha do conjunto.
DIMENSAO_DOS_ITENS = {
    **{item: "infraestrutura_basica" for item in DIMENSOES_INDICES["indice_infraestrutura_basica"]},
    **{item: "espacos_pedagogicos" for item in DIMENSOES_INDICES["indice_espacos_pedagogicos"]},
    **{item: "tecnologia" for item in DIMENSOES_INDICES["indice_tecnologia"]},
    **{item: "materiais" for item in DIMENSOES_INDICES["indice_materiais"]},
    "dormitorio_aluno": "infraestrutura_basica",
    "alimentacao": "infraestrutura_basica",
    "salas_climatizadas_log": "infraestrutura_basica",
    "orgao_gremio_estudantil": "gestao_e_oferta",
    "diurno": "gestao_e_oferta",
    "noturno": "gestao_e_oferta",
    "oferece_iniciais": "gestao_e_oferta",
    "oferece_finais": "gestao_e_oferta",
    "oferece_medio": "gestao_e_oferta",
    **{nova: "recursos_humanos" for nova in PROFISSIONAIS.values()},
    "porte_log": "porte_e_composicao",
    "prop_feminino": "porte_e_composicao",
    **{nova: "porte_e_composicao" for nova in MATRICULAS_RACA.values()},
}

LIMIAR_QUASE_CONSTANTE_PADRAO = 0.98
PERCENTIS_WINSORIZACAO = (0.01, 0.99)

LOGGER = logging.getLogger("pipeline_02")


class ErroValidacao(ValueError):
    """Erro que impede a geração de uma matriz de atributos confiável."""


def configurar_logs() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def validar_colunas(df: pd.DataFrame, obrigatorias: Iterable[str], nome: str) -> None:
    ausentes = sorted(set(obrigatorias) - set(df.columns))
    if ausentes:
        raise ErroValidacao(
            f"{nome}: colunas obrigatórias ausentes: {', '.join(ausentes)}"
        )


def ler_base_integrada(caminho: Path) -> pd.DataFrame:
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {caminho}")

    df = pd.read_csv(caminho, dtype={"id_escola": "string"}, low_memory=False)
    LOGGER.info("Base integrada carregada: %s registros × %s colunas", f"{len(df):,}", len(df.columns))
    return df


def validar_censo_igual_entre_etapas(base: pd.DataFrame) -> int:
    """Confirma que os atributos do Censo se repetem sem variação entre as etapas.

    Retorna o número de escolas-ano que aparecem em mais de uma etapa.
    """

    colunas = [c for c in COLUNAS_CONTEXTO + ATRIBUTOS_CENSO if c in base]
    variacoes = base.groupby(CHAVE_ESCOLA_ANO)[colunas].nunique(dropna=False).max(axis=1)
    divergentes = int((variacoes > 1).sum())
    if divergentes:
        raise ErroValidacao(
            f"{divergentes} escolas-ano têm atributos do Censo diferentes entre etapas"
        )
    return int((base.groupby(CHAVE_ESCOLA_ANO).size() > 1).sum())


def criar_indicadores_etapas(base: pd.DataFrame) -> pd.DataFrame:
    desconhecidas = sorted(set(base["anos_escolares"].dropna()) - set(ETAPAS))
    if desconhecidas:
        raise ErroValidacao(f"Etapas desconhecidas em anos_escolares: {desconhecidas}")

    indicadores = (
        pd.crosstab([base["id_escola"], base["ano"]], base["anos_escolares"])
        .reindex(columns=list(ETAPAS), fill_value=0)
        .clip(upper=1)
        .rename(columns=ETAPAS)
        .astype(int)
        .reset_index()
    )
    indicadores.columns.name = None
    return indicadores


def remover_duplicacao(base: pd.DataFrame) -> pd.DataFrame:
    colunas = CHAVE_ESCOLA_ANO + [c for c in COLUNAS_CONTEXTO + ATRIBUTOS_CENSO if c in base]
    escola_ano = base[colunas].drop_duplicates(CHAVE_ESCOLA_ANO).reset_index(drop=True)
    escola_ano = escola_ano.merge(
        criar_indicadores_etapas(base), on=CHAVE_ESCOLA_ANO, how="left", validate="one_to_one"
    )
    return escola_ano.sort_values(CHAVE_ESCOLA_ANO).reset_index(drop=True)


def separar_ligacao_etapas(base: pd.DataFrame) -> pd.DataFrame:
    colunas = CHAVE_ETAPA + [c for c in RESULTADOS_IDEB if c in base]
    return base[colunas].sort_values(CHAVE_ETAPA).reset_index(drop=True)


def imputar_pela_propria_escola(df: pd.DataFrame, coluna: str) -> tuple[pd.Series, pd.Series]:
    """Preenche a coluna com o valor da mesma escola no ano mais próximo.

    Em caso de empate na distância, usa o ano anterior. Retorna a coluna preenchida
    e a máscara das linhas preenchidas nesta etapa.
    """

    valores = df[coluna].copy()
    ausentes_antes = valores.isna()
    observados = df.loc[df[coluna].notna()].pivot(index="id_escola", columns="ano", values=coluna)
    anos = sorted(df["ano"].unique())

    for ano in anos:
        alvo = ausentes_antes & (df["ano"] == ano)
        if not alvo.any():
            continue
        candidatos = sorted((a for a in anos if a != ano), key=lambda a: (abs(a - ano), a))
        for candidato in candidatos:
            if candidato not in observados:
                continue
            pendente = alvo & valores.isna()
            if not pendente.any():
                break
            valores.loc[pendente] = df.loc[pendente, "id_escola"].map(observados[candidato])

    return valores, ausentes_antes & valores.notna()


def imputar_pelos_pares(df: pd.DataFrame, coluna: str, binaria: bool) -> pd.Series:
    """Preenche com a moda (binárias) ou a mediana (contagens) do grupo de pares."""

    def estatistica(serie: pd.Series) -> float:
        serie = serie.dropna()
        if serie.empty:
            return np.nan
        return float(serie.mode().iloc[0]) if binaria else float(serie.median())

    por_grupo = df.groupby(GRUPO_PARES)[coluna].transform(estatistica)
    valores = df[coluna].fillna(por_grupo)
    return valores.fillna(estatistica(df[coluna]))


def tratar_ausentes(
    df: pd.DataFrame, excluidas: list[str]
) -> tuple[pd.DataFrame, dict[str, dict[str, int]]]:
    resultado = df.drop(columns=[c for c in excluidas if c in df])
    auditoria: dict[str, dict[str, int]] = {}

    for indicador in dict.fromkeys(INDICADORES_IMPUTACAO.values()):
        resultado[indicador] = 0

    atributos = [c for c in ATRIBUTOS_CENSO if c in resultado]
    for coluna in atributos:
        total_ausentes = int(resultado[coluna].isna().sum())
        if not total_ausentes:
            continue

        resultado[coluna], pela_escola = imputar_pela_propria_escola(resultado, coluna)
        ausentes_pares = resultado[coluna].isna()
        resultado[coluna] = imputar_pelos_pares(
            resultado, coluna, binaria=coluna in BINARIAS_CENSO
        )

        indicador = INDICADORES_IMPUTACAO.get(coluna, f"{coluna}_imputado")
        if indicador not in resultado:
            resultado[indicador] = 0
        imputadas = pela_escola | ausentes_pares
        resultado.loc[imputadas, indicador] = 1

        auditoria[coluna] = {
            "ausentes": total_ausentes,
            "pela_propria_escola_em_outro_ano": int(pela_escola.sum()),
            "pelo_grupo_de_pares": int(ausentes_pares.sum()),
        }

    restantes = resultado[atributos].isna().sum()
    restantes = {c: int(n) for c, n in restantes.items() if n}
    if restantes:
        raise ErroValidacao(f"Ausentes não tratados nos atributos: {restantes}")
    return resultado, auditoria


def derivar_atributos(df: pd.DataFrame) -> pd.DataFrame:
    """Converte contagens em razões, proporções e logaritmos e cria os índices."""

    resultado = df.copy()
    total = resultado[MATRICULAS_SEXO].sum(axis=1)
    if (total <= 0).any():
        raise ErroValidacao(f"{int((total <= 0).sum())} escolas-ano sem matrículas")

    resultado["matricula_total"] = total
    resultado["porte_log"] = np.log1p(total)
    resultado["prop_feminino"] = resultado["quantidade_matricula_feminino"] / total
    for original, nova in MATRICULAS_RACA.items():
        resultado[nova] = resultado[original] / total
    for original, nova in PROFISSIONAIS_PRESENCA.items():
        resultado[nova] = (resultado[original] > 0).astype(int)
    for original, nova in PROFISSIONAIS_RAZAO.items():
        resultado[nova] = np.log1p(100 * resultado[original] / total)
    resultado["salas_climatizadas_log"] = np.log1p(
        resultado["quantidade_sala_utilizada_climatizada"]
    )

    for indice, itens in DIMENSOES_INDICES.items():
        resultado[indice] = resultado[itens].mean(axis=1)

    return resultado.drop(columns=[c for c in CONTAGENS_CENSO if c in resultado])


def winsorizar(
    df: pd.DataFrame, colunas: list[str], percentis: tuple[float, float] = PERCENTIS_WINSORIZACAO
) -> tuple[pd.DataFrame, dict[str, dict[str, float | int]]]:
    resultado = df.copy()
    auditoria: dict[str, dict[str, float | int]] = {}
    for coluna in colunas:
        inferior, superior = resultado[coluna].quantile(list(percentis))
        afetadas = int(((resultado[coluna] < inferior) | (resultado[coluna] > superior)).sum())
        resultado[coluna] = resultado[coluna].clip(inferior, superior)
        auditoria[coluna] = {
            "limite_inferior": round(float(inferior), 6),
            "limite_superior": round(float(superior), 6),
            "linhas_limitadas": afetadas,
        }
    return resultado, auditoria


def remover_quase_constantes(
    df: pd.DataFrame, colunas: list[str], limiar: float
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Remove atributos em que um único valor ocupa a fração ``limiar`` ou mais das linhas."""

    removidas = {}
    for coluna in colunas:
        frequencia = float(df[coluna].value_counts(normalize=True).iloc[0])
        if frequencia >= limiar:
            removidas[coluna] = round(frequencia, 4)
    return df.drop(columns=list(removidas)), removidas


def montar_matriz(
    base: pd.DataFrame, excluidas: list[str], limiar_quase_constante: float
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Executa as transformações e retorna a matriz, a ligação com as etapas e a auditoria."""

    escolas_ano_repetidas = validar_censo_igual_entre_etapas(base)
    ligacao = separar_ligacao_etapas(base)
    escola_ano = remover_duplicacao(base)

    escola_ano, imputacoes = tratar_ausentes(escola_ano, excluidas)
    escola_ano = derivar_atributos(escola_ano)

    continuas = [
        "salas_climatizadas_log",
        "porte_log",
        "prop_feminino",
        *MATRICULAS_RACA.values(),
        *PROFISSIONAIS_RAZAO.values(),
    ]
    escola_ano, winsorizacao = winsorizar(escola_ano, continuas)

    candidatos = [c for c in DIMENSAO_DOS_ITENS if c in escola_ano]
    escola_ano, quase_constantes = remover_quase_constantes(
        escola_ano, candidatos, limiar_quase_constante
    )

    indicadores_imputacao = [
        c for c in escola_ano if c.endswith("_imputados") or c.endswith("_imputado")
    ]
    itens = [c for c in DIMENSAO_DOS_ITENS if c in escola_ano]
    indices = list(DIMENSOES_INDICES)
    colunas = (
        CHAVE_ESCOLA_ANO
        + COLUNAS_CONTEXTO
        + ["matricula_total"]
        + indicadores_imputacao
        + itens
        + indices
    )
    matriz = escola_ano[colunas]

    auditoria = {
        "escolas_ano_em_mais_de_uma_etapa": escolas_ano_repetidas,
        "linhas_removidas_por_duplicacao": len(base) - len(matriz),
        "colunas_excluidas_por_ausencia_estrutural": excluidas,
        "imputacoes": imputacoes,
        "winsorizacao": winsorizacao,
        "quase_constantes_removidas": quase_constantes,
        "atributos_itens": {c: DIMENSAO_DOS_ITENS[c] for c in itens},
        "atributos_indices": {i: DIMENSOES_INDICES[i] for i in indices},
        "indicadores_imputacao": indicadores_imputacao,
    }
    return matriz, ligacao, auditoria


def salvar_csv(df: pd.DataFrame, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    df.to_csv(temporario, index=False, encoding="utf-8")
    temporario.replace(caminho)


def salvar_relatorio(relatorio: dict, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    temporario.write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporario.replace(caminho)


def executar(
    entrada: Path,
    saida: Path,
    ligacao_saida: Path,
    relatorio: Path,
    excluidas: list[str],
    limiar_quase_constante: float,
) -> None:
    LOGGER.info("===== PIPELINE 02 — MATRIZ DE ATRIBUTOS =====")
    base = ler_base_integrada(entrada)
    validar_colunas(base, CHAVE_ETAPA + COLUNAS_CONTEXTO + ATRIBUTOS_CENSO, "Base integrada")

    matriz, ligacao, auditoria = montar_matriz(base, excluidas, limiar_quase_constante)
    LOGGER.info("Duplicação removida: %s escolas-ano", f"{len(matriz):,}")
    LOGGER.info("Colunas excluídas por ausência estrutural: %s", ", ".join(excluidas))
    for coluna, contagens in auditoria["imputacoes"].items():
        LOGGER.info(
            "Imputação em %s: %s pela própria escola, %s pelos pares",
            coluna,
            contagens["pela_propria_escola_em_outro_ano"],
            contagens["pelo_grupo_de_pares"],
        )
    LOGGER.info(
        "Quase constantes removidas: %s", ", ".join(auditoria["quase_constantes_removidas"])
    )

    salvar_csv(matriz, saida)
    salvar_csv(ligacao, ligacao_saida)
    dados_relatorio = {
        "executado_em_utc": datetime.now(timezone.utc).isoformat(),
        "entrada": {"arquivo": str(entrada), "registros": len(base)},
        "chave_saida": CHAVE_ESCOLA_ANO,
        "grupo_de_pares_imputacao": GRUPO_PARES,
        "limiar_quase_constante": limiar_quase_constante,
        "percentis_winsorizacao": list(PERCENTIS_WINSORIZACAO),
        **auditoria,
        "saidas": {
            "matriz": {
                "arquivo": str(saida),
                "registros": len(matriz),
                "colunas": len(matriz.columns),
                "duplicidades_na_chave": int(matriz.duplicated(CHAVE_ESCOLA_ANO).sum()),
            },
            "ligacao_etapas": {"arquivo": str(ligacao_saida), "registros": len(ligacao)},
        },
    }
    salvar_relatorio(dados_relatorio, relatorio)

    LOGGER.info("Arquivos gerados: %s, %s", saida, ligacao_saida)
    LOGGER.info("Relatório gerado: %s", relatorio)
    LOGGER.info("===== PIPELINE 02 FINALIZADO =====")


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gera a matriz de atributos por escola-ano a partir da base integrada."
    )
    parser.add_argument(
        "--entrada",
        type=Path,
        default=Path("data/processed/base_integrada.csv"),
        help="CSV da base integrada gerada pelo pipeline 01",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path("data/processed/atributos_escola_ano.csv"),
        help="CSV da matriz de atributos por escola-ano",
    )
    parser.add_argument(
        "--ligacao",
        type=Path,
        default=Path("data/processed/ligacao_etapas.csv"),
        help="CSV que liga cada escola-ano às etapas e aos resultados do IDEB",
    )
    parser.add_argument(
        "--relatorio",
        type=Path,
        default=Path("data/processed/relatorio_atributos.json"),
        help="Relatório JSON de auditoria",
    )
    parser.add_argument(
        "--excluir",
        nargs="*",
        default=COLUNAS_EXCLUIDAS_PADRAO,
        help="Colunas excluídas por ausência estrutural",
    )
    parser.add_argument(
        "--limiar-quase-constante",
        type=float,
        default=LIMIAR_QUASE_CONSTANTE_PADRAO,
        help="Frequência mínima do valor mais comum para remover um atributo",
    )
    return parser


def main() -> None:
    configurar_logs()
    argumentos = criar_parser().parse_args()
    try:
        executar(
            argumentos.entrada,
            argumentos.saida,
            argumentos.ligacao,
            argumentos.relatorio,
            argumentos.excluir,
            argumentos.limiar_quase_constante,
        )
    except (ErroValidacao, FileNotFoundError, pd.errors.ParserError) as erro:
        LOGGER.error("Pipeline interrompido: %s", erro)
        raise SystemExit(1) from erro


if __name__ == "__main__":
    main()
