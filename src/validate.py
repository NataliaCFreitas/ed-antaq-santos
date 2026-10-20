
# ============================================================
# PROJETO ED-ANTAQ-01
# AULA 16 - PARTE 1
# VALIDACAO DA CAMADA SILVER
# ============================================================

from pathlib import Path
import math
import pandas as pd


# 1. CONFIGURAR CAMINHOS

RAIZ = Path(__file__).resolve().parents[1]

ARQUIVO_SILVER = (
    RAIZ / "data" / "silver" /
    "2024Carga_ComplexoSantos.csv"
)

TAMANHO_BLOCO = 50000


# 2. DEFINIR REFERENCIAS DO PILOTO

REGISTROS_ESPERADOS = 760354
PESO_ESPERADO = 177073928.08


# 3. VERIFICAR SE O ARQUIVO EXISTE

if not ARQUIVO_SILVER.is_file():
    raise FileNotFoundError(
        f"Arquivo Silver nao encontrado: {ARQUIVO_SILVER}"
    )


# 4. INICIALIZAR CONTADORES

total_registros = 0
peso_total = 0.0

ids_carga = set()
duplicidades = 0

idcarga_ausente = 0
idatracacao_ausente = 0

pesos_ausentes = 0
pesos_negativos = 0
pesos_zerados = 0

blocos = 0


# 5. LER A SILVER EM BLOCOS

print("=" * 55)
print("ED-ANTAQ-01 - VALIDACAO DA CAMADA SILVER")
print("=" * 55)

leitor = pd.read_csv(
    ARQUIVO_SILVER,
    sep=";",
    encoding="utf-8",
    dtype={
        "IDCarga": "string",
        "IDAtracacao": "string"
    },
    chunksize=TAMANHO_BLOCO,
    low_memory=False
)

for bloco in leitor:

    blocos += 1
    total_registros += len(bloco)

    # Validar presenca das colunas
    colunas_necessarias = [
        "IDCarga",
        "IDAtracacao",
        "PesoBrutoNumerico"
    ]

    for coluna in colunas_necessarias:
        if coluna not in bloco.columns:
            raise ValueError(
                f"Coluna obrigatoria ausente: {coluna}"
            )

    # Validar identificadores
    idcarga_ausente += int(
        bloco["IDCarga"].isna().sum()
    )

    idatracacao_ausente += int(
        bloco["IDAtracacao"].isna().sum()
    )

    # Validar duplicidades em todos os blocos
    for codigo in bloco["IDCarga"].dropna():

        if codigo in ids_carga:
            duplicidades += 1
        else:
            ids_carga.add(codigo)

    # Converter peso para garantir tipo numerico
    pesos = pd.to_numeric(
        bloco["PesoBrutoNumerico"],
        errors="coerce"
    )

    pesos_ausentes += int(pesos.isna().sum())
    pesos_negativos += int((pesos < 0).sum())
    pesos_zerados += int((pesos == 0).sum())

    peso_total += float(pesos.sum())

    print(
        f"Bloco {blocos}: "
        f"{len(bloco)} registros | "
        f"Acumulado: {total_registros}"
    )


# 6. CONFERIR RECONCILIACAO

registros_ok = (
    total_registros == REGISTROS_ESPERADOS
)

peso_ok = math.isclose(
    peso_total,
    PESO_ESPERADO,
    rel_tol=0,
    abs_tol=0.05
)


# 7. APRESENTAR RELATORIO

print("\n" + "=" * 55)
print("RELATORIO DE QUALIDADE")
print("=" * 55)

print("Blocos analisados:", blocos)
print("Registros encontrados:", total_registros)
print("Registros esperados:", REGISTROS_ESPERADOS)

print("\nPeso total:", round(peso_total, 2))
print("Peso esperado:", PESO_ESPERADO)

print("\nIDCarga ausente:", idcarga_ausente)
print("IDAtracacao ausente:", idatracacao_ausente)
print("IDCarga duplicado:", duplicidades)

print("\nPeso ausente:", pesos_ausentes)
print("Peso negativo:", pesos_negativos)
print("Peso zerado:", pesos_zerados)

print("\n" + "-" * 55)

print(
    "Contagem de registros:",
    "OK" if registros_ok else "DIVERGENTE"
)

print(
    "Reconciliacao do peso:",
    "OK" if peso_ok else "DIVERGENTE"
)

if not registros_ok or not peso_ok:
    raise AssertionError(
        "A camada Silver apresentou divergencia "
        "em relacao aos totais esperados."
    )

print("\nValidacao de totais concluida.")
print("Revise os indicadores de qualidade acima.")
