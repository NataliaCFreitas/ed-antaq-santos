
# ============================================================
# PROJETO ED-ANTAQ-01
# MODULO: extract.py
# OBJETIVO: Ler arquivos de origem da ANTAQ
# ============================================================

from pathlib import Path
import pandas as pd


# Localizar a pasta principal do projeto
RAIZ_PROJETO = Path(__file__).resolve().parents[1]

# Definir a pasta de arquivos originais
PASTA_RAW = RAIZ_PROJETO / "data" / "raw"


def ler_amostra(nome_arquivo, quantidade_linhas=1000):
    """
    Lê uma amostra de um arquivo TXT delimitado da ANTAQ.

    Parâmetros
    ----------
    nome_arquivo : str
        Nome do arquivo localizado na pasta data/raw.

    quantidade_linhas : int
        Quantidade de registros que serão lidos.

    Retorno
    -------
    pandas.DataFrame
        Tabela contendo os registros extraídos.
    """

    # Construir o caminho completo do arquivo
    caminho = PASTA_RAW / nome_arquivo

    # Verificar se o arquivo existe
    if not caminho.is_file():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho}"
        )

    # Verificar a quantidade solicitada
    if quantidade_linhas <= 0:
        raise ValueError(
            "A quantidade de linhas deve ser positiva."
        )

    # Ler os registros com Pandas
    df = pd.read_csv(
        caminho,
        sep=";",
        encoding="utf-8-sig",
        nrows=quantidade_linhas,
        dtype={
            "IDCarga": "string",
            "IDAtracacao": "string",
            "CDMercadoria": "string"
        },
        low_memory=False
    )

    # Devolver o DataFrame
    return df


# Executar o teste somente quando este arquivo
# for iniciado diretamente pelo terminal.
if __name__ == "__main__":

    print("=" * 50)
    print("ED-ANTAQ-01 - TESTE DE EXTRACAO")
    print("=" * 50)

    dados = ler_amostra(
        nome_arquivo="2024Carga.txt",
        quantidade_linhas=1000
    )

    print("\nRegistros:", len(dados))
    print("Colunas:", len(dados.columns))

    print("\nPrimeiros registros:")
    print(dados.head().to_string(index=False))

    # Testar a mesma função em outro arquivo
    atracacoes = ler_amostra(
        nome_arquivo="2024Atracacao.txt",
        quantidade_linhas=500
    )

    print("\nTESTE DA BASE DE ATRACACOES")
    print("Registros:", len(atracacoes))
    print("Colunas:", len(atracacoes.columns))
