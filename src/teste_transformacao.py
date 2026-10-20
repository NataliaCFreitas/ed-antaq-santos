
# ============================================================
# PROJETO ED-ANTAQ-01
# AULA 14 - TESTE DAS TRANSFORMACOES
# ============================================================

from pathlib import Path
import pandas as pd

from extract import ler_amostra

from transform import (
    tratar_peso_carga,
    tratar_datas_atracacao,
    selecionar_cargas_complexo
)


RAIZ_PROJETO = Path(__file__).resolve().parents[1]

CAMINHO_ATRACACOES = (
    RAIZ_PROJETO / "data" / "raw" / "2024Atracacao.txt"
)


# ETAPA 1 - EXTRAIR UMA AMOSTRA DE CARGAS

print("\n1. EXTRAINDO CARGAS")

df_cargas = ler_amostra(
    "2024Carga.txt",
    quantidade_linhas=1000
)

print("Registros extraidos:", len(df_cargas))


# ETAPA 2 - EXTRAIR TODAS AS ATRACACOES

print("\n2. EXTRAINDO ATRACACOES")

df_atracacoes = pd.read_csv(
    CAMINHO_ATRACACOES,
    sep=";",
    encoding="utf-8-sig",
    dtype={"IDAtracacao": "string"},
    low_memory=False
)

print("Atracacoes extraidas:", len(df_atracacoes))


# ETAPA 3 - TRATAR PESO BRUTO

print("\n3. TRATANDO PESO")

df_cargas_tratadas = tratar_peso_carga(df_cargas)

print(
    df_cargas_tratadas[
        ["VLPesoCargaBruta", "PesoBrutoNumerico"]
    ].head(10).to_string(index=False)
)


# ETAPA 4 - TRATAR DATAS

print("\n4. TRATANDO DATAS")

df_atracacoes_tratadas = tratar_datas_atracacao(
    df_atracacoes
)

print(
    df_atracacoes_tratadas[
        ["IDAtracacao", "Competencia"]
    ].head(10).to_string(index=False)
)


# ETAPA 5 - SELECIONAR SANTOS

print("\n5. SELECIONANDO CARGAS DE SANTOS")

df_cargas_santos = selecionar_cargas_complexo(
    df_cargas_tratadas,
    df_atracacoes_tratadas,
    nome_complexo="Santos"
)

print(
    "Cargas de Santos na amostra:",
    len(df_cargas_santos)
)


# ETAPA 6 - CONTROLES DE QUALIDADE

print("\n6. VALIDANDO AS TRANSFORMACOES")

# O tratamento do peso deve preservar as linhas
assert len(df_cargas_tratadas) == len(df_cargas)

# A conversao temporal deve preservar as atracacoes
assert len(df_atracacoes_tratadas) == len(df_atracacoes)

# A selecao nao pode produzir mais cargas
# do que a quantidade original da amostra
assert len(df_cargas_santos) <= len(df_cargas)

# Verificar falhas de conversao de peso
falhas_peso = (
    df_cargas["VLPesoCargaBruta"].notna()
    & df_cargas_tratadas["PesoBrutoNumerico"].isna()
).sum()

print("Falhas de conversao de peso:", falhas_peso)

# Verificar falhas de conversao de data
falhas_data = (
    df_atracacoes["Data Atracação"].notna()
    & df_atracacoes_tratadas[
        "DataAtracacaoConvertida"
    ].isna()
).sum()

print("Falhas de conversao de data:", falhas_data)

assert falhas_peso == 0, "Existem pesos nao convertidos."
assert falhas_data == 0, "Existem datas nao convertidas."

print("\nTESTE CONCLUIDO COM SUCESSO!")
