import unittest

import pandas as pd

from pipelines.pipeline_02_atributos import (
    ATRIBUTOS_CENSO,
    BINARIAS_CENSO,
    CHAVE_ESCOLA_ANO,
    COLUNAS_CONTEXTO,
    COLUNAS_EXCLUIDAS_PADRAO,
    ErroValidacao,
    derivar_atributos,
    montar_matriz,
    remover_quase_constantes,
    tratar_ausentes,
    validar_censo_igual_entre_etapas,
    winsorizar,
)


def linha_base(id_escola: str, ano: int, anos_escolares: str, **valores) -> dict:
    linha = {
        "id_escola": id_escola,
        "ano": ano,
        "anos_escolares": anos_escolares,
        "sigla_uf_censo": "BA",
        "id_municipio_censo": 2927408,
        "rede": "Municipal",
        "tipo_localizacao": "Urbana",
        "ensino": "medio" if anos_escolares == "todos (1-4)" else "fundamental",
        "ideb": 5.0,
    }
    for coluna in BINARIAS_CENSO:
        linha[coluna] = 1.0
    for coluna in ATRIBUTOS_CENSO:
        if coluna not in BINARIAS_CENSO:
            linha[coluna] = 10.0
    linha["quantidade_matricula_feminino"] = 100.0
    linha["quantidade_matricula_masculino"] = 100.0
    linha.update(valores)
    return linha


class Pipeline02TestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.base = pd.DataFrame(
            [
                linha_base("100", 2019, "iniciais (1-5)", biblioteca=0.0),
                linha_base("100", 2019, "finais (6-9)", biblioteca=0.0),
                linha_base("100", 2021, "iniciais (1-5)"),
                linha_base("200", 2019, "todos (1-4)", noturno=0.0),
                linha_base("300", 2023, "iniciais (1-5)", quantidade_matricula_feminino=900.0),
            ]
        )

    def test_censo_diferente_entre_etapas_interrompe_pipeline(self) -> None:
        divergente = self.base.copy()
        divergente.loc[1, "biblioteca"] = 1.0
        with self.assertRaises(ErroValidacao):
            validar_censo_igual_entre_etapas(divergente)

    def test_saida_tem_uma_linha_por_escola_ano_com_etapas_oferecidas(self) -> None:
        matriz, ligacao, auditoria = montar_matriz(self.base, COLUNAS_EXCLUIDAS_PADRAO, 1.01)

        self.assertEqual(len(matriz), 4)
        self.assertFalse(matriz.duplicated(CHAVE_ESCOLA_ANO).any())
        self.assertEqual(len(ligacao), len(self.base))
        self.assertEqual(auditoria["escolas_ano_em_mais_de_uma_etapa"], 1)

        escola = matriz.set_index(CHAVE_ESCOLA_ANO).loc[("100", 2019)]
        self.assertEqual(escola["oferece_iniciais"], 1)
        self.assertEqual(escola["oferece_finais"], 1)
        self.assertEqual(escola["oferece_medio"], 0)

    def test_colunas_estruturais_sao_excluidas_e_nao_restam_ausentes(self) -> None:
        base = self.base.copy()
        base["laboratorio_educacao_profissional"] = None
        matriz, _, _ = montar_matriz(base, COLUNAS_EXCLUIDAS_PADRAO, 1.01)

        for coluna in COLUNAS_EXCLUIDAS_PADRAO:
            self.assertNotIn(coluna, matriz.columns)
        self.assertEqual(int(matriz.drop(columns=COLUNAS_CONTEXTO).isna().sum().sum()), 0)

    def test_imputacao_pela_propria_escola_tem_prioridade_sobre_a_moda(self) -> None:
        escola_ano = pd.DataFrame(
            {
                "id_escola": ["100", "100", "200", "300", "400"],
                "ano": [2019, 2021, 2019, 2019, 2019],
                "rede": ["Municipal"] * 5,
                "tipo_localizacao": ["Urbana"] * 5,
                "orgao_gremio_estudantil": [None, 1.0, 0.0, 0.0, None],
            }
        )
        resultado, auditoria = tratar_ausentes(escola_ano, [])

        # A escola 100 recebe o próprio valor de 2021; a 400 recebe a moda dos pares (0).
        self.assertEqual(resultado.loc[0, "orgao_gremio_estudantil"], 1.0)
        self.assertEqual(resultado.loc[4, "orgao_gremio_estudantil"], 0.0)
        self.assertEqual(resultado["gremio_imputado"].tolist(), [1, 0, 0, 0, 1])
        self.assertEqual(
            auditoria["orgao_gremio_estudantil"],
            {"ausentes": 2, "pela_propria_escola_em_outro_ano": 1, "pelo_grupo_de_pares": 1},
        )

    def test_profissionais_raros_viram_presenca_e_pedagogia_vira_razao(self) -> None:
        escola_ano = pd.DataFrame([linha_base("100", 2023, "iniciais (1-5)")]).drop(
            columns=["anos_escolares", "ensino", "ideb"]
        )
        escola_ano["quantidade_profissional_nutricionista"] = 3.0
        escola_ano["quantidade_profissional_psicologo"] = 0.0
        resultado = derivar_atributos(escola_ano)

        self.assertEqual(resultado.loc[0, "tem_nutricionista"], 1)
        self.assertEqual(resultado.loc[0, "tem_psicologo"], 0)
        self.assertNotIn("profissional_nutricionista_100_alunos", resultado.columns)
        self.assertIn("profissional_pedagogia_100_alunos", resultado.columns)

    def test_winsorizacao_respeita_percentis(self) -> None:
        df = pd.DataFrame({"valor": list(range(100)) + [10_000]})
        resultado, auditoria = winsorizar(df, ["valor"])

        limites = auditoria["valor"]
        self.assertLessEqual(resultado["valor"].max(), limites["limite_superior"])
        self.assertGreaterEqual(resultado["valor"].min(), limites["limite_inferior"])
        self.assertGreater(limites["linhas_limitadas"], 0)

    def test_quase_constantes_nao_aparecem_na_saida(self) -> None:
        df = pd.DataFrame({"rara": [1] + [0] * 99, "variada": [0, 1] * 50})
        resultado, removidas = remover_quase_constantes(df, ["rara", "variada"], 0.98)

        self.assertNotIn("rara", resultado.columns)
        self.assertIn("variada", resultado.columns)
        self.assertEqual(list(removidas), ["rara"])


if __name__ == "__main__":
    unittest.main()
