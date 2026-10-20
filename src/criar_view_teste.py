
# ============================================================
# PROJETO ED-ANTAQ-01
# AULA 21 - PARTE 7
# CRIAR E VALIDAR A VIEW 2024 NO BANCO DE TESTE
# ============================================================

from pathlib import Path
import sqlite3
import math
import pandas as pd


# 1. CONFIGURAR OS CAMINHOS

RAIZ = Path(__file__).resolve().parents[1]
PASTA_BANCO = RAIZ / "data" / "database"

BANCO_PRINCIPAL = (
    PASTA_BANCO / "antaq_santos_pipeline.db"
)

BANCO_TESTE = (
    PASTA_BANCO / "antaq_santos_reprocessamento.db"
)

for banco in [BANCO_PRINCIPAL, BANCO_TESTE]:
    if not banco.is_file():
        raise FileNotFoundError(
            f"Banco nao encontrado: {banco}"
        )


# 2. CRIAR A VIEW SOMENTE NO BANCO DE TESTE

print("=" * 55)
print("ED-ANTAQ-01 - VIEW DE REPROCESSAMENTO")
print("=" * 55)

with sqlite3.connect(BANCO_TESTE) as conexao:

    with conexao:

        conexao.execute("""
            DROP VIEW IF EXISTS vw_movimentacao_2024
        """)

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

print("VIEW criada no banco de teste.")


# 3. FUNCAO PARA CONSULTAR A VIEW

def consultar_view(caminho_banco):

    conexao = sqlite3.connect(
        caminho_banco.as_uri() + "?mode=ro",
        uri=True
    )

    try:

        consulta = """
        SELECT
            Competencia,
            SUM(QtdRegistrosCarga) AS Registros,
            ROUND(SUM(PesoBrutoTotal), 2) AS PesoTotal
        FROM vw_movimentacao_2024
        GROUP BY Competencia
        ORDER BY Competencia
        """

        return pd.read_sql_query(
            consulta,
            conexao
        )

    finally:
        conexao.close()


# 4. CONSULTAR PRINCIPAL E TESTE

principal = consultar_view(BANCO_PRINCIPAL)
teste = consultar_view(BANCO_TESTE)


# 5. COMPARAR OS RESULTADOS

comparacao = principal.merge(
    teste,
    on="Competencia",
    how="outer",
    suffixes=("_Principal", "_Teste"),
    indicator=True,
    validate="one_to_one"
)

assert len(comparacao) == 12, (
    "A comparacao nao apresentou 12 meses."
)

assert (comparacao["_merge"] == "both").all(), (
    "Existem meses ausentes em um dos bancos."
)

comparacao["DiferencaRegistros"] = (
    comparacao["Registros_Teste"]
    - comparacao["Registros_Principal"]
)

comparacao["DiferencaPeso"] = (
    comparacao["PesoTotal_Teste"]
    - comparacao["PesoTotal_Principal"]
)

assert (
    comparacao["DiferencaRegistros"] == 0
).all(), "Divergencia na quantidade mensal."

assert (
    comparacao["DiferencaPeso"].abs() <= 0.01
).all(), "Divergencia no peso mensal."


# 6. VALIDAR O RESUMO DE 2024

total_registros = int(
    teste["Registros"].sum()
)

peso_total = float(
    teste["PesoTotal"].sum()
)

assert total_registros == 757413

assert math.isclose(
    peso_total,
    175853477.31,
    rel_tol=0,
    abs_tol=0.05
)


# 7. EXIBIR RESULTADOS

print("\nRESUMO DA VIEW 2024")
print("Meses:", len(teste))
print("Registros:", total_registros)
print("Peso bruto:", round(peso_total, 2))

print("\nCOMPARACAO MENSAL")

print(
    comparacao[
        [
            "Competencia",
            "DiferencaRegistros",
            "DiferencaPeso"
        ]
    ].to_string(index=False)
)

print("\nVIEW 2024 VALIDADA COM SUCESSO.")
