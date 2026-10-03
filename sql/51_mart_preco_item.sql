-- Pergunta 2: onde se paga caro? Dispersão de preço por grupo de comparação
-- (mesmo item de catálogo, mesma unidade de medida), só com compras comparáveis.
CREATE OR REPLACE TABLE mart_preco_item AS
SELECT
    c.sk_item,
    c.unidade_medida,
    COUNT(*) AS compras,
    COUNT(DISTINCT c.sk_orgao) AS orgaos,
    COUNT(DISTINCT c.sk_fornecedor) AS fornecedores,
    SUM(c.valor_total) AS gasto,
    SUM(c.quantidade) AS quantidade,
    MIN(c.valor_unitario) AS preco_minimo,
    ANY_VALUE(c.preco_p25) AS preco_p25,
    ANY_VALUE(c.preco_mediano) AS preco_mediano,
    ANY_VALUE(c.preco_p75) AS preco_p75,
    MAX(c.valor_unitario) AS preco_maximo,
    -- Quantas vezes o preço do quartil caro é maior que o do quartil barato.
    SAFE_DIVIDE(ANY_VALUE(c.preco_p75), ANY_VALUE(c.preco_p25)) AS dispersao_p75_p25
FROM fato_item_compra AS c
WHERE c.comparavel
GROUP BY c.sk_item, c.unidade_medida;
