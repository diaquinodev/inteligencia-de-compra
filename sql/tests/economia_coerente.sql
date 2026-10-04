-- A economia nunca é negativa, a conservadora nunca passa do teto e nenhuma passa do gasto.
SELECT
    e.sk_item,
    e.unidade_medida,
    e.gasto,
    e.economia_teto,
    e.economia_conservadora
FROM mart_economia_item AS e
WHERE
    e.economia_conservadora < 0
    OR e.economia_conservadora > e.economia_teto
    OR e.economia_teto > e.gasto;
