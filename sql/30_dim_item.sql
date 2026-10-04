-- Dimensão item: o catálogo de materiais do recorte, com a hierarquia grupo > classe > item.
CREATE OR REPLACE TABLE dim_item AS
SELECT
    ROW_NUMBER() OVER (ORDER BY c.codigo_item) AS sk_item,
    c.codigo_item,
    c.descricao_item,
    c.nome_pdm AS nome_padrao,
    c.codigo_classe,
    c.nome_classe,
    c.codigo_grupo,
    CASE c.codigo_grupo
        WHEN '70' THEN 'Informática'
        WHEN '75' THEN 'Escritório'
        WHEN '79' THEN 'Limpeza'
    END AS categoria
FROM raw_catalogo AS c;
