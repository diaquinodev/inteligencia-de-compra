-- Cada item de contratação aparece uma única vez na fato.
SELECT
    c.id_compra_item,
    COUNT(*) AS repeticoes
FROM fato_item_compra AS c
GROUP BY c.id_compra_item
HAVING COUNT(*) > 1;
