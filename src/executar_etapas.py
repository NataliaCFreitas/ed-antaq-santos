
# ============================================================
# PROJETO ED-ANTAQ-01
# AULA 21 - PARTE 1
# INTRODUCAO A ORQUESTRACAO COM SUBPROCESS
# ============================================================

from pathlib import Path
import subprocess
import sys
import time


# 1. LOCALIZAR O PROJETO

RAIZ = Path(__file__).resolve().parents[1]

PASTA_SRC = RAIZ / "src"


# 2. DEFINIR A ORDEM DE EXECUCAO

ETAPAS = [
    "executar_consulta.py",
    "consultar_parametros.py"
]


# 3. EXECUTAR CADA ETAPA

print("=" * 55, flush=True)
print("ED-ANTAQ-01 - ORQUESTRACAO DE CONSULTAS", flush=True)
print("=" * 55, flush=True)

inicio_pipeline = time.perf_counter()

for numero, nome_script in enumerate(ETAPAS, start=1):

    caminho_script = PASTA_SRC / nome_script

    if not caminho_script.is_file():
        raise FileNotFoundError(
            f"Script nao encontrado: {caminho_script}"
        )

    print(
        f"\nETAPA {numero}/{len(ETAPAS)}: {nome_script}",
        flush=True
    )

    inicio_etapa = time.perf_counter()

    resultado = subprocess.run(
        [
            sys.executable,
            str(caminho_script)
        ],
        cwd=RAIZ,
        check=False
    )

    duracao = time.perf_counter() - inicio_etapa

    if resultado.returncode != 0:
        raise RuntimeError(
            f"Falha na etapa {nome_script}. "
            f"Codigo de saida: {resultado.returncode}"
        )

    print(
        f"Etapa concluida em {duracao:.2f} segundos.",
        flush=True
    )


# 4. RESUMO FINAL

duracao_total = time.perf_counter() - inicio_pipeline

print("\n" + "=" * 55)
print("TODAS AS ETAPAS CONCLUIDAS")
print("=" * 55)

print(f"Tempo total: {duracao_total:.2f} segundos")
