
# ============================================================
# PROJETO ED-ANTAQ-01
# AULA 21 - PARTE 3
# MODULO: load.py
#
# OBJETIVO:
# Carregar os dados da camada Silver no SQLite,
# utilizando um banco de reprocessamento separado.
# ============================================================

from pathlib import Path
import argparse
import sqlite3
import math

import pandas as pd


# ============================================================
# 1. CONFIGURACOES
# ============================================================

RAIZ = Path(__file__).resolve().parents[1]

ARQUIVO_SILVER = (
    RAIZ
    / "data"
    / "silver"
    / "2024Carga_ComplexoSantos.csv"
)

PASTA_DATABASE = RAIZ / "data" / "database"

BANCOS_PERMITIDOS = {
    "reprocessamento": (
        PASTA_DATABASE
        / "antaq_santos_reprocessamento.db"
    ),
    "staging": (
        PASTA_DATABASE
        / "antaq_santos_staging.db"
    )
}

TAMANHO_BLOCO = 50000

TOTAL_ESPERADO = 760354
PESO_ESPERADO = 177073928.08


# Colunas presentes na Silver
COLUNAS_ORIGEM = [
    "IDCarga",
    "IDAtracacao",
    "CDMercadoria",
    "Tipo Operação da Carga",
    "Natureza da Carga",
    "Sentido",
    "TEU",
    "QTCarga",
    "PesoBrutoNumerico"
]


# Colunas do banco SQLite
COLUNAS_BANCO = [
    "IDCarga",
    "IDAtracacao",
    "CDMercadoria",
    "TipoOperacao",
    "NaturezaCarga",
    "Sentido",
    "TEU",
    "QTCarga",
    "PesoBruto"
]


