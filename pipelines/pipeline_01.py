"""Pipeline 01 de preparação e integração dos dados do Censo Escolar e do IDEB."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd


ANOS_VALIDOS = (2019, 2021, 2023)
CHAVE_CENSO = ["id_escola", "ano"]
CHAVE_INTEGRACAO = ["id_escola", "ano", "anos_escolares"]

COLUNAS_CENSO = ["ano", "id_escola", "id_municipio"]
COLUNAS_IDEB = [
    "ano",
    "id_escola",
    "id_municipio",
    "anos_escolares",
    "taxa_aprovacao",
    "indicador_rendimento",
    "nota_saeb_media_padronizada",
    "ideb",
]

DOMINIOS_NUMERICOS_IDEB = {
    "taxa_aprovacao": (0.0, 100.0),
    "indicador_rendimento": (0.0, 1.0),
    "nota_saeb_media_padronizada": (0.0, 10.0),
    "ideb": (0.0, 10.0),
    "projecao": (0.0, 10.0),
}

LOGGER = logging.getLogger("pipeline")


class ErroValidacao(ValueError):
    """Erro que impede a geração de uma base integrada confiável."""


def configurar_logs() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def validar_colunas(df: pd.DataFrame, obrigatorias: Iterable[str], nome: str) -> None:
    ausentes = sorted(set(obrigatorias) - set(df.columns))
    if ausentes:
        raise ErroValidacao(
            f"{nome}: colunas obrigatórias ausentes: {', '.join(ausentes)}"
        )


def ler_csv(caminho: Path, nome: str) -> pd.DataFrame:
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {caminho}")

    df = pd.read_csv(
        caminho,
        dtype={"id_escola": "string", "id_municipio": "string"},
        low_memory=False,
    )
    df.columns = df.columns.str.strip()
    LOGGER.info("%s carregado: %s registros × %s colunas", nome, f"{len(df):,}", len(df.columns))
    return df


def padronizar_chaves(df: pd.DataFrame, nome: str) -> pd.DataFrame:
    resultado = df.copy()

    for coluna in ("id_escola", "id_municipio"):
        if coluna in resultado:
            resultado[coluna] = resultado[coluna].astype("string").str.strip()
            resultado[coluna] = resultado[coluna].replace("", pd.NA)

    ano_convertido = pd.to_numeric(resultado["ano"], errors="coerce")
    invalidos = int(ano_convertido.isna().sum() - resultado["ano"].isna().sum())
    if invalidos:
        raise ErroValidacao(f"{nome}: {invalidos} valores de ano não são numéricos")
    resultado["ano"] = ano_convertido.astype("Int64")

    if "anos_escolares" in resultado:
        resultado["anos_escolares"] = (
            resultado["anos_escolares"].astype("string").str.strip().str.lower()
        )
        resultado["anos_escolares"] = resultado["anos_escolares"].replace("", pd.NA)

    return resultado


def filtrar_anos(df: pd.DataFrame, nome: str) -> tuple[pd.DataFrame, int]:
    fora_do_recorte = int((~df["ano"].isin(ANOS_VALIDOS)).sum())
    resultado = df.loc[df["ano"].isin(ANOS_VALIDOS)].copy()
    if resultado.empty:
        raise ErroValidacao(f"{nome}: nenhum registro pertence aos anos {ANOS_VALIDOS}")
    return resultado, fora_do_recorte


def validar_chave(df: pd.DataFrame, chave: list[str], nome: str) -> None:
    nulos = df[chave].isna().sum()
    nulos = {coluna: int(total) for coluna, total in nulos.items() if total}
    if nulos:
        raise ErroValidacao(f"{nome}: valores ausentes na chave: {nulos}")

    duplicados = int(df.duplicated(chave, keep=False).sum())
    if duplicados:
        raise ErroValidacao(
            f"{nome}: {duplicados} registros pertencem a chaves duplicadas em {chave}"
        )


def padronizar_e_validar_numericos_ideb(df: pd.DataFrame) -> pd.DataFrame:
    resultado = df.copy()
    for coluna, (minimo, maximo) in DOMINIOS_NUMERICOS_IDEB.items():
        if coluna not in resultado:
            continue

        original = resultado[coluna]
        convertida = pd.to_numeric(original, errors="coerce")
        falhas_conversao = int((original.notna() & convertida.isna()).sum())
        if falhas_conversao:
            raise ErroValidacao(
                f"IDEB: {falhas_conversao} valores inválidos na coluna {coluna}"
            )

        fora_dominio = convertida.notna() & ~convertida.between(minimo, maximo)
        if fora_dominio.any():
            raise ErroValidacao(
                f"IDEB: {int(fora_dominio.sum())} valores de {coluna} fora de "
                f"[{minimo}, {maximo}]"
            )
        resultado[coluna] = convertida
    return resultado


def preparar_granularidade_censo(
    censo: pd.DataFrame, ideb: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Leva o Censo de escola-ano para escola-ano-etapa antes do cruzamento final.

    O arquivo do Censo usado no projeto tem uma linha por escola e ano e, portanto,
    não contém ``anos_escolares``. As etapas válidas são obtidas da chave única do
    IDEB. A expansão abaixo não agrega nem inventa indicadores: apenas associa a
    infraestrutura da escola às etapas para as quais há uma observação no IDEB.
    """

    etapas_ideb = ideb[CHAVE_INTEGRACAO].drop_duplicates()
    auditoria = etapas_ideb.merge(
        censo[CHAVE_CENSO],
        on=CHAVE_CENSO,
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    sem_censo = int((auditoria["_merge"] == "left_only").sum())

    pares_ideb = etapas_ideb[CHAVE_CENSO].drop_duplicates()
    censo_sem_ideb = int(
        (
            censo[CHAVE_CENSO]
            .merge(pares_ideb, on=CHAVE_CENSO, how="left", indicator=True)["_merge"]
            == "left_only"
        ).sum()
    )

    censo_por_etapa = etapas_ideb.merge(
        censo,
        on=CHAVE_CENSO,
        how="inner",
        validate="many_to_one",
    )
    validar_chave(censo_por_etapa, CHAVE_INTEGRACAO, "Censo por etapa")

    return censo_por_etapa, {
        "chaves_ideb_sem_censo": sem_censo,
        "escolas_ano_censo_sem_ideb": censo_sem_ideb,
        "registros_censo_apos_expansao_por_etapa": len(censo_por_etapa),
    }


def integrar(censo_por_etapa: pd.DataFrame, ideb: pd.DataFrame) -> pd.DataFrame:
    integrada = censo_por_etapa.merge(
        ideb,
        on=CHAVE_INTEGRACAO,
        how="inner",
        validate="one_to_one",
        suffixes=("_censo", "_ideb"),
    )
    validar_chave(integrada, CHAVE_INTEGRACAO, "Base integrada")

    if len(integrada) != len(censo_por_etapa):
        raise ErroValidacao(
            "A integração final perdeu registros que já tinham correspondência no Censo"
        )

    for coluna in ("sigla_uf", "id_municipio", "id_municipio_nome"):
        coluna_censo = f"{coluna}_censo"
        coluna_ideb = f"{coluna}_ideb"
        if coluna_censo in integrada and coluna_ideb in integrada:
            divergencias = (
                integrada[coluna_censo].astype("string")
                != integrada[coluna_ideb].astype("string")
            ).fillna(False)
            if divergencias.any():
                raise ErroValidacao(
                    f"Base integrada: {int(divergencias.sum())} divergências em {coluna}"
                )

    demais_colunas = [c for c in integrada.columns if c not in CHAVE_INTEGRACAO]
    return integrada[CHAVE_INTEGRACAO + demais_colunas]


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


def executar(caminho_censo: Path, caminho_ideb: Path, saida: Path, relatorio: Path) -> None:
    LOGGER.info("===== PIPELINE CENSO + IDEB =====")
    censo = ler_csv(caminho_censo, "Censo")
    ideb = ler_csv(caminho_ideb, "IDEB")
    recebidos = {"censo": len(censo), "ideb": len(ideb)}

    validar_colunas(censo, COLUNAS_CENSO, "Censo")
    validar_colunas(ideb, COLUNAS_IDEB, "IDEB")
    LOGGER.info("Colunas obrigatórias verificadas")

    censo = padronizar_chaves(censo, "Censo")
    ideb = padronizar_chaves(ideb, "IDEB")
    ideb = padronizar_e_validar_numericos_ideb(ideb)
    LOGGER.info("Tipos e domínios numéricos padronizados")

    censo, censo_fora_recorte = filtrar_anos(censo, "Censo")
    ideb, ideb_fora_recorte = filtrar_anos(ideb, "IDEB")
    LOGGER.info("Recorte temporal aplicado: %s", ", ".join(map(str, ANOS_VALIDOS)))

    validar_chave(censo, CHAVE_CENSO, "Censo")
    validar_chave(ideb, CHAVE_INTEGRACAO, "IDEB")
    LOGGER.info("Chaves sem nulos e sem duplicidades")

    censo_por_etapa, auditoria = preparar_granularidade_censo(censo, ideb)
    LOGGER.info(
        "Censo levado à granularidade da chave %s", " + ".join(CHAVE_INTEGRACAO)
    )
    LOGGER.info("Chaves do IDEB sem correspondência no Censo: %s", auditoria["chaves_ideb_sem_censo"])

    integrada = integrar(censo_por_etapa, ideb)
    LOGGER.info("Cruzamento 1:1 concluído: %s registros", f"{len(integrada):,}")

    salvar_csv(integrada, saida)
    dados_relatorio = {
        "executado_em_utc": datetime.now(timezone.utc).isoformat(),
        "entradas": {
            "censo": {"arquivo": str(caminho_censo), "registros": recebidos["censo"]},
            "ideb": {"arquivo": str(caminho_ideb), "registros": recebidos["ideb"]},
        },
        "anos_selecionados": list(ANOS_VALIDOS),
        "chave_censo_original": CHAVE_CENSO,
        "chave_integracao": CHAVE_INTEGRACAO,
        "registros_fora_do_recorte": {
            "censo": censo_fora_recorte,
            "ideb": ideb_fora_recorte,
        },
        "auditoria_cruzamento": auditoria,
        "saida": {
            "arquivo": str(saida),
            "registros": len(integrada),
            "colunas": len(integrada.columns),
            "duplicidades_na_chave": int(integrada.duplicated(CHAVE_INTEGRACAO).sum()),
            "nulos_na_chave": int(integrada[CHAVE_INTEGRACAO].isna().sum().sum()),
        },
    }
    salvar_relatorio(dados_relatorio, relatorio)

    LOGGER.info("Arquivo gerado: %s", saida)
    LOGGER.info("Relatório gerado: %s", relatorio)
    LOGGER.info("===== PIPELINE FINALIZADO =====")


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepara e integra Censo Escolar e IDEB pela chave escola-ano-etapa."
    )
    parser.add_argument(
        "--censo",
        type=Path,
        default=Path("data/censo_nordeste_2019+.csv"),
        help="CSV do Censo Escolar",
    )
    parser.add_argument(
        "--ideb",
        type=Path,
        default=Path("data/ideb_nordeste_2019+.csv"),
        help="CSV do IDEB",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path("data/processed/base_integrada.csv"),
        help="CSV integrado de saída",
    )
    parser.add_argument(
        "--relatorio",
        type=Path,
        default=Path("data/processed/relatorio_execucao.json"),
        help="Relatório JSON de auditoria",
    )
    return parser


def main() -> None:
    configurar_logs()
    argumentos = criar_parser().parse_args()
    try:
        executar(argumentos.censo, argumentos.ideb, argumentos.saida, argumentos.relatorio)
    except (ErroValidacao, FileNotFoundError, pd.errors.ParserError) as erro:
        LOGGER.error("Pipeline interrompido: %s", erro)
        raise SystemExit(1) from erro


if __name__ == "__main__":
    main()
