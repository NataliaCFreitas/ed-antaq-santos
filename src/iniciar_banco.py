
# ============================================================
# PROJETO ED-ANTAQ-01
# AULA 17 - PARTE 1
# INICIALIZACAO DO BANCO SQLITE LOCAL
# ============================================================

from pathlib import Path
import sqlite3

# Localizar a pasta do projeto
RAIZ = Path(__file__).resolve().parents[1]

# Definir o local do novo banco
PASTA_BANCO = RAIZ / "data" / "database"
PASTA_BANCO.mkdir(parents=True, exist_ok=True)

CAMINHO_BANCO = (
    PASTA_BANCO / "antaq_santos_pipeline.db"
)

# Abrir a conexao
with sqlite3.connect(CAMINHO_BANCO) as conexao:

    # Criar uma tabela vazia, caso ainda nao exista
    conexao.execute("""
        CREATE TABLE IF NOT EXISTS carga_santos (
            IDCarga TEXT PRIMARY KEY,
            IDAtracacao TEXT NOT NULL,
            CDMercadoria TEXT,
            TipoOperacao TEXT,
            NaturezaCarga TEXT,
            Sentido TEXT,
            TEU INTEGER,
            QTCarga INTEGER,
            PesoBruto REAL
        )
    """)

print("Banco SQLite inicializado com sucesso.")
print("Caminho:", CAMINHO_BANCO)