SQL_INSERT = """
INSERT INTO carga_santos (
    IDCarga,
    IDAtracacao,
    CDMercadoria,
    TipoOperacao,
    NaturezaCarga,
    Sentido,
    TEU,
    QTCarga,
    PesoBruto
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


# ============================================================
# 2. RECEBER O ARGUMENTO DO TERMINAL
# ============================================================

def obter_argumentos():
    """
    Recebe o ambiente de destino informado no terminal.

    Exemplo:
    python src/load.py --banco reprocessamento
    """

    parser = argparse.ArgumentParser(
        description=(
            "Carregamento da Silver ANTAQ no SQLite"
        )
    )

    parser.add_argument(
        "--banco",
        choices=list(BANCOS_PERMITIDOS.keys()),
        required=True,
        help="Banco de destino autorizado"
    )

    return parser.parse_args()


# ============================================================
# 3. CONVERTER VALORES NUMERICOS
# ============================================================

def converter_numero(serie, nome_coluna):
    """
    Converte numeros com virgula decimal.

    Exemplos:
    2,25 -> 2.25
    4,5  -> 4.5
    10   -> 10

    Preserva valores ausentes.
    """

    texto = (
        serie
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
        .str.replace(",", ".", regex=False)
    )

    convertido = pd.to_numeric(
        texto,
        errors="coerce"
    )

    falhas = (
        texto.notna()
        & convertido.isna()
    )

    quantidade_falhas = int(falhas.sum())

    if quantidade_falhas > 0:

        exemplos = (
            texto.loc[falhas]
            .head(5)
            .tolist()
        )

        raise ValueError(
            f"Coluna {nome_coluna}: "
            f"{quantidade_falhas} falhas de conversao. "
            f"Exemplos: {exemplos}"
        )

    valores_validos = convertido.dropna()

    if not valores_validos.map(math.isfinite).all():
        raise ValueError(
            f"Coluna {nome_coluna}: "
            "foram encontrados valores infinitos."
        )

    return convertido


# ============================================================
# 4. PREPARAR OS REGISTROS PARA SQLITE
# ============================================================

def preparar_valores(bloco):
    """
    Prepara os registros para insercao no banco.

    Regras:
    - IDCarga e IDAtracacao sao textos obrigatorios.
    - TEU permite valores decimais.
    - QTCarga deve ser inteiro, quando preenchido.
    - PesoBruto deve ser numerico.
    - Valores ausentes sao enviados como NULL.
    """

    dados = bloco.copy()

    # 4.1. Verificar a estrutura
    for coluna in COLUNAS_ORIGEM:

        if coluna not in dados.columns:
            raise ValueError(
                f"Coluna ausente: {coluna}"
            )

    # 4.2. Padronizar identificadores
    for coluna in [
        "IDCarga",
        "IDAtracacao",
        "CDMercadoria"
    ]:

        dados[coluna] = (
            dados[coluna]
            .astype("string")
            .str.strip()
        )

    # 4.3. Validar as chaves obrigatorias
    for coluna in ["IDCarga", "IDAtracacao"]:

        invalidos = (
            dados[coluna].isna()
            | dados[coluna].eq("")
        ).fillna(True)

        if invalidos.any():
            raise ValueError(
                f"Chave obrigatoria ausente: {coluna}"
            )

    # 4.4. Converter TEU
    dados["TEU"] = converter_numero(
        dados["TEU"],
        "TEU"
    )

    # 4.5. Converter QTCarga
    dados["QTCarga"] = converter_numero(
        dados["QTCarga"],
        "QTCarga"
    )

    # Garantir que QTCarga nao seja fracionaria
    quantidades = dados["QTCarga"].dropna()

    if not (quantidades % 1 == 0).all():
        raise ValueError(
            "QTCarga possui valores fracionarios."
        )

    # 4.6. Converter peso bruto
    dados["PesoBrutoNumerico"] = converter_numero(
        dados["PesoBrutoNumerico"],
        "PesoBrutoNumerico"
    )

    if dados["PesoBrutoNumerico"].isna().any():
        raise ValueError(
            "Existem registros com peso bruto ausente."
        )

    # 4.7. Renomear colunas
    dados = dados.rename(
        columns={
            "Tipo Operação da Carga": "TipoOperacao",
            "Natureza da Carga": "NaturezaCarga",
            "PesoBrutoNumerico": "PesoBruto"
        }
    )

    dados = dados[COLUNAS_BANCO]

    # 4.8. Preparar os tipos aceitos pelo SQLite
    registros = []

    for linha in dados.itertuples(
        index=False,
        name=None
    ):

        valores = list(linha)

        # TEU: float ou NULL
        if pd.notna(valores[6]):
            valores[6] = float(valores[6])
        else:
            valores[6] = None

        # QTCarga: int ou NULL
        if pd.notna(valores[7]):
            valores[7] = int(valores[7])
        else:
            valores[7] = None

        # PesoBruto: float
        valores[8] = float(valores[8])

        # Converter valores ausentes das colunas textuais
        for indice in range(6):

            if pd.isna(valores[indice]):
                valores[indice] = None

        registros.append(tuple(valores))

    return registros


# ============================================================
# 5. VALIDAR A ESTRUTURA DO SQLITE
# ============================================================

def validar_estrutura_banco(conexao):
    """
    Confere a estrutura da tabela carga_santos.
    """

    tabela = conexao.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'carga_santos'
    """).fetchone()

    if tabela is None:
        raise RuntimeError(
            "Tabela carga_santos nao encontrada."
        )

    estrutura = conexao.execute(
        "PRAGMA table_info(carga_santos)"
    ).fetchall()

    tipos = {
        linha[1]: linha[2].upper()
        for linha in estrutura
    }

    for coluna in COLUNAS_BANCO:

        if coluna not in tipos:
            raise RuntimeError(
                f"Coluna ausente no banco: {coluna}"
            )

    if tipos["TEU"] != "REAL":
        raise RuntimeError(
            "A coluna TEU precisa ser REAL."
        )

    if tipos["QTCarga"] != "INTEGER":
        raise RuntimeError(
            "A coluna QTCarga precisa ser INTEGER."
        )

    if tipos["PesoBruto"] != "REAL":
        raise RuntimeError(
            "A coluna PesoBruto precisa ser REAL."
        )

    print("Estrutura da tabela: OK")


