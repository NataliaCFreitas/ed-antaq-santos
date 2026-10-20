
# ============================================================
# ED-ANTAQ-01
# AULA 22 - PARTE 8
# VALIDACAO INTEGRADA DO BANCO STAGING
# ============================================================

from pathlib import Path
import sqlite3
import math
import sys


RAIZ = Path(__file__).resolve().parents[1]

BANCO = (
    RAIZ / "data" / "database"
    / "antaq_santos_staging.db"
)


def validar_condicao(condicao, mensagem):
    if not condicao:
        raise AssertionError(mensagem)

    print(f"[OK] {mensagem}")


def main():

    print("=" * 55)
    print("ED-ANTAQ-01 - VALIDACAO INTEGRADA DO STAGING")
    print("=" * 55)

    if not BANCO.is_file():
        raise FileNotFoundError(
            f"Banco staging nao encontrado: {BANCO}"
        )

    # Conexao explicitamente somente para leitura
    conexao = sqlite3.connect(
        BANCO.resolve().as_uri() + "?mode=ro",
        uri=True
    )

    try:

        # 1. VALIDAR A QUANTIDADE DE CARGAS

        cargas, peso_cargas = conexao.execute("""
            SELECT COUNT(*), SUM(PesoBruto)
            FROM carga_santos
        """).fetchone()

        validar_condicao(
            cargas == 760354,
            "Quantidade de cargas: 760354"
        )

        validar_condicao(
            peso_cargas is not None
            and math.isclose(
                peso_cargas,
                177073928.08,
                rel_tol=0,
                abs_tol=0.05
            ),
            "Peso bruto total das cargas"
        )

        # 2. VALIDAR ATRACACOES

        atracacoes, competencias_nulas = conexao.execute("""
            SELECT
                COUNT(*),
                SUM(
                    CASE
                        WHEN Competencia IS NULL THEN 1
                        ELSE 0
                    END
                )
            FROM atracacoes
        """).fetchone()

        validar_condicao(
            atracacoes == 6292,
            "Quantidade de atracacoes: 6292"
        )

        validar_condicao(
            competencias_nulas == 0,
            "Competencias ausentes: 0"
        )

        # 3. VALIDAR RELACIONAMENTO

        sem_atracacao = conexao.execute("""
            SELECT COUNT(*)
            FROM carga_santos AS c
            LEFT JOIN atracacoes AS a
                ON c.IDAtracacao = a.IDAtracacao
            WHERE a.IDAtracacao IS NULL
        """).fetchone()[0]

        validar_condicao(
            sem_atracacao == 0,
            "Cargas sem atracacao correspondente: 0"
        )

        # 4. VALIDAR GOLD

        registros_gold, peso_gold = conexao.execute("""
            SELECT
                SUM(QtdRegistrosCarga),
                SUM(PesoBrutoTotal)
            FROM gold_movimentacao_mensal
        """).fetchone()

        validar_condicao(
            registros_gold == cargas,
            "Gold reconciliada com a carga"
        )

        validar_condicao(
            peso_gold is not None
            and math.isclose(
                peso_gold,
                peso_cargas,
                rel_tol=0,
                abs_tol=0.05
            ),
            "Peso da Gold reconciliado"
        )

        # 5. VALIDAR VIEW 2024

        meses, registros_view, peso_view = conexao.execute("""
            SELECT
                COUNT(DISTINCT Competencia),
                SUM(QtdRegistrosCarga),
                SUM(PesoBrutoTotal)
            FROM vw_movimentacao_2024
        """).fetchone()

        validar_condicao(
            meses == 12,
            "VIEW com 12 competencias"
        )

        validar_condicao(
            registros_view == 757413,
            "VIEW com 757413 registros"
        )

        validar_condicao(
            peso_view is not None
            and math.isclose(
                peso_view,
                175853477.31,
                rel_tol=0,
                abs_tol=0.05
            ),
            "Peso da VIEW 2024"
        )

        # 6. VALIDAR INTEGRIDADE DO SQLITE

        integridade = conexao.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        validar_condicao(
            integridade == "ok",
            "Integridade SQLite"
        )

        print("\n" + "=" * 55)
        print("STATUS FINAL: STAGING APROVADO")
        print("=" * 55)

    finally:
        conexao.close()


if __name__ == "__main__":

    try:
        main()

    except Exception as erro:
        print("\nSTATUS FINAL: STAGING REPROVADO")
        print("Motivo:", erro)
        sys.exit(1)
