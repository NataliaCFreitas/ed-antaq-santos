
# ============================================================
# ED-ANTAQ-01
# AULA 22 - PARTE 9
# RECONSTRUCAO INTEGRADA DO PIPELINE
# ============================================================

from pathlib import Path
import sqlite3
import time
import math
import sys

import pandas as pd

from load import (
    preparar_valores,
    SQL_INSERT,
    COLUNAS_ORIGEM,
    TAMANHO_BLOCO,
)


# 1. CONFIGURACOES

RAIZ = Path(__file__).resolve().parents[1]

SILVER = (
    RAIZ / "data" / "silver"
    / "2024Carga_ComplexoSantos.csv"
)

ARQUIVO_ATRACACOES = (
    RAIZ / "data" / "raw"
    / "2024Atracacao.txt"
)

PASTA_BANCO = RAIZ / "data" / "database"

BANCO_PRINCIPAL = (
    PASTA_BANCO / "antaq_santos_pipeline.db"
)

BANCO_CANDIDATO = (
    PASTA_BANCO / "antaq_santos_candidato.db"
)

TOTAL_CARGAS = 760354
TOTAL_ATRACACOES = 6292
PESO_CARGAS = 177073928.08
REGISTROS_2024 = 757413
PESO_2024 = 175853477.31


def informar(mensagem):
    print(mensagem, flush=True)


def verificar_arquivos():

    for arquivo in [
        SILVER,
        ARQUIVO_ATRACACOES,
        BANCO_PRINCIPAL,
    ]:
        if not arquivo.is_file():
            raise FileNotFoundError(arquivo)

    if BANCO_CANDIDATO.exists():
        raise FileExistsError(
            "O banco candidato ja existe. "
            "Nenhum arquivo sera sobrescrito."
        )


# 2. PREPARAR TABELA DE CARGAS

def criar_tabela_cargas(conexao):

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


def carregar_cargas(conexao):

    informar("\nETAPA 1 - CARREGAR SILVER")

    leitor = pd.read_csv(
        SILVER,
        sep=";",
        encoding="utf-8",
        usecols=COLUNAS_ORIGEM,
        dtype="string",
        chunksize=TAMANHO_BLOCO,
    )

    total = 0

    for numero, bloco in enumerate(leitor, start=1):

        registros = preparar_valores(bloco)

        conexao.executemany(
            SQL_INSERT,
            registros
        )

        total += len(registros)

        informar(
            f"Bloco {numero}: "
            f"{len(registros)} registros | "
            f"Acumulado: {total}"
        )

    if total != TOTAL_CARGAS:
        raise AssertionError(
            f"Quantidade de cargas divergente: {total}"
        )

    conexao.execute("""
        CREATE INDEX idx_carga_santos_idatracacao
        ON carga_santos (IDAtracacao)
    """)

    informar("Carga Silver: OK")


# 3. CRIAR DIMENSAO DE ATRACACOES

