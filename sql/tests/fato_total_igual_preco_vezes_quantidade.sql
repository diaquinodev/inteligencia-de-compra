-- O total do item é o preço unitário vezes a quantidade (tolerância de 1%).
SELECT
    c.id_compra_item,
    c.quantidade,
    c.valor_unitario,
    c.valor_total
FROM fato_item_compra AS c
WHERE ABS(c.valor_total - c.valor_unitario * c.quantidade) > 0.01 * c.valor_total;
