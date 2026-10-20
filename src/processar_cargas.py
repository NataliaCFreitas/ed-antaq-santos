
# ============================================================
# PROJETO ED-ANTAQ-01
# AULA 15 - PROCESSAMENTO EM LOTES
# TESTE COM OS DOIS PRIMEIROS BLOCOS
# ============================================================

from pathlib import Path
import pandas as pd

from transform import (
    tratar_peso_carga,
    selecionar_cargas_complexo
)

# 1. Localizar as pastas do projeto
RAIZ = Path(__file__).resolve().parents[1]
PASTA_RAW = RAIZ / "data" / "raw"

ARQUIVO_CARGAS = PASTA_RAW / "2024Carga.txt"
ARQUIVO_ATRACACOES = PASTA_RAW / "2024Atracacao.txt"

# 2. Ler toda a tabela de atracacoes
print("Carregando atracacoes...")

df_atracacoes = pd.read_csv(
    ARQUIVO_ATRACACOES,
    sep=";",
    encoding="utf-8-sig",
    dtype={"IDAtracacao": "string"},
    low_memory=False
)

print("Atracacoes carregadas:", len(df_atracacoes))

# 3. Preparar a leitura das cargas em blocos
leitor = pd.read_csv(
    ARQUIVO_CARGAS,
    sep=";",
    encoding="utf-8-sig",
    dtype={
        "IDCarga": "string",
        "IDAtracacao": "string",
        "CDMercadoria": "string"
    },
    chunksize=50000,
    low_memory=False
)

total_lido = 0
total_santos = 0
blocos_processados = 0

# 4. Processar somente dois blocos
for numero_bloco, bloco in enumerate(leitor, start=1):

    if numero_bloco > 2:
        break

    # Transformar peso
    bloco_tratado = tratar_peso_carga(bloco)

    # Identificar falhas de conversao
    falhas = (
        bloco["VLPesoCargaBruta"].notna()
        & bloco_tratado["PesoBrutoNumerico"].isna()
    ).sum()

    if falhas > 0:
        raise ValueError(
            f"Bloco {numero_bloco}: "
            f"{falhas} pesos nao convertidos."
        )

    # Filtrar cargas de Santos
    bloco_santos = selecionar_cargas_complexo(
        bloco_tratado,
        df_atracacoes,
        nome_complexo="Santos"
    )

    # Atualizar indicadores
    total_lido += len(bloco)
    total_santos += len(bloco_santos)
    blocos_processados += 1

    print(
        f"Bloco {numero_bloco}: "
        f"{len(bloco)} linhas lidas | "
        f"{len(bloco_santos)} cargas de Santos"
    )

# 5. Resumo do teste
print("\n" + "=" * 50)
print("RESUMO DO PROCESSAMENTO")
print("=" * 50)

print("Blocos processados:", blocos_processados)
print("Total de cargas lidas:", total_lido)
print("Total de cargas de Santos:", total_santos)
