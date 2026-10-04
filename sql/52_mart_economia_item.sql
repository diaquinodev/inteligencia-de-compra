-- Pergunta 3: quanto dá para economizar? Para cada grupo de comparação, quanto se pagou
-- acima da referência. Duas referências:
--   teto: toda compra acima da mediana passa a pagar a mediana;
--   conservadora: só as compras acima do terceiro quartil (p75) caem para o p75.
-- Nos grupos de preço homogêneo (p75 até 2 vezes o p25) a economia conservadora é a mais
-- defensável: a diferença de preço dificilmente vem de produtos diferentes sob o mesmo código.
CREATE OR REPLACE TABLE mart_economia_item AS
WITH por_grupo AS (
    SELECT
        c.sk_item,
        c.unidade_medida,
        ANY_VALUE(c.preco_homogeneo) AS preco_homogeneo,
        COUNT(*) AS compras,
        SUM(c.valor_total) AS gasto,
        COUNTIF(c.valor_unitario > c.preco_p75) AS compras_acima_p75,
        SUM(GREATEST(c.valor_unitario - c.preco_mediano, 0) * c.quantidade) AS economia_teto,
        SUM(GREATEST(c.valor_unitario - c.preco_p75, 0) * c.quantidade) AS economia_conservadora
    FROM fato_item_compra AS c
    WHERE c.comparavel
    GROUP BY c.sk_item, c.unidade_medida
)

SELECT
    i.categoria,
    i.nome_classe,
    i.nome_padrao,
    i.descricao_item,
    g.*,
    SAFE_DIVIDE(g.economia_conservadora, g.gasto) AS economia_conservadora_pct,
    RANK() OVER (ORDER BY g.economia_conservadora DESC) AS posicao_geral,
    RANK() OVER (
        PARTITION BY i.categoria ORDER BY g.economia_conservadora DESC
    ) AS posicao_na_categoria
FROM por_grupo AS g
INNER JOIN dim_item AS i ON g.sk_item = i.sk_item;