# ============================================================
# 6. CARREGAMENTO DA SILVER
# ============================================================

def carregar_silver(caminho_banco):
    """
    Carrega a Silver no SQLite de destino.

    Utiliza transacao unica e valida os totais
    antes de confirmar a gravacao.
    """

    print("=" * 55)
    print("ED-ANTAQ-01 - CARREGAMENTO SILVER -> SQLITE")
    print("=" * 55)

    # 6.1. Verificar arquivos
    if not ARQUIVO_SILVER.is_file():
        raise FileNotFoundError(
            f"Silver nao encontrada: {ARQUIVO_SILVER}"
        )

    if not caminho_banco.is_file():
        raise FileNotFoundError(
            f"Banco nao encontrado: {caminho_banco}"
        )

    print("\nArquivo Silver:", ARQUIVO_SILVER)
    print("Banco de destino:", caminho_banco)

    total_carregado = 0
    blocos_processados = 0

    conexao = sqlite3.connect(
        caminho_banco,
        timeout=30
    )

    try:

        # 6.2. Validar estrutura
        validar_estrutura_banco(conexao)

        # 6.3. Impedir carregamento sobre tabela preenchida
        total_existente = conexao.execute(
            "SELECT COUNT(*) FROM carga_santos"
        ).fetchone()[0]

        if total_existente > 0:
            raise RuntimeError(
                "A tabela ja contem "
                f"{total_existente} registros. "
                "Carga cancelada para evitar duplicacao."
            )

        # 6.4. Preparar leitura em blocos
        leitor = pd.read_csv(
            ARQUIVO_SILVER,
            sep=";",
            encoding="utf-8",
            usecols=COLUNAS_ORIGEM,
            dtype="string",
            chunksize=TAMANHO_BLOCO,
            low_memory=False
        )

        # 6.5. Abrir transacao
        conexao.execute("BEGIN")

        print("\nIniciando carregamento...\n")

        for bloco in leitor:

            blocos_processados += 1

            valores = preparar_valores(bloco)

            conexao.executemany(
                SQL_INSERT,
                valores
            )

            total_carregado += len(valores)

            print(
                f"Bloco {blocos_processados}: "
                f"{len(valores)} registros | "
                f"Acumulado: {total_carregado}",
                flush=True
            )

        # 6.6. Reconciliar os totais
        total_banco, peso_banco = conexao.execute("""
            SELECT
                COUNT(*),
                SUM(PesoBruto)
            FROM carga_santos
        """).fetchone()

        if total_banco != TOTAL_ESPERADO:
            raise ValueError(
                f"Registros divergentes: {total_banco}. "
                f"Esperado: {TOTAL_ESPERADO}"
            )

        if total_carregado != TOTAL_ESPERADO:
            raise ValueError(
                "Total processado diferente do esperado."
            )

        if peso_banco is None or not math.isclose(
            peso_banco,
            PESO_ESPERADO,
            rel_tol=0,
            abs_tol=0.05
        ):
            raise ValueError(
                f"Peso divergente: {peso_banco}. "
                f"Esperado: {PESO_ESPERADO}"
            )

        # 6.7. Confirmar gravacao
        conexao.commit()

        print("\n" + "=" * 55)
        print("RESUMO DO CARREGAMENTO")
        print("=" * 55)

        print("Blocos processados:", blocos_processados)
        print("Registros carregados:", total_banco)
        print("Peso total:", round(peso_banco, 2))
        print("Status: CARGA CONCLUIDA")

    except Exception:

        conexao.rollback()

        print(
            "\nFalha no carregamento. "
            "Transacao revertida ou carga cancelada."
        )

        raise

    finally:

        conexao.close()


# ============================================================
# 7. PONTO DE ENTRADA
# ============================================================

def main():

    argumentos = obter_argumentos()

    caminho_banco = BANCOS_PERMITIDOS[
        argumentos.banco
    ]

    print("\nAmbiente selecionado:", argumentos.banco)

    carregar_silver(caminho_banco)


if __name__ == "__main__":
    main()
