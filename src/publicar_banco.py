
# ============================================================
# ED-ANTAQ-01
# AULA 22 - PARTE 10
# PUBLICACAO CONTROLADA DO BANCO CANDIDATO
# ============================================================

from pathlib import Path
import sqlite3
import math


RAIZ = Path(__file__).resolve().parents[1]
PASTA = RAIZ / "data" / "database"

CANDIDATO = PASTA / "antaq_santos_candidato.db"
PUBLICADO = PASTA / "antaq_santos_publicado.db"


def validar_banco(conexao):

    integridade = conexao.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]

    if integridade != "ok":
        raise AssertionError(
            "Falha na integridade do SQLite."
        )

    tabelas = {
        linha[0]
        for linha in conexao.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table'
        """)
    }

    obrigatorias = {
        "carga_santos",
        "atracacoes",
        "gold_movimentacao_mensal",
    }

    if not obrigatorias.issubset(tabelas):
        raise AssertionError(
            "Existem tabelas obrigatorias ausentes."
        )

    cargas, peso = conexao.execute("""
        SELECT COUNT(*), SUM(PesoBruto)
        FROM carga_santos
    """).fetchone()

    atracacoes = conexao.execute("""
        SELECT COUNT(*) FROM atracacoes
    """).fetchone()[0]

    gold = conexao.execute("""
        SELECT SUM(QtdRegistrosCarga)
        FROM gold_movimentacao_mensal
    """).fetchone()[0]

    meses, registros_2024 = conexao.execute("""
        SELECT
            COUNT(DISTINCT Competencia),
            SUM(QtdRegistrosCarga)
        FROM vw_movimentacao_2024
    """).fetchone()

    if cargas != 760354:
        raise AssertionError("Cargas divergentes.")

    if atracacoes != 6292:
        raise AssertionError("Atracacoes divergentes.")

    if gold != cargas:
        raise AssertionError("Gold divergente.")

    if meses != 12 or registros_2024 != 757413:
        raise AssertionError("VIEW 2024 divergente.")

    if peso is None or not math.isclose(
        peso,
        177073928.08,
        rel_tol=0,
        abs_tol=0.05
    ):
        raise AssertionError("Peso bruto divergente.")

    return cargas, atracacoes, registros_2024


def main():

    print("=" * 55)
    print("ED-ANTAQ-01 - PUBLICACAO CONTROLADA")
    print("=" * 55)

    if not CANDIDATO.is_file():
        raise FileNotFoundError(
            "Banco candidato nao encontrado."
        )

    if PUBLICADO.exists():
        raise FileExistsError(
            "O banco publicado ja existe. "
            "Publicacao cancelada para evitar sobrescrita."
        )

    # Abrir o candidato somente para leitura
    origem = sqlite3.connect(
        CANDIDATO.resolve().as_uri() + "?mode=ro",
        uri=True
    )

    try:

        print("\n1. Validando banco candidato...")
        resumo_origem = validar_banco(origem)

        # O destino e criado exclusivamente nesta etapa
        destino = sqlite3.connect(
            PUBLICADO,
            timeout=30
        )

        try:

            print("2. Criando copia consistente...")

            origem.backup(destino)

            print("3. Validando banco publicado...")

            resumo_destino = validar_banco(destino)

            if resumo_origem != resumo_destino:
                raise AssertionError(
                    "Divergencia entre origem e destino."
                )

        except Exception:
            destino.close()

            # Apagar somente o novo arquivo criado
            # nesta tentativa de publicacao
            if PUBLICADO.exists():
                PUBLICADO.unlink()

            raise

        else:
            destino.close()

    finally:
        origem.close()

    print("\n" + "=" * 55)
    print("PUBLICACAO CONCLUIDA COM SUCESSO")
    print("=" * 55)

    print("Banco:", PUBLICADO.name)
    print("Cargas:", resumo_destino[0])
    print("Atracacoes:", resumo_destino[1])
    print("Registros VIEW 2024:", resumo_destino[2])
    print("Integridade: OK")
    print("Bancos anteriores: preservados")


if __name__ == "__main__":
    main()
