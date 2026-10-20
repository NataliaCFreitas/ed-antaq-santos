
# ============================================================
# PROJETO ED-ANTAQ-01
# AULA 21 - PARTE 2
# PREPARACAO DO AMBIENTE DE REPROCESSAMENTO
# ============================================================

from pathlib import Path
import sqlite3


# 1. LOCALIZAR A PASTA DO PROJETO

RAIZ = Path(__file__).resolve().parents[1]

PASTA_BANCO = RAIZ / "data" / "database"

BANCO_PRINCIPAL = (
    PASTA_BANCO / "antaq_santos_pipeline.db"
)

BANCO_TESTE = (
    PASTA_BANCO / "antaq_santos_reprocessamento.db"
)


# 2. VALIDAR O BANCO PRINCIPAL

if not BANCO_PRINCIPAL.is_file():
    raise FileNotFoundError(
        "Banco principal nao encontrado."
    )


# 3. IMPEDIR SOBRESCRITA DO BANCO DE TESTE

if BANCO_TESTE.exists():
    raise FileExistsError(
        "O banco de reprocessamento ja existe. "
        "Nenhuma alteracao foi realizada."
    )


# 4. CRIAR A TABELA VAZIA DE CARGAS

print("Preparando ambiente de reprocessamento...")

with sqlite3.connect(BANCO_TESTE) as conexao:

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

    total = conexao.execute("""
        SELECT COUNT(*)
        FROM carga_santos
    """).fetchone()[0]


# 5. APRESENTAR RESULTADO

print("\nBANCO DE TESTE CRIADO")
print("Caminho:", BANCO_TESTE)
print("Registros existentes:", total)

print("\nBanco principal preservado.")
print("Preparacao concluida.")
