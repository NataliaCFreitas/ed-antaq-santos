
# ============================================================
# PROJETO ED-ANTAQ-01
# CRIACAO DE INDICES PARA CONSULTAS SQL
# ============================================================

from pathlib import Path
import sqlite3

RAIZ = Path(__file__).resolve().parents[1]

BANCO = (
    RAIZ / "data" / "database"
    / "antaq_santos_pipeline.db"
)

if not BANCO.is_file():
    raise FileNotFoundError(
        f"Banco nao encontrado: {BANCO}"
    )

print("Conectando ao SQLite...")

with sqlite3.connect(BANCO, timeout=30) as conexao:

    print("Criando indice para IDAtracacao...")

    conexao.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_carga_santos_idatracacao
        ON carga_santos (IDAtracacao)
    """)

    print("Indice criado ou ja existente.")

    print("\nIndices disponiveis:")

    indices = conexao.execute("""
        PRAGMA index_list('carga_santos')
    """).fetchall()

    for indice in indices:
        print(indice[1])

print("\nOperacao concluida.")
