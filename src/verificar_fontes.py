
# ============================================================
# PROJETO ED-ANTAQ-01
# AULA 12 - VERIFICACAO DAS FONTES DE DADOS
# ============================================================

from pathlib import Path

# 1. Localizar a raiz do projeto
# __file__ representa o caminho deste script.
# parents[1] corresponde à pasta ed_antaq_piloto.

RAIZ_PROJETO = Path(__file__).resolve().parents[1]

# 2. Definir a pasta onde estão os arquivos originais
PASTA_RAW = RAIZ_PROJETO / "data" / "raw"

# 3. Informar os arquivos esperados
ARQUIVOS_ESPERADOS = [
    "2024Carga.txt",
    "2024Atracacao.txt",
    "2024TemposAtracacao.txt"
]

# 4. Verificar a disponibilidade das fontes
print("=" * 50)
print("PROJETO ED-ANTAQ-01")
print("VERIFICACAO DOS ARQUIVOS DE ORIGEM")
print("=" * 50)

print(f"\nPasta do projeto: {RAIZ_PROJETO}")
print(f"Pasta dos dados: {PASTA_RAW}\n")

arquivos_encontrados = 0

for nome in ARQUIVOS_ESPERADOS:

    caminho = PASTA_RAW / nome

    if caminho.is_file():

        tamanho_mb = caminho.stat().st_size / (1024 ** 2)

        print(f"[OK] {nome}")
        print(f"     Tamanho: {tamanho_mb:.2f} MB")

        arquivos_encontrados += 1

    else:
        print(f"[AUSENTE] {nome}")

# 5. Resultado
print("\n" + "-" * 50)

print(
    f"Arquivos encontrados: "
    f"{arquivos_encontrados}/{len(ARQUIVOS_ESPERADOS)}"
)

if arquivos_encontrados == len(ARQUIVOS_ESPERADOS):
    print("Todas as fontes estão disponíveis.")
else:
    print("Existem arquivos pendentes. Verifique data/raw.")
