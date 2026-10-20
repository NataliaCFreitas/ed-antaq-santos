
# ============================================================
# ED-ANTAQ-01
# AULA 22 - PARTE 3
# PREPARACAO SEGURA DO BANCO STAGING
# ============================================================

from pathlib import Path
import sqlite3


# 1. LOCALIZAR O PROJETO

RAIZ = Path(__file__).resolve().parents[1]

PASTA_DATABASE = RAIZ / "data" / "database"

BANCO_PRINCIPAL = (
    PASTA_DATABASE / "antaq_santos_pipeline.db"
)

BANCO_TESTE = (
    PASTA_DATABASE / "antaq_santos_reprocessamento.db"
)

BANCO_STAGING = (
    PASTA_DATABASE / "antaq_santos_staging.db"
)


# 2. VALIDAR OS AMBIENTES EXISTENTES

print("=" * 55)
print("ED-ANTAQ-01 - PREPARACAO DO STAGING")
print("=" * 55)

for banco in [BANCO_PRINCIPAL, BANCO_TESTE]:

    if not banco.is_file():
        raise FileNotFoundError(
            f"Banco nao encontrado: {banco}"
        )

print("\nBanco principal: encontrado")
print("Banco de teste: encontrado")


# 3. PROTEGER CONTRA SOBRESCRITA

if BANCO_STAGING.exists():
    raise FileExistsError(
        "O banco staging ja existe. "
        "Nenhuma alteracao foi realizada."
    )


# 4. CRIAR O NOVO BANCO

print("\nCriando banco staging...")

conexao = sqlite3.connect(BANCO_STAGING)

try:

    conexao.execute("BEGIN")

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

    conexao.execute("""
        CREATE INDEX idx_carga_santos_idatracacao
        ON carga_santos (IDAtracacao)
    """)

    conexao.commit()

    total = conexao.execute("""
        SELECT COUNT(*)
        FROM carga_santos
    """).fetchone()[0]

    tabelas = conexao.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
    """).fetchall()

    print("\nBANCO STAGING CRIADO")
    print("Arquivo:", BANCO_STAGING.name)
    print("Tabelas:", [item[0] for item in tabelas])
    print("Registros:", total)
    print("Status: OK")

except Exception:

    conexao.rollback()

    if BANCO_STAGING.exists():
        conexao.close()
        BANCO_STAGING.unlink()

    raise

finally:

    conexao.close()


# 5. RESUMO

print("\nBanco principal: preservado")
print("Banco de teste: preservado")
print("Banco staging: pronto para receber dados")
