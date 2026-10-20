
# ============================================================
# PROJETO ED-ANTAQ-01
# AULA 18 - PARTE 3
# VALIDACAO DO RELACIONAMENTO ENTRE TABELAS
# ============================================================

from pathlib import Path
import sqlite3
import pandas as pd

# 1. Localizar o banco
RAIZ = Path(__file__).resolve().parents[1]

BANCO = (
    RAIZ / "data" / "database"
    / "antaq_santos_pipeline.db"
)

if not BANCO.is_file():
    raise FileNotFoundError(
        f"Banco nao encontrado: {BANCO}"
    )

# 2. Abrir conexao somente leitura
conexao = sqlite3.connect(
    BANCO.as_uri() + "?mode=ro",
    uri=True
)

try:

    # CONSULTA 1 - INTEGRIDADE DAS CARGAS
    sql_integridade = """
    SELECT
        COUNT(*) AS TotalCargas,
        COUNT(a.IDAtracacao) AS CargasComAtracacao,
        COUNT(*) - COUNT(a.IDAtracacao)
            AS CargasSemAtracacao

    FROM carga_santos AS c

    LEFT JOIN atracacoes AS a
        ON c.IDAtracacao = a.IDAtracacao;
    """

    print("\n1. INTEGRIDADE REFERENCIAL")

    df_integridade = pd.read_sql_query(
        sql_integridade,
        conexao
    )

    print(df_integridade.to_string(index=False))

    # CONSULTA 2 - ATRACACOES COM E SEM CARGA
    sql_cobertura = """
    SELECT
        COUNT(*) AS TotalAtracacoes,

        SUM(
            CASE
                WHEN EXISTS (
                    SELECT 1
                    FROM carga_santos AS c
                    WHERE c.IDAtracacao = a.IDAtracacao
                )
                THEN 1 ELSE 0
            END
        ) AS AtracacoesComCarga,

        SUM(
            CASE
                WHEN NOT EXISTS (
                    SELECT 1
                    FROM carga_santos AS c
                    WHERE c.IDAtracacao = a.IDAtracacao
                )
                THEN 1 ELSE 0
            END
        ) AS AtracacoesSemCarga

    FROM atracacoes AS a;
    """

    print("\n2. COBERTURA DAS ATRACACOES")

    df_cobertura = pd.read_sql_query(
        sql_cobertura,
        conexao
    )

    print(df_cobertura.to_string(index=False))

    # CONSULTA 3 - EXEMPLOS SEM CARGA
    sql_exemplos = """
    SELECT
        a.IDAtracacao,
        a.PortoAtracacao,
        a.Competencia

    FROM atracacoes AS a

    WHERE NOT EXISTS (
        SELECT 1
        FROM carga_santos AS c
        WHERE c.IDAtracacao = a.IDAtracacao
    )

    ORDER BY a.Competencia, a.IDAtracacao
    LIMIT 10;
    """

    print("\n3. EXEMPLOS DE ATRACACOES SEM CARGA")

    df_exemplos = pd.read_sql_query(
        sql_exemplos,
        conexao
    )

    print(df_exemplos.to_string(index=False))

    # 4. VALIDACOES
    assert (
        df_integridade.loc[0, "TotalCargas"]
        == 760354
    ), "Quantidade de cargas divergente."

    assert (
        df_integridade.loc[0, "CargasSemAtracacao"]
        == 0
    ), "Existem cargas sem atracacao correspondente."

    assert (
        df_cobertura.loc[0, "TotalAtracacoes"]
        == 6292
    ), "Quantidade de atracacoes divergente."

    assert (
        df_cobertura.loc[0, "AtracacoesComCarga"]
        + df_cobertura.loc[0, "AtracacoesSemCarga"]
        == df_cobertura.loc[0, "TotalAtracacoes"]
    ), "Divergencia na cobertura das atracacoes."

    print("\nValidacoes de relacionamento aprovadas.")

finally:
    conexao.close()
