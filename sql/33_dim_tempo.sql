-- Dimensão tempo: um dia por linha, do primeiro ao último resultado do recorte.
CREATE OR REPLACE TABLE dim_tempo AS
SELECT
    dia AS data,
    EXTRACT(YEAR FROM dia) AS ano,
    EXTRACT(QUARTER FROM dia) AS trimestre,
    EXTRACT(MONTH FROM dia) AS mes,
    FORMAT_DATE('%Y-%m', dia) AS ano_mes,
    DATE_TRUNC(dia, MONTH) AS inicio_do_mes
FROM
    UNNEST(
        GENERATE_DATE_ARRAY(
            (SELECT MIN(v.data_resultado) FROM stg_item_valido AS v),
            (SELECT MAX(v.data_resultado) FROM stg_item_valido AS v)
        )
    ) AS dia;
