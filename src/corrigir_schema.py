
# ============================================================
# PROJETO ED-ANTAQ-01
# CORRECAO DO ESQUEMA DA TABELA CARGA_SANTOS
# ============================================================

from pathlib import Path
import sqlite3

RAIZ = Path(__file__).resolve().parents[1]

BANCO = RAIZ / "data" / "database" / "antaq_santos_pipeline.db"

if not BANCO.is_file():
    raise FileNotFoundError(f"Banco nao encontrado: {BANCO}")

conexao = sqlite3.connect(BANCO)

try:
    tabela = conexao.execute("""
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name = 'carga_santos'
    """).fetchone()

    if tabela is None:
        raise RuntimeError("Tabela carga_santos nao encontrada.")

    quantidade = conexao.execute(
        "SELECT COUNT(*) FROM carga_santos"
    ).fetchone()[0]

    if quantidade != 0:
        raise RuntimeError(
            f"A tabela contem {quantidade} registros. "
            "Correcao automatica cancelada."
        )

    with conexao:
        conexao.execute("DROP TABLE carga_santos")

        conexao.execute("""
            CREATE TABLE carga_santos (
                IDCarga TEXT PRIMARY KEY,
                IDAtracacao TEXT NOT NULL,
                CDMercadoria TEXT,
                TipoOperacao TEXT,
                NaturezaCarga TEXT,
                Sentido TEXT,
                TEU REAL,
                QTCarga INTEGER,
                PesoBruto REAL
            )
        """)

    print("Estrutura corrigida com sucesso.")

    for coluna in conexao.execute(
        "PRAGMA table_info(carga_santos)"
    ).fetchall():
        print(coluna[1], "-", coluna[2])

finally:
    conexao.close()