def carregar_atracacoes(conexao):

    informar("\nETAPA 2 - CARREGAR ATRACACOES")

    df = pd.read_csv(
        ARQUIVO_ATRACACOES,
        sep=";",
        encoding="utf-8-sig",
        dtype={"IDAtracacao": "string"},
        low_memory=False,
    )

    df = df.loc[
        df["Complexo Portuário"] == "Santos"
    ].copy()

    if len(df) != TOTAL_ATRACACOES:
        raise AssertionError(
            "Quantidade de atracacoes divergente."
        )

    if (
        df["IDAtracacao"].isna().any()
        or not df["IDAtracacao"].is_unique
    ):
        raise AssertionError(
            "Identificadores de atracacao invalidos."
        )

    datas = pd.to_datetime(
        df["Data Atracação"],
        format="%d/%m/%Y %H:%M:%S",
        errors="coerce",
    )

    if datas.isna().any():
        raise AssertionError(
            "Existem datas de atracacao invalidas."
        )

    df["DataAtracacao"] = (
        datas.dt.strftime("%Y-%m-%d %H:%M:%S")
    )

    df["Competencia"] = (
        datas.dt.strftime("%Y-%m")
    )

    df = df[
        [
            "IDAtracacao",
            "Porto Atracação",
            "Apelido Instalação Portuária",
            "Complexo Portuário",
            "DataAtracacao",
            "Competencia",
        ]
    ].copy()

    df = df.astype(object).where(
        pd.notna(df),
        None
    )

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
        INSERT INTO atracacoes
        VALUES (?, ?, ?, ?, ?, ?)
    """, df.itertuples(index=False, name=None))

    informar(
        f"Atracacoes carregadas: {len(df)}"
    )


# 4. CRIAR GOLD

def criar_gold(conexao):

    informar("\nETAPA 3 - CRIAR GOLD")

    conexao.execute("""
        CREATE TABLE gold_movimentacao_mensal AS
        SELECT
            a.Competencia AS Competencia,
            a.PortoAtracacao AS PortoAtracacao,
            c.NaturezaCarga AS NaturezaCarga,
            c.Sentido AS Sentido,
            COUNT(*) AS QtdRegistrosCarga,
            SUM(c.PesoBruto) AS PesoBrutoTotal
        FROM carga_santos AS c
        INNER JOIN atracacoes AS a
            ON c.IDAtracacao = a.IDAtracacao
        GROUP BY
            a.Competencia,
            a.PortoAtracacao,
            c.NaturezaCarga,
            c.Sentido
    """)

    informar("Gold criada: OK")


# 5. CRIAR VIEW 2024

def criar_view(conexao):

    informar("\nETAPA 4 - CRIAR VIEW 2024")

    conexao.execute("""
        CREATE VIEW vw_movimentacao_2024 AS
        SELECT
            Competencia,
            PortoAtracacao,
            NaturezaCarga,
            Sentido,
            QtdRegistrosCarga,
            PesoBrutoTotal
        FROM gold_movimentacao_mensal
        WHERE Competencia >= '2024-01'
          AND Competencia < '2025-01'
    """)

    informar("VIEW criada: OK")


# 6. EXECUTAR QUALITY GATE

def validar(conexao):

    informar("\nETAPA 5 - QUALITY GATE")

    cargas, peso = conexao.execute("""
        SELECT COUNT(*), SUM(PesoBruto)
        FROM carga_santos
    """).fetchone()

    atracacoes = conexao.execute("""
        SELECT COUNT(*) FROM atracacoes
    """).fetchone()[0]

    sem_vinculo = conexao.execute("""
        SELECT COUNT(*)
        FROM carga_santos AS c
        LEFT JOIN atracacoes AS a
            ON c.IDAtracacao = a.IDAtracacao
        WHERE a.IDAtracacao IS NULL
    """).fetchone()[0]

    gold_registros, gold_peso = conexao.execute("""
        SELECT
            SUM(QtdRegistrosCarga),
            SUM(PesoBrutoTotal)
        FROM gold_movimentacao_mensal
    """).fetchone()

    meses, view_registros, view_peso = conexao.execute("""
        SELECT
            COUNT(DISTINCT Competencia),
            SUM(QtdRegistrosCarga),
            SUM(PesoBrutoTotal)
        FROM vw_movimentacao_2024
    """).fetchone()

    if cargas != TOTAL_CARGAS:
        raise AssertionError("Cargas divergentes.")

    if atracacoes != TOTAL_ATRACACOES:
        raise AssertionError("Atracacoes divergentes.")

    if sem_vinculo != 0:
        raise AssertionError("Cargas sem atracacao.")

    if gold_registros != cargas:
        raise AssertionError("Gold nao reconciliada.")

    if meses != 12 or view_registros != REGISTROS_2024:
        raise AssertionError("VIEW 2024 divergente.")

    for encontrado, esperado, descricao in [
        (peso, PESO_CARGAS, "Peso das cargas"),
        (gold_peso, PESO_CARGAS, "Peso Gold"),
        (view_peso, PESO_2024, "Peso VIEW"),
    ]:
        if encontrado is None or not math.isclose(
            encontrado,
            esperado,
            rel_tol=0,
            abs_tol=0.05,
        ):
            raise AssertionError(
                f"{descricao} divergente."
            )

    # Comparar todas as competencias com a referencia
    referencia = sqlite3.connect(
        BANCO_PRINCIPAL.resolve().as_uri() + "?mode=ro",
        uri=True,
    )

    try:
        sql = """
            SELECT
                Competencia,
                SUM(QtdRegistrosCarga),
                SUM(PesoBrutoTotal)
            FROM gold_movimentacao_mensal
            GROUP BY Competencia
        """

        mensal_principal = {
            linha[0]: (linha[1], linha[2])
            for linha in referencia.execute(sql)
        }

    finally:
        referencia.close()

    mensal_candidato = {
        linha[0]: (linha[1], linha[2])
        for linha in conexao.execute(sql)
    }

    if mensal_principal.keys() != mensal_candidato.keys():
        raise AssertionError(
            "Competencias diferentes entre os bancos."
        )

    for competencia, valores in mensal_principal.items():

        registros_ref, peso_ref = valores

        registros_novo, peso_novo = (
            mensal_candidato[competencia]
        )

        if registros_ref != registros_novo:
            raise AssertionError(
                f"Registros divergentes: {competencia}"
            )

        if not math.isclose(
            peso_ref,
            peso_novo,
            rel_tol=0,
            abs_tol=0.05,
        ):
            raise AssertionError(
                f"Peso divergente: {competencia}"
            )

    informar(f"Cargas: {cargas}")
    informar(f"Atracacoes: {atracacoes}")
    informar(f"Competencias Gold: {len(mensal_candidato)}")
    informar(f"Registros VIEW 2024: {view_registros}")
    informar("Quality Gate: APROVADO")


# 7. EXECUCAO INTEGRADA

def main():

    inicio = time.perf_counter()

    informar("=" * 55)
    informar("ED-ANTAQ-01 - RECONSTRUCAO INTEGRADA")
    informar("=" * 55)

    verificar_arquivos()

    conexao = sqlite3.connect(
        BANCO_CANDIDATO,
        timeout=30,
    )

    try:
        conexao.execute("BEGIN")

        criar_tabela_cargas(conexao)
        carregar_cargas(conexao)
        carregar_atracacoes(conexao)
        criar_gold(conexao)
        criar_view(conexao)
        validar(conexao)

        conexao.commit()

        integridade = conexao.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        if integridade != "ok":
            raise AssertionError(
                "Falha de integridade SQLite."
            )

    except Exception:

        conexao.rollback()
        informar("\nPIPELINE REPROVADO")
        raise

    finally:
        conexao.close()

    duracao = time.perf_counter() - inicio

    informar("\n" + "=" * 55)
    informar("PIPELINE CONCLUIDO COM SUCESSO")
    informar(f"Tempo total: {duracao:.2f} segundos")
    informar("Banco candidato validado.")
    informar("Bancos existentes preservados.")
    informar("=" * 55)


if __name__ == "__main__":

    try:
        main()

    except Exception as erro:
        print(f"\nERRO: {erro}", file=sys.stderr)
        sys.exit(1)
