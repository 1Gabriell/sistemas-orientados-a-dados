import unittest

import pandas as pd

from pipelines.pipeline_01 import (
    CHAVE_INTEGRACAO,
    ErroValidacao,
    integrar,
    padronizar_e_validar_numericos_ideb,
    preparar_granularidade_censo,
    validar_chave,
)


class PipelineTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.censo = pd.DataFrame(
            {
                "id_escola": ["100"],
                "ano": pd.Series([2023], dtype="Int64"),
                "id_municipio": ["10"],
                "sigla_uf": ["PE"],
                "id_municipio_nome": ["Recife"],
                "biblioteca": [1],
            }
        )
        self.ideb = pd.DataFrame(
            {
                "id_escola": ["100", "100"],
                "ano": pd.Series([2023, 2023], dtype="Int64"),
                "anos_escolares": ["iniciais (1-5)", "finais (6-9)"],
                "id_municipio": ["10", "10"],
                "sigla_uf": ["PE", "PE"],
                "id_municipio_nome": ["Recife", "Recife"],
                "ideb": [5.1, 4.8],
            }
        )

    def test_integracao_preserva_duas_etapas_e_chave_tripla_unica(self) -> None:
        censo_por_etapa, auditoria = preparar_granularidade_censo(
            self.censo, self.ideb
        )
        resultado = integrar(censo_por_etapa, self.ideb)

        self.assertEqual(len(resultado), 2)
        self.assertEqual(auditoria["chaves_ideb_sem_censo"], 0)
        self.assertEqual(resultado["anos_escolares"].nunique(), 2)
        self.assertFalse(resultado.duplicated(CHAVE_INTEGRACAO).any())

    def test_duplicidade_na_chave_tripla_interrompe_pipeline(self) -> None:
        duplicado = pd.concat([self.ideb, self.ideb.iloc[[0]]], ignore_index=True)
        with self.assertRaises(ErroValidacao):
            validar_chave(duplicado, CHAVE_INTEGRACAO, "IDEB")

    def test_indicador_fora_do_dominio_interrompe_pipeline(self) -> None:
        invalido = self.ideb.assign(ideb=[11.0, 4.8])
        with self.assertRaises(ErroValidacao):
            padronizar_e_validar_numericos_ideb(invalido)


if __name__ == "__main__":
    unittest.main()
