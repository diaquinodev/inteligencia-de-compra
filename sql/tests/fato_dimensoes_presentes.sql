-- Toda linha da fato encontra sua linha em cada dimensão.
SELECT
    c.id_compra_item,
    i.sk_item IS NULL AS sem_item,
    f.sk_fornecedor IS NULL AS sem_fornecedor,
    o.sk_orgao IS NULL AS sem_orgao,
    t.data IS NULL AS sem_data
FROM fato_item_compra AS c
LEFT JOIN dim_item AS i ON c.sk_item = i.sk_item
LEFT JOIN dim_fornecedor AS f ON c.sk_fornecedor = f.sk_fornecedor
LEFT JOIN dim_orgao AS o ON c.sk_orgao = o.sk_orgao
LEFT JOIN dim_tempo AS t ON c.data = t.data
WHERE i.sk_item IS NULL OR f.sk_fornecedor IS NULL OR o.sk_orgao IS NULL OR t.data IS NULL;
