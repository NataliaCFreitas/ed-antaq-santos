
# ============================================================
# ED-ANTAQ-01
# AULA 22 - PARTE 7
# CRIAR VIEW 2024 NO STAGING
# ============================================================

from pathlib import Path
import sqlite3
import math
import pandas as pd


# 1. CONFIGURACOES

RAIZ = Path(__file__).resolve().parents[1]

PASTA_BANCO = RAIZ / "data" / "database"

BANCO_STAGING = (
    PASTA_BANCO / "antaq_santos_staging.db"
)

BANCO_PRINCIPAL = (
    PASTA_BANCO / "antaq_santos_pipeline.db"
)

TOTAL_ESPERADO = 757413
PESO_ESPERADO = 175853477.31


# 2. VERIFICAR OS BANCOS

for caminho in [BANCO_STAGING, BANCO_PRINCIPAL]:
    if not caminho.is_file():
        raise FileNotFoundError(
            f"Banco nao encontrado: {caminho}"
        )


# 3. CRIAR A VIEW NO STAGING

print("=" * 55)
print("ED-ANTAQ-01 - VIEW 2024 NO STAGING")
print("=" * 55)

with sqlite3.connect(BANCO_STAGING) as conexao:

    existe = conexao.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'view'
          AND name = 'vw_movimentacao_2024'
    """).fetchone()

    if existe is not None:
        raise RuntimeError(
            "A VIEW ja existe no staging. "
            "Nenhuma alteracao foi realizada."
        )

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

print("\nVIEW criada no staging.")


# 4. CONSULTAR A VIEW

def consultar_view(caminho):

    conexao = sqlite3.connect(
        caminho.resolve().as_uri() + "?mode=ro",
        uri=True
    )

    try:

        consulta = """
        SELECT
            Competencia,
            SUM(QtdRegistrosCarga) AS Registros,
            SUM(PesoBrutoTotal) AS PesoTotal
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


# 5. COMPARAR PRINCIPAL E STAGING

principal = consultar_view(BANCO_PRINCIPAL)
staging = consultar_view(BANCO_STAGING)

comparacao = principal.merge(
    staging,
    on="Competencia",
    how="outer",
    suffixes=("_Principal", "_Staging"),
    indicator=True,
    validate="one_to_one"
)

if len(comparacao) != 12:
    raise AssertionError(
        "Quantidade de meses divergente."
    )

if not (comparacao["_merge"] == "both").all():
    raise AssertionError(
        "Existem meses sem correspondencia."
    )

comparacao["DiferencaRegistros"] = (
    comparacao["Registros_Staging"]
    - comparacao["Registros_Principal"]
)

comparacao["DiferencaPeso"] = (
    comparacao["PesoTotal_Staging"]
    - comparacao["PesoTotal_Principal"]
)

if not (
    comparacao["DiferencaRegistros"] == 0
).all():
    raise AssertionError(
        "Divergencia nos registros mensais."
    )

if not (
    comparacao["DiferencaPeso"].abs() <= 0.01
).all():
    raise AssertionError(
        "Divergencia nos pesos mensais."
    )


# 6. VALIDAR OS TOTAIS

total_registros = int(staging["Registros"].sum())
peso_total = float(staging["PesoTotal"].sum())

if total_registros != TOTAL_ESPERADO:
    raise AssertionError(
        "Total de registros diferente do esperado."
    )

if not math.isclose(
    peso_total,
    PESO_ESPERADO,
    rel_tol=0,
    abs_tol=0.05
):
    raise AssertionError(
        "Peso bruto total diferente do esperado."
    )


# 7. EXIBIR RESULTADOS

print("\nRESUMO DA VIEW 2024")
print("Meses:", len(staging))
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
