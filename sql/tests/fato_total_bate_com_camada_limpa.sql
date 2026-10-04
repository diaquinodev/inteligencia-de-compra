-- Nenhuma linha se perde nem se duplica entre a camada limpa e a fato.
WITH limpa AS (
    SELECT
        COUNT(*) AS linhas,
        ROUND(SUM(v.valor_total), 2) AS total
    FROM stg_item_valido AS v
),

fato AS (
    SELECT
        COUNT(*) AS linhas,
        ROUND(SUM(c.valor_total), 2) AS total
    FROM fato_item_compra AS c
)

SELECT
    limpa.linhas AS linhas_limpa,
    fato.linhas AS linhas_fato,
    limpa.total AS total_limpa,
    fato.total AS total_fato
FROM limpa
CROSS JOIN fato
WHERE limpa.linhas != fato.linhas OR limpa.total != fato.total;
