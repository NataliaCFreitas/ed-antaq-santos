
# ============================================================
# ED-ANTAQ-01
# AULA 22 - PARTE 6
# GOLD PARAMETRIZADA - BANCO STAGING
# ============================================================

from pathlib import Path
import argparse
import sqlite3
import math
import pandas as pd


# 1. CONFIGURACOES

RAIZ = Path(__file__).resolve().parents[1]
PASTA_BANCO = RAIZ / "data" / "database"

BANCO_PRINCIPAL = (
    PASTA_BANCO / "antaq_santos_pipeline.db"
)

BANCOS_PERMITIDOS = {
    "staging": (
        PASTA_BANCO / "antaq_santos_staging.db"
    ),
    "reprocessamento": (
        PASTA_BANCO / "antaq_santos_reprocessamento.db"
    )
}

TOTAL_ESPERADO = 760354
PESO_ESPERADO = 177073928.08


# 2. RECEBER ARGUMENTO

def obter_argumentos():

    parser = argparse.ArgumentParser(
        description="Criar Gold ANTAQ no banco selecionado"
    )

    parser.add_argument(
        "--banco",
        choices=list(BANCOS_PERMITIDOS),
        required=True
    )

    return parser.parse_args()


# 3. CONSULTAR A SERIE MENSAL

def consultar_mensal(caminho):

    conexao = sqlite3.connect(
        caminho.resolve().as_uri() + "?mode=ro",
        uri=True
    )

    try:
        return pd.read_sql_query(
            """
            SELECT
                Competencia,
                SUM(QtdRegistrosCarga) AS Registros,
                SUM(PesoBrutoTotal) AS PesoTotal
            FROM gold_movimentacao_mensal
            GROUP BY Competencia
            ORDER BY Competencia
            """,
            conexao
        )

    finally:
        conexao.close()


# 4. CRIAR A GOLD

def criar_gold(caminho):

    if not caminho.is_file():
        raise FileNotFoundError(caminho)

    conexao = sqlite3.connect(caminho, timeout=30)

    try:

        existe = conexao.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'gold_movimentacao_mensal'
        """).fetchone()

        if existe is not None:
            raise RuntimeError(
                "A Gold ja existe neste banco. "
                "Nenhuma alteracao foi realizada."
            )

        conexao.execute("BEGIN")

        conexao.execute("""
            CREATE TABLE gold_movimentacao_mensal (
                Competencia TEXT,
                PortoAtracacao TEXT,
                NaturezaCarga TEXT,
                Sentido TEXT,
                QtdRegistrosCarga INTEGER,
                PesoBrutoTotal REAL
            )
        """)

        conexao.execute("""
            INSERT INTO gold_movimentacao_mensal (
                Competencia,
                PortoAtracacao,
                NaturezaCarga,
                Sentido,
                QtdRegistrosCarga,
                PesoBrutoTotal
            )
            SELECT
                a.Competencia,
                a.PortoAtracacao,
                c.NaturezaCarga,
                c.Sentido,
                COUNT(*),
                SUM(c.PesoBruto)
            FROM carga_santos AS c
            INNER JOIN atracacoes AS a
                ON c.IDAtracacao = a.IDAtracacao
            GROUP BY
                a.Competencia,
                a.PortoAtracacao,
                c.NaturezaCarga,
                c.Sentido
        """)

        registros, peso = conexao.execute("""
            SELECT
                SUM(QtdRegistrosCarga),
                SUM(PesoBrutoTotal)
            FROM gold_movimentacao_mensal
        """).fetchone()

        if registros != TOTAL_ESPERADO:
            raise AssertionError(
                f"Registros divergentes: {registros}"
            )

        if peso is None or not math.isclose(
            peso,
            PESO_ESPERADO,
            rel_tol=0,
            abs_tol=0.05
        ):
            raise AssertionError(
                f"Peso divergente: {peso}"
            )

        conexao.commit()

        print("\nGOLD CRIADA")
        print("Registros reconciliados:", registros)
        print("Peso bruto:", round(peso, 2))

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


# 5. COMPARAR COM O BANCO PRINCIPAL

def validar_gold(caminho):

    principal = consultar_mensal(BANCO_PRINCIPAL)
    atual = consultar_mensal(caminho)

    comparacao = principal.merge(
        atual,
        on="Competencia",
        how="outer",
        suffixes=("_Principal", "_Staging"),
        indicator=True,
        validate="one_to_one"
    )

    if len(comparacao) != 13:
        raise AssertionError(
            "Quantidade de competencias divergente."
        )

    if not (comparacao["_merge"] == "both").all():
        raise AssertionError(
            "Existem competencias sem correspondencia."
        )

    comparacao["DiferencaRegistros"] = (
        comparacao["Registros_Staging"]
        - comparacao["Registros_Principal"]
    )

    comparacao["DiferencaPeso"] = (
        comparacao["PesoTotal_Staging"]
        - comparacao["PesoTotal_Principal"]
    )

    if not (
        comparacao["DiferencaRegistros"] == 0
    ).all():
        raise AssertionError(
            "Divergencias na quantidade mensal."
        )

    if not (
        comparacao["DiferencaPeso"].abs() <= 0.01
    ).all():
        raise AssertionError(
            "Divergencias no peso mensal."
        )

    print("\n" + "=" * 55)
    print("COMPARACAO COM O BANCO PRINCIPAL")
    print("=" * 55)

    print(
        comparacao[
            [
                "Competencia",
                "DiferencaRegistros",
                "DiferencaPeso"
            ]
        ].to_string(index=False)
    )

    print("\nCompetencias comparadas:", len(comparacao))
    print("Status: GOLD VALIDADA")


# 6. EXECUCAO PRINCIPAL

def main():

    argumentos = obter_argumentos()
    caminho = BANCOS_PERMITIDOS[argumentos.banco]

    if not BANCO_PRINCIPAL.is_file():
        raise FileNotFoundError(BANCO_PRINCIPAL)

    print("=" * 55)
    print("ED-ANTAQ-01 - GOLD PARAMETRIZADA")
    print("=" * 55)

    print("Ambiente selecionado:", argumentos.banco)

    criar_gold(caminho)
    validar_gold(caminho)


if __name__ == "__main__":
    main()
