
# ============================================================
# PROJETO ED-ANTAQ-01
# AULA 15 - PARTE 2
# PROCESSAMENTO COMPLETO DA CAMADA SILVER
# ============================================================

from pathlib import Path
import os
import pandas as pd

from transform import tratar_peso_carga


# 1. DEFINIR CAMINHOS

RAIZ = Path(__file__).resolve().parents[1]

PASTA_RAW = RAIZ / "data" / "raw"
PASTA_SILVER = RAIZ / "data" / "silver"

ARQUIVO_CARGAS = PASTA_RAW / "2024Carga.txt"
ARQUIVO_ATRACACOES = PASTA_RAW / "2024Atracacao.txt"

PASTA_SILVER.mkdir(parents=True, exist_ok=True)

ARQUIVO_SILVER = (
    PASTA_SILVER / "2024Carga_ComplexoSantos.csv"
)

ARQUIVO_TEMPORARIO = (
    PASTA_SILVER / "2024Carga_ComplexoSantos.csv.tmp"
)

TAMANHO_BLOCO = 50000


# 2. VALIDAR ARQUIVOS DE ORIGEM

for caminho in [ARQUIVO_CARGAS, ARQUIVO_ATRACACOES]:
    if not caminho.is_file():
        raise FileNotFoundError(
            f"Arquivo nao encontrado: {caminho}"
        )


# 3. CARREGAR AS ATRACACOES

print("1. Carregando atracacoes...")

df_atracacoes = pd.read_csv(
    ARQUIVO_ATRACACOES,
    sep=";",
    encoding="utf-8-sig",
    dtype={"IDAtracacao": "string"},
    low_memory=False
)

assert df_atracacoes["IDAtracacao"].notna().all()
assert df_atracacoes["IDAtracacao"].is_unique

ids_santos = set(
    df_atracacoes.loc[
        df_atracacoes["Complexo Portuário"] == "Santos",
        "IDAtracacao"
    ]
)

print("Atracacoes nacionais:", len(df_atracacoes))
print("Atracacoes do Complexo Santos:", len(ids_santos))


# 4. PREPARAR INDICADORES

total_lido = 0
total_santos = 0
total_falhas_peso = 0
peso_total_santos = 0.0
blocos_processados = 0

# O arquivo temporario evita considerar um CSV
# incompleto como resultado final.
if ARQUIVO_TEMPORARIO.exists():
    raise FileExistsError(
        "Ja existe um arquivo temporario. "
        "Verifique antes de executar novamente: "
        f"{ARQUIVO_TEMPORARIO}"
    )


# 5. PROCESSAR O ARQUIVO NACIONAL

print("\n2. Iniciando processamento completo...")

try:

    leitor = pd.read_csv(
        ARQUIVO_CARGAS,
        sep=";",
        encoding="utf-8-sig",
        dtype={
            "IDCarga": "string",
            "IDAtracacao": "string",
            "CDMercadoria": "string"
        },
        chunksize=TAMANHO_BLOCO,
        low_memory=False
    )

    primeiro_bloco_gravado = False

    for numero_bloco, bloco in enumerate(leitor, start=1):

        # Converter peso bruto
        bloco_tratado = tratar_peso_carga(bloco)

        # Verificar falhas de conversao
        falhas = (
            bloco["VLPesoCargaBruta"].notna()
            & bloco_tratado["PesoBrutoNumerico"].isna()
        ).sum()

        total_falhas_peso += int(falhas)

        if falhas > 0:
            raise ValueError(
                f"Bloco {numero_bloco}: "
                f"{falhas} valores de peso nao convertidos."
            )

        # Selecionar cargas de Santos
        bloco_santos = bloco_tratado.loc[
            bloco_tratado["IDAtracacao"].isin(ids_santos)
        ].copy()

        # Atualizar indicadores
        total_lido += len(bloco)
        total_santos += len(bloco_santos)
        blocos_processados += 1

        peso_total_santos += (
            bloco_santos["PesoBrutoNumerico"].sum()
        )

        # Gravar apenas as cargas selecionadas
        bloco_santos.to_csv(
            ARQUIVO_TEMPORARIO,
            sep=";",
            index=False,
            mode="a",
            header=not primeiro_bloco_gravado,
            encoding="utf-8"
        )

        primeiro_bloco_gravado = True

        print(
            f"Bloco {numero_bloco}: "
            f"{len(bloco)} lidos | "
            f"{len(bloco_santos)} Santos | "
            f"Acumulado: {total_santos}"
        )

    # Publicar resultado somente apos sucesso total
    os.replace(ARQUIVO_TEMPORARIO, ARQUIVO_SILVER)

except Exception:
    print(
        "\nProcessamento interrompido. "
        "Verifique o erro e o arquivo temporario."
    )
    raise


# 6. RESUMO FINAL

print("\n" + "=" * 55)
print("RESUMO DA CAMADA SILVER")
print("=" * 55)

print("Blocos processados:", blocos_processados)
print("Registros nacionais lidos:", total_lido)
print("Registros de Santos:", total_santos)
print("Falhas de conversao:", total_falhas_peso)
print("Peso bruto total:", round(peso_total_santos, 2))

print("\nArquivo gerado:")
print(ARQUIVO_SILVER)

print("\nPROCESSAMENTO CONCLUIDO.")
