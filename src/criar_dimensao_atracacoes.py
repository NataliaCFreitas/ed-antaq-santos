
# ============================================================
# PROJETO ED-ANTAQ-01
# AULA 18 - PARTE 2
# CRIACAO DA DIMENSAO DE ATRACACOES
# ============================================================

from pathlib import Path
import sqlite3
import pandas as pd


# 1. DEFINIR CAMINHOS

RAIZ = Path(__file__).resolve().parents[1]

ARQUIVO_ATRACACOES = (
    RAIZ / "data" / "raw" / "2024Atracacao.txt"
)

ARQUIVO_BANCO = (
    RAIZ / "data" / "database"
    / "antaq_santos_pipeline.db"
)

if not ARQUIVO_ATRACACOES.is_file():
    raise FileNotFoundError(
        f"Arquivo nao encontrado: {ARQUIVO_ATRACACOES}"
    )

if not ARQUIVO_BANCO.is_file():
    raise FileNotFoundError(
        f"Banco nao encontrado: {ARQUIVO_BANCO}"
    )


# 2. EXTRAIR AS ATRACACOES

print("1. Lendo atracacoes...")

df = pd.read_csv(
    ARQUIVO_ATRACACOES,
    sep=";",
    encoding="utf-8-sig",
    dtype={"IDAtracacao": "string"},
    low_memory=False
)

print("Atracacoes nacionais:", len(df))


# 3. SELECIONAR O COMPLEXO DE SANTOS

df_santos = df.loc[
    df["Complexo Portuário"] == "Santos"
].copy()

print("Atracacoes de Santos:", len(df_santos))


# 4. VALIDAR IDENTIFICADORES

assert df_santos["IDAtracacao"].notna().all(), (
    "Existem atracacoes sem identificador."
)

assert df_santos["IDAtracacao"].is_unique, (
    "IDAtracacao duplicado na dimensao."
)


# 5. CONVERTER DATA DE ATRACACAO

df_santos["DataAtracacaoConvertida"] = pd.to_datetime(
    df_santos["Data Atracação"],
    format="%d/%m/%Y %H:%M:%S",
    errors="coerce"
)

falhas_data = (
    df_santos["Data Atracação"].notna()
    & df_santos["DataAtracacaoConvertida"].isna()
).sum()

if falhas_data > 0:
    raise ValueError(
        f"Falhas de conversao de data: {falhas_data}"
    )

df_santos["DataAtracacao"] = (
    df_santos["DataAtracacaoConvertida"]
    .dt.strftime("%Y-%m-%d %H:%M:%S")
)

df_santos["Competencia"] = (
    df_santos["DataAtracacaoConvertida"]
    .dt.strftime("%Y-%m")
)


# 6. PREPARAR COLUNAS PARA O BANCO

df_sql = df_santos[
    [
        "IDAtracacao",
        "Porto Atracação",
        "Apelido Instalação Portuária",
        "Complexo Portuário",
        "DataAtracacao",
        "Competencia"
    ]
].copy()

df_sql = df_sql.rename(
    columns={
        "Porto Atracação": "PortoAtracacao",
        "Apelido Instalação Portuária": "Instalacao",
        "Complexo Portuário": "ComplexoPortuario"
    }
)

# Converter valores ausentes em NULL
df_sql = df_sql.astype(object).where(
    pd.notna(df_sql), None
)


# 7. PREPARAR INSERCAO SQL

SQL_INSERT = """
INSERT INTO atracacoes (
    IDAtracacao,
    PortoAtracacao,
    Instalacao,
    ComplexoPortuario,
    DataAtracacao,
    Competencia
)
VALUES (?, ?, ?, ?, ?, ?)
"""

registros = list(
    df_sql.itertuples(
        index=False,
        name=None
    )
)


# 8. CRIAR A TABELA NO SQLITE

conexao = sqlite3.connect(ARQUIVO_BANCO)

try:

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS atracacoes (
            IDAtracacao TEXT PRIMARY KEY,
            PortoAtracacao TEXT,
            Instalacao TEXT,
            ComplexoPortuario TEXT,
            DataAtracacao TEXT,
            Competencia TEXT
        )
    """)

    conexao.commit()

    # Evitar duplicacao em nova execucao
    quantidade_existente = conexao.execute(
        "SELECT COUNT(*) FROM atracacoes"
    ).fetchone()[0]

    if quantidade_existente > 0:
        raise RuntimeError(
            "A tabela atracacoes ja possui "
            f"{quantidade_existente} registros. "
            "Carga cancelada para evitar duplicacao."
        )

    # Abrir transacao
    conexao.execute("BEGIN")

    conexao.executemany(
        SQL_INSERT,
        registros
    )

    # Validar quantidade antes do COMMIT
    total_banco = conexao.execute(
        "SELECT COUNT(*) FROM atracacoes"
    ).fetchone()[0]

    if total_banco != len(df_sql):
        raise ValueError(
            "Divergencia na quantidade de atracacoes."
        )

    conexao.commit()

    print("\n2. RESUMO DA DIMENSAO")
    print("Registros inseridos:", total_banco)
    print(
        "Competencias ausentes:",
        df_santos["Competencia"].isna().sum()
    )

    print("\nDimensao criada com sucesso.")

except Exception:

    conexao.rollback()
    raise

finally:

    conexao.close()
