
# ============================================================
# ED-ANTAQ-01
# AULA 23 - PARTE 2
# TESTES UNITARIOS DAS TRANSFORMACOES
# ============================================================

from pathlib import Path
import sys
import unittest

import pandas as pd


# Permitir importar os modulos da pasta src

RAIZ = Path(__file__).resolve().parents[1]
PASTA_SRC = RAIZ / "src"

sys.path.insert(0, str(PASTA_SRC))

from load import converter_numero, preparar_valores


class TestTransformacoes(unittest.TestCase):

    def test_01_converter_virgula_decimal(self):

        entrada = pd.Series(
            ["2,25", "4,5", "10"],
            dtype="string"
        )

        resultado = converter_numero(
            entrada,
            "TEU"
        )

        esperado = [2.25, 4.5, 10.0]

        self.assertEqual(
            resultado.tolist(),
            esperado
        )

    def test_02_preservar_valores_ausentes(self):

        entrada = pd.Series(
            ["1,5", None, ""],
            dtype="string"
        )

        resultado = converter_numero(
            entrada,
            "TEU"
        )

        self.assertEqual(
            resultado.iloc[0],
            1.5
        )

        self.assertTrue(
            pd.isna(resultado.iloc[1])
        )

        self.assertTrue(
            pd.isna(resultado.iloc[2])
        )

    def test_03_rejeitar_valor_invalido(self):

        entrada = pd.Series(
            ["2,5", "valor_invalido"],
            dtype="string"
        )

        with self.assertRaises(ValueError):

            converter_numero(
                entrada,
                "TEU"
            )

    def test_04_preparar_registro_valido(self):

        entrada = pd.DataFrame(
            {
                "IDCarga": ["100"],
                "IDAtracacao": ["200"],
                "CDMercadoria": ["3102"],
                "Tipo Operação da Carga": ["Teste"],
                "Natureza da Carga": ["Granel Sólido"],
                "Sentido": ["Desembarcados"],
                "TEU": ["2,25"],
                "QTCarga": ["10"],
                "PesoBrutoNumerico": ["150,5"]
            }
        )

        resultado = preparar_valores(entrada)

        self.assertEqual(len(resultado), 1)

        registro = resultado[0]

        self.assertEqual(registro[0], "100")
        self.assertEqual(registro[1], "200")
        self.assertEqual(registro[6], 2.25)
        self.assertEqual(registro[7], 10)
        self.assertEqual(registro[8], 150.5)

    def test_05_rejeitar_quantidade_fracionaria(self):

        entrada = pd.DataFrame(
            {
                "IDCarga": ["100"],
                "IDAtracacao": ["200"],
                "CDMercadoria": ["3102"],
                "Tipo Operação da Carga": ["Teste"],
                "Natureza da Carga": ["Granel Sólido"],
                "Sentido": ["Desembarcados"],
                "TEU": ["2,25"],
                "QTCarga": ["1,5"],
                "PesoBrutoNumerico": ["150,5"]
            }
        )

        with self.assertRaises(ValueError):

            preparar_valores(entrada)


if __name__ == "__main__":
    unittest.main()
