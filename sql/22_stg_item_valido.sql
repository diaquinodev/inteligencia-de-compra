-- Itens que entram na análise, com a referência de preço do seu grupo de comparação.
-- Grupo de comparação: mesmo item de catálogo na mesma unidade de medida.
-- Preço suspeito: mais de 10 vezes acima ou abaixo da mediana do grupo (com 10+ compras).
-- Costuma ser o valor do lote lançado no campo de valor unitário, não um preço real.
CREATE OR REPLACE TABLE stg_item_valido AS
WITH validos AS (
    SELECT s.* EXCEPT (motivo_exclusao)
    FROM stg_item AS s
    WHERE s.motivo_exclusao IS NULL
),

com_referencia AS (
    SELECT
        v.*,
        COUNT(*) OVER grupo AS compras_no_grupo,
        PERCENTILE_CONT(v.valor_unitario, 0.5) OVER grupo AS mediana_bruta
    FROM validos AS v
    WINDOW grupo AS (PARTITION BY v.codigo_item, v.unidade_medida)
),

marcado AS (
    SELECT
        c.*,
        c.compras_no_grupo >= 10
        AND (c.valor_unitario > 10 * c.mediana_bruta OR c.valor_unitario < c.mediana_bruta / 10)
            AS preco_suspeito
    FROM com_referencia AS c
),

-- A referência final é recalculada sem os preços suspeitos, para eles não a distorcerem.
com_quartis AS (
    SELECT
        m.* EXCEPT (compras_no_grupo, mediana_bruta),
        COUNTIF(NOT m.preco_suspeito) OVER grupo AS compras_comparaveis,
        PERCENTILE_CONT(IF(m.preco_suspeito, NULL, m.valor_unitario), 0.25) OVER grupo
            AS preco_p25,
        PERCENTILE_CONT(IF(m.preco_suspeito, NULL, m.valor_unitario), 0.5) OVER grupo
            AS preco_mediano,
        PERCENTILE_CONT(IF(m.preco_suspeito, NULL, m.valor_unitario), 0.75) OVER grupo
            AS preco_p75
    FROM marcado AS m
    WINDOW grupo AS (PARTITION BY m.codigo_item, m.unidade_medida)
)

-- Preço homogêneo: o quartil caro custa no máximo 2 vezes o quartil barato. Nesses grupos a
-- diferença de preço dificilmente vem de produtos diferentes sob o mesmo código de catálogo.
SELECT
    q.*,
    COALESCE(SAFE_DIVIDE(q.preco_p75, q.preco_p25) <= 2, FALSE) AS preco_homogeneo
FROM com_quartis AS q;
