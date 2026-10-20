
# ============================================================
# ED-ANTAQ-01
# AULA 23 - PARTE 1
# TESTES AUTOMATIZADOS DO BANCO PUBLICADO
# ============================================================

from pathlib import Path
import sqlite3
import unittest
import math


RAIZ = Path(__file__).resolve().parents[1]

BANCO = (
    RAIZ
    / "data"
    / "database"
    / "antaq_santos_publicado.db"
)


class TestBancoPublicado(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        if not BANCO.is_file():
            raise FileNotFoundError(
                f"Banco publicado nao encontrado: {BANCO}"
            )

        cls.conexao = sqlite3.connect(
            BANCO.resolve().as_uri() + "?mode=ro",
            uri=True
        )

    @classmethod
    def tearDownClass(cls):
        cls.conexao.close()

    def test_01_quantidade_cargas(self):

        total = self.conexao.execute("""
            SELECT COUNT(*)
            FROM carga_santos
        """).fetchone()[0]

        self.assertEqual(total, 760354)

    def test_02_quantidade_atracacoes(self):

        total = self.conexao.execute("""
            SELECT COUNT(*)
            FROM atracacoes
        """).fetchone()[0]

        self.assertEqual(total, 6292)

    def test_03_integridade_relacionamento(self):

        total = self.conexao.execute("""
            SELECT COUNT(*)
            FROM carga_santos AS c
            LEFT JOIN atracacoes AS a
                ON c.IDAtracacao = a.IDAtracacao
            WHERE a.IDAtracacao IS NULL
        """).fetchone()[0]

        self.assertEqual(total, 0)

    def test_04_registros_view_2024(self):

        total = self.conexao.execute("""
            SELECT SUM(QtdRegistrosCarga)
            FROM vw_movimentacao_2024
        """).fetchone()[0]

        self.assertEqual(total, 757413)

    def test_05_meses_view_2024(self):

        meses = self.conexao.execute("""
            SELECT COUNT(DISTINCT Competencia)
            FROM vw_movimentacao_2024
        """).fetchone()[0]

        self.assertEqual(meses, 12)

    def test_06_peso_bruto(self):

        peso = self.conexao.execute("""
            SELECT SUM(PesoBruto)
            FROM carga_santos
        """).fetchone()[0]

        self.assertTrue(
            math.isclose(
                peso,
                177073928.08,
                rel_tol=0,
                abs_tol=0.05
            )
        )

    def test_07_integridade_sqlite(self):

        resultado = self.conexao.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        self.assertEqual(resultado, "ok")


if __name__ == "__main__":
    unittest.main()

