-- Quantidade, preço e total são sempre maiores que zero.
SELECT
    c.id_compra_item,
    c.quantidade,
    c.valor_unitario,
    c.valor_total
FROM fato_item_compra AS c
WHERE
    COALESCE(c.quantidade, 0) <= 0
    OR COALESCE(c.valor_unitario, 0) <= 0
    OR COALESCE(c.valor_total, 0) <= 0;
