
# ============================================================
# PROJETO ED-ANTAQ-01
# AULA 19 - PARTE 1
# CONSTRUCAO DA CAMADA GOLD NO SQLITE
# ============================================================

from pathlib import Path
import sqlite3
import math
import pandas as pd


# 1. CONFIGURACOES

RAIZ = Path(__file__).resolve().parents[1]

BANCO = (
    RAIZ / "data" / "database"
    / "antaq_santos_pipeline.db"
)

TOTAL_ESPERADO = 760354
PESO_ESPERADO = 177073928.08

if not BANCO.is_file():
    raise FileNotFoundError(
        f"Banco nao encontrado: {BANCO}"
    )


# 2. CONECTAR AO SQLITE

conexao = sqlite3.connect(BANCO)

try:

    print("=" * 55)
    print("ED-ANTAQ-01 - CONSTRUCAO DA CAMADA GOLD")
    print("=" * 55)

    # 3. VERIFICAR A INTEGRIDADE DO RELACIONAMENTO

    integridade = conexao.execute("""
        SELECT COUNT(*)
        FROM carga_santos AS c
        LEFT JOIN atracacoes AS a
            ON c.IDAtracacao = a.IDAtracacao
        WHERE a.IDAtracacao IS NULL
    """).fetchone()[0]

    if integridade != 0:
        raise ValueError(
            f"Existem {integridade} cargas sem atracacao."
        )

    print("Integridade referencial: OK")

    # 4. IMPEDIR SOBRESCRITA DE UMA GOLD EXISTENTE

    tabela_existente = conexao.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'gold_movimentacao_mensal'
    """).fetchone()

    if tabela_existente is not None:
        raise RuntimeError(
            "A tabela gold_movimentacao_mensal ja existe. "
            "A execucao foi cancelada para preservar "
            "o resultado anterior."
        )

    # 5. INICIAR TRANSACAO

    conexao.execute("BEGIN")

    # 6. CRIAR A TABELA GOLD

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

    # 7. AGREGAR OS DADOS

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

    # 8. RECONCILIAR OS TOTAIS

    registros, peso = conexao.execute("""
        SELECT
            SUM(QtdRegistrosCarga),
            SUM(PesoBrutoTotal)
        FROM gold_movimentacao_mensal
    """).fetchone()

    if registros != TOTAL_ESPERADO:
        raise ValueError(
            f"Registros divergentes: {registros}"
        )

    if peso is None or not math.isclose(
        peso,
        PESO_ESPERADO,
        rel_tol=0,
        abs_tol=0.05
    ):
        raise ValueError(
            f"Peso divergente: {peso}"
        )

    # 9. CONFIRMAR TRANSACAO

    conexao.commit()

    print("\nTabela Gold criada e reconciliada.")

    # 10. CONSULTAR A SERIE MENSAL

    consulta = """
        SELECT
            Competencia,
            SUM(QtdRegistrosCarga) AS Registros,
            ROUND(SUM(PesoBrutoTotal), 2) AS PesoTotal
        FROM gold_movimentacao_mensal
        GROUP BY Competencia
        ORDER BY Competencia
    """

    resultado = pd.read_sql_query(
        consulta,
        conexao
    )

    print("\nSERIE MENSAL:")
    print(resultado.to_string(index=False))

    print("\nRESUMO:")
    print("Registros reconciliados:", registros)
    print("Peso bruto reconciliado:", round(peso, 2))
    print("Competencias encontradas:", len(resultado))

except Exception:

    conexao.rollback()
    raise

finally:

    conexao.close()
