-- Nos itens comparáveis, p25 <= mediana <= p75 e o grupo tem pelo menos 10 compras.
SELECT
    c.id_compra_item,
    c.preco_p25,
    c.preco_mediano,
    c.preco_p75,
    c.compras_comparaveis
FROM fato_item_compra AS c
WHERE
    c.comparavel
    AND (
        c.preco_p25 > c.preco_mediano
        OR c.preco_mediano > c.preco_p75
        OR c.compras_comparaveis < 10
        OR c.preco_suspeito
    );
