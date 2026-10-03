-- Dimensão órgão comprador: todo órgão com item válido, mesmo sem cabeçalho na origem.
-- O mesmo CNPJ aparece com grafias diferentes entre as compras; fica o nome mais frequente.
CREATE OR REPLACE TABLE dim_orgao AS
WITH compradores AS (
    SELECT DISTINCT v.cnpj_orgao
    FROM stg_item_valido AS v
),

cadastro AS (
    SELECT
        c.cnpj_orgao,
        APPROX_TOP_COUNT(c.nome_orgao, 1)[OFFSET(0)].value AS nome_orgao,
        APPROX_TOP_COUNT(c.esfera, 1)[OFFSET(0)].value AS esfera,
        APPROX_TOP_COUNT(c.poder, 1)[OFFSET(0)].value AS poder
    FROM stg_contratacao AS c
    GROUP BY c.cnpj_orgao
)

SELECT
    ROW_NUMBER() OVER (ORDER BY o.cnpj_orgao) AS sk_orgao,
    o.cnpj_orgao,
    COALESCE(c.nome_orgao, 'Não informado') AS nome_orgao,
    COALESCE(c.esfera, 'Não informado') AS esfera,
    COALESCE(c.poder, 'Não informado') AS poder
FROM compradores AS o
LEFT JOIN cadastro AS c ON o.cnpj_orgao = c.cnpj_orgao;
