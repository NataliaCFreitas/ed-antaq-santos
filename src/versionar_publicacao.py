
# ============================================================
# ED-ANTAQ-01
# AULA 23 - PARTE 4
# VERSIONAMENTO SEGURO DO BANCO PUBLICADO
# ============================================================

from pathlib import Path
import sqlite3
import math


# 1. CAMINHOS

RAIZ = Path(__file__).resolve().parents[1]

PASTA_BANCO = RAIZ / "data" / "database"

BANCO_PUBLICADO = (
    PASTA_BANCO / "antaq_santos_publicado.db"
)

BANCO_VERSIONADO = (
    PASTA_BANCO / "antaq_santos_2024_v1.db"
)


# 2. VERIFICAR ARQUIVOS

if not BANCO_PUBLICADO.is_file():
    raise FileNotFoundError(
        "Banco publicado nao encontrado."
    )

if BANCO_VERSIONADO.exists():
    raise FileExistsError(
        "A versao v1 ja existe. "
        "Nenhum arquivo foi sobrescrito."
    )


# 3. VALIDAR E COPIAR

print("=" * 55)
print("ED-ANTAQ-01 - PUBLICACAO VERSIONADA")
print("=" * 55)

origem = sqlite3.connect(
    BANCO_PUBLICADO.resolve().as_uri() + "?mode=ro",
    uri=True
)

try:

    integridade = origem.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]

    if integridade != "ok":
        raise AssertionError(
            "Falha de integridade na origem."
        )

    cargas, peso = origem.execute("""
        SELECT COUNT(*), SUM(PesoBruto)
        FROM carga_santos
    """).fetchone()

    if cargas != 760354:
        raise AssertionError(
            "Quantidade de cargas divergente."
        )

    if peso is None or not math.isclose(
        peso,
        177073928.08,
        rel_tol=0,
        abs_tol=0.05
    ):
        raise AssertionError(
            "Peso bruto divergente."
        )

    destino = sqlite3.connect(
        BANCO_VERSIONADO,
        timeout=30
    )

    try:

        origem.backup(destino)

        integridade_destino = destino.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        if integridade_destino != "ok":
            raise AssertionError(
                "Falha de integridade no destino."
            )

        cargas_destino, peso_destino = destino.execute("""
            SELECT COUNT(*), SUM(PesoBruto)
            FROM carga_santos
        """).fetchone()

        if cargas_destino != cargas:
            raise AssertionError(
                "Divergencia de registros."
            )

        if not math.isclose(
            peso_destino,
            peso,
            rel_tol=0,
            abs_tol=0.01
        ):
            raise AssertionError(
                "Divergencia de peso bruto."
            )

    except Exception:

        destino.close()

        if BANCO_VERSIONADO.exists():
            BANCO_VERSIONADO.unlink()

        raise

    else:
        destino.close()

finally:
    origem.close()


# 4. RESUMO

print("\nVERSAO PUBLICADA")
print("Arquivo:", BANCO_VERSIONADO.name)
print("Registros:", cargas_destino)
print("Peso bruto:", round(peso_destino, 2))
print("Integridade: OK")

print("\nBanco publicado original preservado.")
print("VERSIONAMENTO CONCLUIDO COM SUCESSO.")
