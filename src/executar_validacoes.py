
# ============================================================
# ED-ANTAQ-01
# AULA 22 - PARTE 2
# ORQUESTRACAO DE VALIDACOES COM LOGS
# ============================================================

from pathlib import Path
import subprocess
import sys
import time
import logging


# 1. CONFIGURACOES

RAIZ = Path(__file__).resolve().parents[1]

PASTA_SRC = RAIZ / "src"
PASTA_LOGS = RAIZ / "logs"

PASTA_LOGS.mkdir(
    parents=True,
    exist_ok=True
)

ARQUIVO_LOG = (
    PASTA_LOGS / "pipeline_validacoes.log"
)


# 2. CONFIGURAR O REGISTRO DE LOGS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(
            ARQUIVO_LOG,
            encoding="utf-8"
        ),
        logging.StreamHandler(sys.stdout)
    ]
)


# 3. DEFINIR A SEQUENCIA

ETAPAS = [
    "pipeline.py",
    "comparar_bancos.py"
]


# 4. EXECUTAR UMA ETAPA

def executar_etapa(nome_script):

    caminho = PASTA_SRC / nome_script

    if not caminho.is_file():
        raise FileNotFoundError(
            f"Script nao encontrado: {caminho}"
        )

    logging.info(
        "INICIANDO: %s",
        nome_script
    )

    inicio = time.perf_counter()

    resultado = subprocess.run(
        [
            sys.executable,
            str(caminho)
        ],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    duracao = time.perf_counter() - inicio

    if resultado.stdout.strip():
        logging.info(
            "SAIDA DE %s:\n%s",
            nome_script,
            resultado.stdout.strip()
        )

    if resultado.stderr.strip():
        logging.warning(
            "MENSAGENS DE %s:\n%s",
            nome_script,
            resultado.stderr.strip()
        )

    if resultado.returncode != 0:
        logging.error(
            "FALHA: %s | Codigo: %s | Tempo: %.2fs",
            nome_script,
            resultado.returncode,
            duracao
        )

        raise RuntimeError(
            f"Falha na etapa {nome_script}"
        )

    logging.info(
        "CONCLUIDO: %s | Tempo: %.2fs",
        nome_script,
        duracao
    )


# 5. CONTROLAR O PROCESSO COMPLETO

def main():

    inicio_pipeline = time.perf_counter()

    logging.info("=" * 55)
    logging.info("INICIO DAS VALIDACOES ED-ANTAQ-01")
    logging.info("=" * 55)

    try:

        for numero, etapa in enumerate(
            ETAPAS,
            start=1
        ):

            logging.info(
                "ETAPA %s/%s",
                numero,
                len(ETAPAS)
            )

            executar_etapa(etapa)

        duracao = (
            time.perf_counter()
            - inicio_pipeline
        )

        logging.info(
            "VALIDACOES APROVADAS | Tempo total: %.2fs",
            duracao
        )

    except Exception:

        logging.exception(
            "EXECUCAO INTERROMPIDA"
        )

        raise


if __name__ == "__main__":
    main()
