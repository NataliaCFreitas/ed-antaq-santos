
-- PROJETO ED-ANTAQ-01
-- CONSULTA PARAMETRIZADA POR COMPETENCIA E NATUREZA

SELECT
    Competencia,
    NaturezaCarga,
    SUM(QtdRegistrosCarga) AS Registros,
    ROUND(SUM(PesoBrutoTotal), 2) AS PesoTotal

FROM vw_movimentacao_2024

WHERE Competencia = :competencia
  AND NaturezaCarga = :natureza

GROUP BY
    Competencia,
    NaturezaCarga;
