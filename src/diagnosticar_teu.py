
# ============================================================
# PROJETO ED-ANTAQ-01
# DIAGNOSTICO DE CONVERSAO DA COLUNA TEU
# ============================================================

from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]

ARQUIVO = (
    RAIZ / "data" / "silver"
    / "2024Carga_ComplexoSantos.csv"
)

TAMANHO_BLOCO = 50000

print("=" * 55)
print("DIAGNOSTICO DA COLUNA TEU")
print("=" * 55)

total_problematicos = 0

leitor = pd.read_csv(
    ARQUIVO,
    sep=";",
    encoding="utf-8",
    dtype={
        "IDCarga": "string",
        "IDAtracacao": "string",
        "TEU": "string"
    },
    chunksize=TAMANHO_BLOCO,
    low_memory=False
)

for numero_bloco, bloco in enumerate(leitor, start=1):

    original = bloco["TEU"]

    convertido = pd.to_numeric(
        original,
        errors="coerce"
    )

    mascara_problema = (
        original.notna()
        & convertido.isna()
    )

    quantidade = int(mascara_problema.sum())

    if quantidade > 0:

        total_problematicos += quantidade

        print(f"\nBloco {numero_bloco}")
        print("Valores problematicos:", quantidade)

        colunas = [
            "IDCarga",
            "IDAtracacao",
            "TEU",
            "QTCarga",
            "VLPesoCargaBruta"
        ]

        print(
            bloco.loc[mascara_problema, colunas]
            .to_string(index=False)
        )

print("\n" + "=" * 55)
print("TOTAL DE VALORES NAO CONVERTIDOS:", total_problematicos)
