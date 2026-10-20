
# ============================================================
# PROJETO ED-ANTAQ-01
# AULA 20 - PARTE 2
# CONSULTAS SQL PARAMETRIZADAS
# ============================================================

from pathlib import Path
import sqlite3
import pandas as pd


# 1. LOCALIZAR OS ARQUIVOS

RAIZ = Path(__file__).resolve().parents[1]

BANCO = (
    RAIZ / "data" / "database"
    / "antaq_santos_pipeline.db"
)

ARQUIVO_SQL = (
    RAIZ / "sql"
    / "02_consulta_parametrizada.sql"
)


# 2. DEFINIR OS PARAMETROS


competencia = "2024-10"
natureza = "Carga Conteinerizada"



# 3. VALIDAR OS ARQUIVOS

if not BANCO.is_file():
    raise FileNotFoundError(BANCO)

if not ARQUIVO_SQL.is_file():
    raise FileNotFoundError(ARQUIVO_SQL)


# 4. LER A CONSULTA SQL

consulta = ARQUIVO_SQL.read_text(
    encoding="utf-8"
)


# 5. EXECUTAR NO SQLITE

conexao = sqlite3.connect(
    BANCO.as_uri() + "?mode=ro",
    uri=True
)

try:

    parametros = {
        "competencia": competencia,
        "natureza": natureza
    }

    resultado = pd.read_sql_query(
        consulta,
        conexao,
        params=parametros
    )

    print("=" * 50)
    print("CONSULTA PARAMETRIZADA")
    print("=" * 50)

    print("Competencia:", competencia)
    print("Natureza:", natureza)

    print("\nRESULTADO:")

    if resultado.empty:
        print("Nenhum registro encontrado.")
    else:
        print(resultado.to_string(index=False))

finally:
    conexao.close()
