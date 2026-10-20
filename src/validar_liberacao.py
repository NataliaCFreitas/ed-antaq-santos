
# ============================================================
# ED-ANTAQ-01
# AULA 23 - PARTE 3
# CONTROLE DE QUALIDADE ANTES DA PUBLICACAO
# ============================================================

from pathlib import Path
import subprocess
import sqlite3
import sys
import math
import time
import logging


# 1. CONFIGURACOES

RAIZ = Path(__file__).resolve().parents[1]

PASTA_DATABASE = RAIZ / "data" / "database"

BANCO_CANDIDATO = (
    PASTA_DATABASE / "antaq_santos_candidato.db"
)

BANCO_PUBLICADO = (
    PASTA_DATABASE / "antaq_santos_publicado.db"
)

PASTA_LOGS = RAIZ / "logs"

PASTA_LOGS.mkdir(
    parents=True,
    exist_ok=True
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            PASTA_LOGS / "validacao_liberacao.log",
            encoding="utf-8"
        )
    ]
)


# 2. EXECUTAR TESTES AUTOMATIZADOS

def executar_testes():

    logging.info("ETAPA 1 - EXECUTAR TESTES")

    comando = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-p",
        "test_*.py",
        "-v"
    ]

    resultado = subprocess.run(
        comando,
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if resultado.stdout.strip():
        logging.info(resultado.stdout.strip())

    if resultado.stderr.strip():
        logging.info(resultado.stderr.strip())

    if resultado.returncode != 0:
        raise RuntimeError(
            "A suíte de testes apresentou falhas."
        )

    logging.info("Testes automatizados: APROVADOS")


# 3. CONSULTAR UM BANCO SOMENTE PARA LEITURA

def consultar_banco(caminho):

    if not caminho.is_file():
        raise FileNotFoundError(
            f"Banco nao encontrado: {caminho}"
        )

    conexao = sqlite3.connect(
        caminho.resolve().as_uri() + "?mode=ro",
        uri=True
    )

    try:

        integridade = conexao.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        if integridade != "ok":
            raise AssertionError(
                f"Falha de integridade: {caminho.name}"
            )

        cargas, peso = conexao.execute("""
            SELECT COUNT(*), SUM(PesoBruto)
            FROM carga_santos
        """).fetchone()

        atracacoes = conexao.execute("""
            SELECT COUNT(*)
            FROM atracacoes
        """).fetchone()[0]

        gold = conexao.execute("""
            SELECT
                Competencia,
                SUM(QtdRegistrosCarga),
                SUM(PesoBrutoTotal)
            FROM gold_movimentacao_mensal
            GROUP BY Competencia
            ORDER BY Competencia
        """).fetchall()

        meses, registros_view = conexao.execute("""
            SELECT
                COUNT(DISTINCT Competencia),
                SUM(QtdRegistrosCarga)
            FROM vw_movimentacao_2024
        """).fetchone()

        return {
            "cargas": cargas,
            "peso": peso,
            "atracacoes": atracacoes,
            "gold": gold,
            "meses": meses,
            "registros_view": registros_view
        }

    finally:
        conexao.close()


# 4. COMPARAR CANDIDATO E PUBLICADO

def comparar_bancos():

    logging.info(
        "ETAPA 2 - VALIDAR E COMPARAR BANCOS"
    )

    candidato = consultar_banco(BANCO_CANDIDATO)
    publicado = consultar_banco(BANCO_PUBLICADO)

    for campo in [
        "cargas",
        "atracacoes",
        "meses",
        "registros_view"
    ]:

        if candidato[campo] != publicado[campo]:
            raise AssertionError(
                f"Divergencia no indicador: {campo}"
            )

    if not math.isclose(
        candidato["peso"],
        publicado["peso"],
        rel_tol=0,
        abs_tol=0.01
    ):
        raise AssertionError(
            "Divergencia no peso bruto total."
        )

    gold_candidato = candidato["gold"]
    gold_publicado = publicado["gold"]

    if len(gold_candidato) != len(gold_publicado):
        raise AssertionError(
            "Quantidade de competencias divergente."
        )

    for linha_c, linha_p in zip(
        gold_candidato,
        gold_publicado
    ):

        competencia_c, registros_c, peso_c = linha_c
        competencia_p, registros_p, peso_p = linha_p

        if (
            competencia_c != competencia_p
            or registros_c != registros_p
        ):
            raise AssertionError(
                "Divergencia na serie mensal."
            )

        if not math.isclose(
            peso_c,
            peso_p,
            rel_tol=0,
            abs_tol=0.01
        ):
            raise AssertionError(
                f"Peso mensal divergente: {competencia_c}"
            )

    logging.info(
        "Cargas: %s",
        candidato["cargas"]
    )

    logging.info(
        "Atracacoes: %s",
        candidato["atracacoes"]
    )

    logging.info(
        "Competencias Gold: %s",
        len(gold_candidato)
    )

    logging.info(
        "Comparacao entre bancos: APROVADA"
    )


# 5. EXECUTAR CONTROLE DE LIBERACAO

def main():

    inicio = time.perf_counter()

    logging.info("=" * 55)
    logging.info("ED-ANTAQ-01 - CONTROLE DE LIBERACAO")
    logging.info("=" * 55)

    try:

        executar_testes()
        comparar_bancos()

    except Exception:

        logging.exception(
            "LIBERACAO REPROVADA"
        )

        sys.exit(1)

    duracao = time.perf_counter() - inicio

    logging.info("=" * 55)
    logging.info("LIBERACAO APROVADA")
    logging.info(
        "Tempo total: %.2f segundos",
        duracao
    )
    logging.info("=" * 55)


if __name__ == "__main__":
    main()
