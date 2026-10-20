
# ============================================================
# PROJETO ED-ANTAQ-01
# AULA 19 - PARTE 2
# CRIACAO DA VIEW ANALITICA DE 2024
# ============================================================

from pathlib import Path
import sqlite3
import pandas as pd
import math


# 1. DEFINIR O CAMINHO DO BANCO

RAIZ = Path(__file__).resolve().parents[1]

BANCO = (
    RAIZ / "data" / "database"
    / "antaq_santos_pipeline.db"
)

if not BANCO.is_file():
    raise FileNotFoundError(
        f"Banco nao encontrado: {BANCO}"
    )


# 2. CONECTAR AO SQLITE

with sqlite3.connect(BANCO) as conexao:

    # 3. CRIAR A VIEW
    # IF NOT EXISTS permite executar novamente sem duplicar.

    conexao.execute("""
        CREATE VIEW IF NOT EXISTS vw_movimentacao_2024 AS
        SELECT
            Competencia,
            PortoAtracacao,
            NaturezaCarga,
            Sentido,
            QtdRegistrosCarga,
            PesoBrutoTotal
        FROM gold_movimentacao_mensal
        WHERE Competencia >= '2024-01'
          AND Competencia < '2025-01';
    """)

    print("VIEW criada ou ja existente.")

    # 4. CONSULTAR O RESUMO

    sql_resumo = """
    SELECT
        COUNT(DISTINCT Competencia) AS Meses,
        SUM(QtdRegistrosCarga) AS Registros,
        ROUND(SUM(PesoBrutoTotal), 2) AS PesoTotal
    FROM vw_movimentacao_2024;
    """

    resumo = pd.read_sql_query(
        sql_resumo,
        conexao
    )

    print("\n1. RESUMO DA VIEW 2024")
    print(resumo.to_string(index=False))

    # 5. VALIDAR OS RESULTADOS

    assert resumo.loc[0, "Meses"] == 12

    assert resumo.loc[0, "Registros"] == 757413

    assert math.isclose(
        resumo.loc[0, "PesoTotal"],
        175853477.31,
        rel_tol=0,
        abs_tol=0.05
    )

    # 6. CONSULTAR A MOVIMENTACAO MENSAL

    sql_mensal = """
    SELECT
        Competencia,
        SUM(QtdRegistrosCarga) AS Registros,
        ROUND(SUM(PesoBrutoTotal), 2) AS PesoTotal
    FROM vw_movimentacao_2024
    GROUP BY Competencia
    ORDER BY Competencia;
    """

    mensal = pd.read_sql_query(
        sql_mensal,
        conexao
    )

    print("\n2. SERIE MENSAL DE 2024")
    print(mensal.to_string(index=False))

    # 7. CONSULTAR POR NATUREZA DA CARGA

    sql_natureza = """
    SELECT
        NaturezaCarga,
        SUM(QtdRegistrosCarga) AS Registros,
        ROUND(SUM(PesoBrutoTotal), 2) AS PesoTotal
    FROM vw_movimentacao_2024
    GROUP BY NaturezaCarga
    ORDER BY PesoTotal DESC;
    """

    natureza = pd.read_sql_query(
        sql_natureza,
        conexao
    )

    print("\n3. NATUREZA DA CARGA - 2024")
    print(natureza.to_string(index=False))

    print("\nValidacoes da VIEW concluidas.")
