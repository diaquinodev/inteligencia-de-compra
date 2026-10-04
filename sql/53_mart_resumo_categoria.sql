-- Indicadores por categoria, para o topo do painel e para o README.
-- HHI: soma dos quadrados das participações dos fornecedores (0 a 10.000);
-- acima de 2.500 o mercado é considerado concentrado.
CREATE OR REPLACE TABLE mart_resumo_categoria AS
WITH gasto AS (
    SELECT
        i.categoria,
        COUNT(*) AS itens_comprados,
        COUNT(DISTINCT c.sk_orgao) AS orgaos,
        COUNT(DISTINCT c.sk_fornecedor) AS fornecedores,
        SUM(c.valor_total) AS gasto_total,
        SUM(IF(c.comparavel, c.valor_total, 0)) AS gasto_comparavel,
        COUNTIF(c.preco_suspeito) AS itens_preco_suspeito,
        SUM(IF(c.preco_suspeito, c.valor_total, 0)) AS gasto_preco_suspeito
    FROM fato_item_compra AS c
    INNER JOIN dim_item AS i ON c.sk_item = i.sk_item
    GROUP BY i.categoria
),

concentracao AS (
    SELECT
        m.categoria,
        SUM(POW(m.participacao * 100, 2)) AS hhi,
        SUM(IF(m.posicao <= 10, m.participacao, 0)) AS participacao_top_10,
        COUNTIF(m.classe_abc = 'A') AS fornecedores_classe_a
    FROM mart_gasto_fornecedor AS m
    GROUP BY m.categoria
),

economia AS (
    SELECT
        e.categoria,
        SUM(e.economia_teto) AS economia_teto,
        SUM(e.economia_conservadora) AS economia_conservadora,
        SUM(IF(e.preco_homogeneo, e.gasto, 0)) AS gasto_homogeneo,
        SUM(IF(e.preco_homogeneo, e.economia_conservadora, 0)) AS economia_homogenea
    FROM mart_economia_item AS e
    GROUP BY e.categoria
)

SELECT
    g.*,
    c.hhi,
    c.participacao_top_10,
    c.fornecedores_classe_a,
    e.economia_teto,
    e.economia_conservadora,
    e.gasto_homogeneo,
    e.economia_homogenea,
    SAFE_DIVIDE(e.economia_conservadora, g.gasto_comparavel) AS economia_conservadora_pct
FROM gasto AS g
INNER JOIN concentracao AS c ON g.categoria = c.categoria
INNER JOIN economia AS e ON g.categoria = e.categoria;
