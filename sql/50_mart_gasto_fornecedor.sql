-- Pergunta 1: onde está o gasto? Fornecedores por categoria, com participação e curva ABC.
-- Classe A: fornecedores que somam os primeiros 80% do gasto; B: até 95%; C: o restante.
CREATE OR REPLACE TABLE mart_gasto_fornecedor AS
WITH por_fornecedor AS (
    SELECT
        i.categoria,
        f.sk_fornecedor,
        SUM(c.valor_total) AS gasto,
        COUNT(*) AS itens_comprados,
        COUNT(DISTINCT c.sk_orgao) AS orgaos_atendidos
    FROM fato_item_compra AS c
    INNER JOIN dim_item AS i ON c.sk_item = i.sk_item
    INNER JOIN dim_fornecedor AS f ON c.sk_fornecedor = f.sk_fornecedor
    GROUP BY i.categoria, f.sk_fornecedor
),

com_participacao AS (
    SELECT
        p.*,
        RANK() OVER (PARTITION BY p.categoria ORDER BY p.gasto DESC) AS posicao,
        p.gasto / SUM(p.gasto) OVER (PARTITION BY p.categoria) AS participacao,
        SUM(p.gasto) OVER (
            PARTITION BY p.categoria ORDER BY p.gasto DESC, p.sk_fornecedor ASC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) / SUM(p.gasto) OVER (PARTITION BY p.categoria) AS participacao_acumulada
    FROM por_fornecedor AS p
)

SELECT
    c.*,
    CASE
        WHEN c.participacao_acumulada - c.participacao < 0.80 THEN 'A'
        WHEN c.participacao_acumulada - c.participacao < 0.95 THEN 'B'
        ELSE 'C'
    END AS classe_abc
FROM com_participacao AS c;
