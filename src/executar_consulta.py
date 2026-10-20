
# ============================================================
# PROJETO ED-ANTAQ-01
# AULA 20 - EXECUCAO DE CONSULTAS SQL EXTERNAS
# ============================================================

from pathlib import Path
import sqlite3
import pandas as pd


# 1. LOCALIZAR A RAIZ DO PROJETO

RAIZ = Path(__file__).resolve().parents[1]


# 2. DEFINIR OS CAMINHOS

BANCO = (
    RAIZ
    / "data"
    / "database"
    / "antaq_santos_pipeline.db"
)

ARQUIVO_SQL = (
    RAIZ
    / "sql"
    / "01_resumo_mensal_2024.sql"
)


# 3. VERIFICAR A EXISTENCIA DOS ARQUIVOS

if not BANCO.is_file():
    raise FileNotFoundError(
        f"Banco nao encontrado: {BANCO}"
    )

if not ARQUIVO_SQL.is_file():
    raise FileNotFoundError(
        f"Arquivo SQL nao encontrado: {ARQUIVO_SQL}"
    )


# 4. LER A CONSULTA SQL

consulta = ARQUIVO_SQL.read_text(
    encoding="utf-8"
)

print("Arquivo SQL carregado com sucesso.")


# 5. ABRIR O BANCO SOMENTE PARA LEITURA

conexao = sqlite3.connect(
    BANCO.as_uri() + "?mode=ro",
    uri=True
)

try:

    # 6. EXECUTAR A CONSULTA
    resultado = pd.read_sql_query(
        consulta,
        conexao
    )

    # 7. MOSTRAR O RESULTADO
    print("\nRESUMO MENSAL - 2024")
    print("=" * 45)

    print(
        resultado.to_string(index=False)
    )

    # 8. CONTROLE SIMPLES
    assert len(resultado) == 12, (
        "A consulta nao retornou 12 competencias."
    )

    print("\nConsulta executada e validada.")

finally:

    conexao.close()
