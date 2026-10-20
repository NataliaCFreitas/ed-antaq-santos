
-- ===================================================
-- PROJETO ED-ANTAQ-01
-- CONSULTA: RESUMO MENSAL DE 2024
-- FONTE: vw_movimentacao_2024
-- ===================================================

SELECT
    Competencia,

    SUM(QtdRegistrosCarga) AS Registros,

    ROUND(
        SUM(PesoBrutoTotal),
        2
    ) AS PesoTotal

FROM vw_movimentacao_2024

GROUP BY Competencia

ORDER BY Competencia;
