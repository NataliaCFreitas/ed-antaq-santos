
# ============================================================
# PROJETO ED-ANTAQ-01
# AULA 21 - PARTE 4
# COMPARACAO ENTRE BANCOS SQLITE
# ============================================================

from pathlib import Path
import sqlite3
import math


# 1. CAMINHOS DOS BANCOS

RAIZ = Path(__file__).resolve().parents[1]

PASTA_BANCO = RAIZ / "data" / "database"

BANCO_PRINCIPAL = (
    PASTA_BANCO / "antaq_santos_pipeline.db"
)

BANCO_TESTE = (
    PASTA_BANCO / "antaq_santos_reprocessamento.db"
)


# 2. FUNCAO DE CONSULTA

def consultar_resumo(caminho):
    """
    Consulta quantidade de registros e
    peso bruto total de um banco SQLite.

    A conexao e aberta somente para leitura.
    """

    if not caminho.is_file():
        raise FileNotFoundError(
            f"Banco nao encontrado: {caminho}"
        )

    conexao = sqlite3.connect(
        caminho.as_uri() + "?mode=ro",
        uri=True
    )

    try:

        resultado = conexao.execute("""
            SELECT
                COUNT(*) AS Registros,
                SUM(PesoBruto) AS PesoTotal
            FROM carga_santos
        """).fetchone()

        return resultado

    finally:
        conexao.close()


# 3. CONSULTAR OS DOIS BANCOS

registros_principal, peso_principal = (
    consultar_resumo(BANCO_PRINCIPAL)
)

registros_teste, peso_teste = (
    consultar_resumo(BANCO_TESTE)
)


# 4. APRESENTAR OS RESULTADOS

print("=" * 55)
print("COMPARACAO DOS BANCOS SQLITE")
print("=" * 55)

print("\nBANCO PRINCIPAL")
print("Registros:", registros_principal)
print("Peso bruto:", round(peso_principal, 2))

print("\nBANCO DE REPROCESSAMENTO")
print("Registros:", registros_teste)
print("Peso bruto:", round(peso_teste, 2))


# 5. VERIFICAR CONSISTENCIA

registros_iguais = (
    registros_principal == registros_teste
)

peso_igual = math.isclose(
    peso_principal,
    peso_teste,
    rel_tol=0,
    abs_tol=0.01
)

print("\n" + "-" * 55)

print(
    "Contagem:",
    "OK" if registros_iguais else "DIVERGENTE"
)

print(
    "Peso bruto:",
    "OK" if peso_igual else "DIVERGENTE"
)

if not registros_iguais or not peso_igual:
    raise AssertionError(
        "Os bancos apresentaram divergencias."
    )

print("\nBANCOS RECONCILIADOS COM SUCESSO.")
