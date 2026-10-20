
# ============================================================
# PROJETO ED-ANTAQ-01
# AULA 18 - CONSULTAS SQL NO SQLITE
# ============================================================

from pathlib import Path
import sqlite3
import pandas as pd

# 1. Localizar o banco de dados
RAIZ = Path(__file__).resolve().parents[1]

CAMINHO_BANCO = (
    RAIZ / "data" / "database" /
    "antaq_santos_pipeline.db"
)

if not CAMINHO_BANCO.is_file():
    raise FileNotFoundError(
        f"Banco nao encontrado: {CAMINHO_BANCO}"
    )

# 2. Abrir conexao em modo somente leitura
conexao = sqlite3.connect(
    CAMINHO_BANCO.as_uri() + "?mode=ro",
    uri=True
)

try:

    # CONSULTA 1 - TOTAL DE REGISTROS
    sql_total = """
    SELECT
        COUNT(*) AS TotalRegistros,
        COUNT(DISTINCT IDAtracacao) AS AtracacoesDistintas,
        ROUND(SUM(PesoBruto), 2) AS PesoTotal
    FROM carga_santos;
    """

    print("\n1. RESUMO GERAL")
    print(
        pd.read_sql_query(
            sql_total,
            conexao
        ).to_string(index=False)
    )

    # CONSULTA 2 - NATUREZA DA CARGA
    sql_natureza = """
    SELECT
        NaturezaCarga,
        COUNT(*) AS Registros,
        ROUND(SUM(PesoBruto), 2) AS PesoTotal
    FROM carga_santos
    GROUP BY NaturezaCarga
    ORDER BY PesoTotal DESC;
    """

    print("\n2. POR NATUREZA DA CARGA")
    print(
        pd.read_sql_query(
            sql_natureza,
            conexao
        ).to_string(index=False)
    )

    # CONSULTA 3 - SENTIDO
    sql_sentido = """
    SELECT
        Sentido,
        COUNT(*) AS Registros,
        ROUND(SUM(PesoBruto), 2) AS PesoTotal
    FROM carga_santos
    GROUP BY Sentido
    ORDER BY PesoTotal DESC;
    """

    print("\n3. POR SENTIDO")
    print(
        pd.read_sql_query(
            sql_sentido,
            conexao
        ).to_string(index=False)
    )

finally:
    conexao.close()

print("\nConsultas finalizadas.")
