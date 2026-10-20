
# ============================================================
# PROJETO ED-ANTAQ-01
# AULA 21 - PARTE 5
# CRIAR DIMENSAO DE ATRACACOES NO BANCO DE TESTE
# ============================================================

from pathlib import Path
import sqlite3
import argparse
import pandas as pd


# 1. CAMINHOS

RAIZ = Path(__file__).resolve().parents[1]

ARQUIVO_ORIGEM = (
    RAIZ / "data" / "raw" / "2024Atracacao.txt"
)


# Selecionar o ambiente pelo terminal

parser = argparse.ArgumentParser(
    description="Criar dimensao de atracacoes ANTAQ"
)

parser.add_argument(
    "--banco",
    choices=["staging", "reprocessamento"],
    required=True,
    help="Banco de destino"
)

argumentos = parser.parse_args()

PASTA_DATABASE = RAIZ / "data" / "database"

BANCOS = {
    "staging": (
        PASTA_DATABASE / "antaq_santos_staging.db"
    ),
    "reprocessamento": (
        PASTA_DATABASE / "antaq_santos_reprocessamento.db"
    )
}

BANCO_TESTE = BANCOS[argumentos.banco]

print("Ambiente selecionado:", argumentos.banco)



TOTAL_ESPERADO = 6292


# 2. VERIFICAR ARQUIVOS

if not ARQUIVO_ORIGEM.is_file():
    raise FileNotFoundError(ARQUIVO_ORIGEM)

if not BANCO_TESTE.is_file():
    raise FileNotFoundError(BANCO_TESTE)


# 3. EXTRAIR ATRACACOES

print("1. Lendo arquivo original...")

df = pd.read_csv(
    ARQUIVO_ORIGEM,
    sep=";",
    encoding="utf-8-sig",
    dtype={"IDAtracacao": "string"},
    low_memory=False
)

# Selecionar o Complexo Portuario de Santos
df = df.loc[
    df["Complexo Portuário"] == "Santos"
].copy()

print("Atracacoes de Santos:", len(df))


# 4. VALIDAR IDENTIFICADORES

assert len(df) == TOTAL_ESPERADO

assert df["IDAtracacao"].notna().all()

assert df["IDAtracacao"].is_unique


# 5. TRATAR A DATA

df["DataConvertida"] = pd.to_datetime(
    df["Data Atracação"],
    format="%d/%m/%Y %H:%M:%S",
    errors="coerce"
)

falhas_conversao = (
    df["Data Atracação"].notna()
    & df["DataConvertida"].isna()
).sum()

if falhas_conversao > 0:
    raise ValueError(
        f"Falhas na conversao de datas: {falhas_conversao}"
    )

df["DataAtracacao"] = (
    df["DataConvertida"]
    .dt.strftime("%Y-%m-%d %H:%M:%S")
)

df["Competencia"] = (
    df["DataConvertida"]
    .dt.strftime("%Y-%m")
)

if df["Competencia"].isna().any():
    raise ValueError(
        "Existem competencias ausentes em Santos."
    )


# 6. SELECIONAR E RENOMEAR COLUNAS

df_sql = df[
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

df_sql = df_sql.astype(object).where(
    pd.notna(df_sql), None
)

registros = list(
    df_sql.itertuples(index=False, name=None)
)


# 7. INSERIR NO BANCO DE REPROCESSAMENTO

print("\n2. Conectando ao banco de teste...")

conexao = sqlite3.connect(BANCO_TESTE, timeout=30)

try:

    # Impedir sobrescrita de uma dimensao existente
    existe = conexao.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'atracacoes'
    """).fetchone()

    if existe is not None:
        raise RuntimeError(
            "A tabela atracacoes ja existe no banco "
            "de teste. Nenhuma alteracao foi realizada."
        )

    conexao.execute("BEGIN")

    conexao.execute("""
        CREATE TABLE atracacoes (
            IDAtracacao TEXT PRIMARY KEY,
            PortoAtracacao TEXT,
            Instalacao TEXT,
            ComplexoPortuario TEXT,
            DataAtracacao TEXT,
            Competencia TEXT
        )
    """)

    conexao.executemany("""
        INSERT INTO atracacoes (
            IDAtracacao,
            PortoAtracacao,
            Instalacao,
            ComplexoPortuario,
            DataAtracacao,
            Competencia
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, registros)

    # 8. CONFERIR A DIMENSAO
    total, competencias_ausentes = conexao.execute("""
        SELECT
            COUNT(*),
            SUM(
                CASE
                    WHEN Competencia IS NULL THEN 1
                    ELSE 0
                END
            )
        FROM atracacoes
    """).fetchone()

    assert total == TOTAL_ESPERADO
    assert competencias_ausentes == 0

    # 9. VERIFICAR AS CARGAS SEM ATRACACAO
    sem_correspondencia = conexao.execute("""
        SELECT COUNT(*)
        FROM carga_santos AS c
        LEFT JOIN atracacoes AS a
            ON c.IDAtracacao = a.IDAtracacao
        WHERE a.IDAtracacao IS NULL
    """).fetchone()[0]

    assert sem_correspondencia == 0, (
        "Existem cargas sem atracacao."
    )

    conexao.commit()

    print("\n" + "=" * 50)
    print("RESUMO DA DIMENSAO - BANCO DE TESTE")
    print("=" * 50)

    print("Atracacoes carregadas:", total)
    print("Competencias ausentes:", competencias_ausentes)
    print("Cargas sem atracacao:", sem_correspondencia)

    print("\nDIMENSAO VALIDADA COM SUCESSO.")

except Exception:
    conexao.rollback()
    print("\nErro. Transacao revertida.")
    raise

finally:
    conexao.close()
