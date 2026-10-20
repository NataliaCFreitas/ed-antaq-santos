
# ============================================================
# PROJETO ED-ANTAQ-01
# MODULO: transform.py
# OBJETIVO: Transformar os dados da ANTAQ
# ============================================================

import pandas as pd


def tratar_peso_carga(df):
    """
    Converte VLPesoCargaBruta para um campo numerico.

    Entrada:
        DataFrame de cargas da ANTAQ.

    Saida:
        Copia do DataFrame com PesoBrutoNumerico.
    """

    dados = df.copy()

    if "VLPesoCargaBruta" not in dados.columns:
        raise ValueError(
            "Coluna VLPesoCargaBruta nao encontrada."
        )

    peso_texto = (
        dados["VLPesoCargaBruta"]
        .astype("string")
        .str.strip()
        .str.replace(",", ".", regex=False)
    )

    dados["PesoBrutoNumerico"] = pd.to_numeric(
        peso_texto,
        errors="coerce"
    )

    return dados

def tratar_datas_atracacao(df):
    """
    Converte a data de atracacao e cria
    Ano, Mes e Competencia.
    """

    dados = df.copy()

    if "Data Atracação" not in dados.columns:
        raise ValueError(
            "Coluna Data Atracação nao encontrada."
        )

    dados["DataAtracacaoConvertida"] = pd.to_datetime(
        dados["Data Atracação"],
        format="%d/%m/%Y %H:%M:%S",
        errors="coerce"
    )

    dados["Ano"] = (
        dados["DataAtracacaoConvertida"]
        .dt.year
        .astype("Int64")
    )

    dados["Mes"] = (
        dados["DataAtracacaoConvertida"]
        .dt.month
        .astype("Int64")
    )

    dados["Competencia"] = (
        dados["DataAtracacaoConvertida"]
        .dt.strftime("%Y-%m")
    )

    return dados

def selecionar_cargas_complexo(
    df_cargas,
    df_atracacoes,
    nome_complexo="Santos"
):
    """
    Seleciona cargas associadas as atracacoes
    de determinado Complexo Portuario.

    Retorna um novo DataFrame de cargas.
    """

    cargas = df_cargas.copy()
    atracacoes = df_atracacoes.copy()

    colunas_obrigatorias_carga = ["IDAtracacao"]
    colunas_obrigatorias_atracacao = [
        "IDAtracacao",
        "Complexo Portuário"
    ]

    for coluna in colunas_obrigatorias_carga:
        if coluna not in cargas.columns:
            raise ValueError(f"Coluna ausente: {coluna}")

    for coluna in colunas_obrigatorias_atracacao:
        if coluna not in atracacoes.columns:
            raise ValueError(f"Coluna ausente: {coluna}")

    cargas["IDAtracacao"] = (
        cargas["IDAtracacao"].astype("string")
    )

    atracacoes["IDAtracacao"] = (
        atracacoes["IDAtracacao"].astype("string")
    )

    # Selecionar os IDs do complexo desejado
    ids_complexo = set(
        atracacoes.loc[
            atracacoes["Complexo Portuário"] == nome_complexo,
            "IDAtracacao"
        ].dropna()
    )

    # Selecionar as cargas correspondentes
    resultado = cargas.loc[
        cargas["IDAtracacao"].isin(ids_complexo)
    ].copy()

    return resultado

def tratar_datas_atracacao(df):
    """
    Converte Data Atracação e cria
    Ano, Mes e Competencia.
    """

    dados = df.copy()

    if "Data Atracação" not in dados.columns:
        raise ValueError(
            "Coluna Data Atracação nao encontrada."
        )

    dados["DataAtracacaoConvertida"] = pd.to_datetime(
        dados["Data Atracação"],
        format="%d/%m/%Y %H:%M:%S",
        errors="coerce"
    )

    dados["Ano"] = (
        dados["DataAtracacaoConvertida"]
        .dt.year
        .astype("Int64")
    )

    dados["Mes"] = (
        dados["DataAtracacaoConvertida"]
        .dt.month
        .astype("Int64")
    )

    dados["Competencia"] = (
        dados["DataAtracacaoConvertida"]
        .dt.strftime("%Y-%m")
    )

    return dados
