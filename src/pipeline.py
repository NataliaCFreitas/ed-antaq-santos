
# ============================================================
# ED-ANTAQ-01
# AULA 22 - PARTE 1
# VERIFICACAO INICIAL DO PIPELINE
# ============================================================

from pathlib import Path
import sqlite3
import math
import time


RAIZ = Path(__file__).resolve().parents[1]
PASTA_BANCO = RAIZ / "data" / "database"

BANCOS = {
    "principal": PASTA_BANCO / "antaq_santos_pipeline.db",
    "teste": PASTA_BANCO / "antaq_santos_reprocessamento.db",
}

TABELAS = [
    "carga_santos",
    "atracacoes",
    "gold_movimentacao_mensal",
]

VIEW = "vw_movimentacao_2024"


def verificar_banco(nome, caminho):
    """Verifica estrutura e indicadores sem alterar o banco."""

    if not caminho.is_file():
        raise FileNotFoundError(
            f"Banco {nome} nao encontrado: {caminho}"
        )

    conexao = sqlite3.connect(
        caminho.as_uri() + "?mode=ro",
        uri=True
    )

    try:
        objetos = {
            (tipo, objeto)
            for tipo, objeto in conexao.execute("""
                SELECT type, name
                FROM sqlite_master
                WHERE type IN ('table', 'view')
            """)
        }

        for tabela in TABELAS:
            if ("table", tabela) not in objetos:
                raise RuntimeError(
                    f"{nome}: tabela ausente: {tabela}"
                )

        if ("view", VIEW) not in objetos:
            raise RuntimeError(
                f"{nome}: VIEW ausente: {VIEW}"
            )

        cargas, peso_cargas = conexao.execute("""
            SELECT COUNT(*), SUM(PesoBruto)
            FROM carga_santos
        """).fetchone()

        atracacoes = conexao.execute("""
            SELECT COUNT(*)
            FROM atracacoes
        """).fetchone()[0]

        registros_2024, peso_2024 = conexao.execute("""
            SELECT
                SUM(QtdRegistrosCarga),
                SUM(PesoBrutoTotal)
            FROM vw_movimentacao_2024
        """).fetchone()

        if cargas != 760354:
            raise AssertionError(
                f"{nome}: quantidade de cargas divergente"
            )

        if atracacoes != 6292:
            raise AssertionError(
                f"{nome}: quantidade de atracacoes divergente"
            )

        if registros_2024 != 757413:
            raise AssertionError(
                f"{nome}: registros de 2024 divergentes"
            )

        if not math.isclose(
            peso_cargas,
            177073928.08,
            rel_tol=0,
            abs_tol=0.05
        ):
            raise AssertionError(
                f"{nome}: peso das cargas divergente"
            )

        if not math.isclose(
            peso_2024,
            175853477.31,
            rel_tol=0,
            abs_tol=0.05
        ):
            raise AssertionError(
                f"{nome}: peso de 2024 divergente"
            )

        print(f"\nBANCO: {nome.upper()}")
        print("Cargas:", cargas)
        print("Atracacoes:", atracacoes)
        print("Registros VIEW 2024:", registros_2024)
        print("Peso VIEW 2024:", round(peso_2024, 2))
        print("Status: OK")

        return {
            "cargas": cargas,
            "atracacoes": atracacoes,
            "registros_2024": registros_2024,
            "peso_cargas": peso_cargas,
            "peso_2024": peso_2024,
        }

    finally:
        conexao.close()


def main():

    inicio = time.perf_counter()

    print("=" * 55)
    print("ED-ANTAQ-01 - VERIFICACAO DO PIPELINE")
    print("=" * 55)

    resultados = {}

    for nome, caminho in BANCOS.items():
        resultados[nome] = verificar_banco(
            nome,
            caminho
        )

    principal = resultados["principal"]
    teste = resultados["teste"]

    for campo in ["cargas", "atracacoes", "registros_2024"]:
        if principal[campo] != teste[campo]:
            raise AssertionError(
                f"Divergencia entre bancos: {campo}"
            )

    for campo in ["peso_cargas", "peso_2024"]:
        if not math.isclose(
            principal[campo],
            teste[campo],
            rel_tol=0,
            abs_tol=0.01
        ):
            raise AssertionError(
                f"Divergencia entre bancos: {campo}"
            )

    duracao = time.perf_counter() - inicio

    print("\n" + "=" * 55)
    print("VERIFICACAO CONCLUIDA COM SUCESSO")
    print(f"Tempo total: {duracao:.2f} segundos")
    print("=" * 55)


if __name__ == "__main__":
    main()
