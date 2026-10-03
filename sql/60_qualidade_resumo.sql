-- Relatório de qualidade: o que cada regra de limpeza tirou da análise, em linhas e em valor.
CREATE OR REPLACE TABLE qualidade_resumo AS
SELECT
    1 AS ordem,
    'Linhas do recorte na origem' AS etapa,
    COUNT(*) AS linhas,
    SUM(r.valor_total_resultado) AS valor
FROM raw_item AS r
UNION ALL
SELECT
    2 AS ordem,
    'Removidas: item repetido na origem' AS etapa,
    (SELECT COUNT(*) FROM raw_item) - (SELECT COUNT(*) FROM stg_item) AS linhas,
    NULL AS valor
UNION ALL
SELECT
    3 AS ordem,
    CONCAT('Fora da análise: ', s.motivo_exclusao) AS etapa,
    COUNT(*) AS linhas,
    SUM(s.valor_total) AS valor
FROM stg_item AS s
WHERE s.motivo_exclusao IS NOT NULL
GROUP BY s.motivo_exclusao
UNION ALL
SELECT
    4 AS ordem,
    'Válidas (entram na fato)' AS etapa,
    COUNT(*) AS linhas,
    SUM(v.valor_total) AS valor
FROM stg_item_valido AS v
UNION ALL
SELECT
    5 AS ordem,
    'Válidas com preço suspeito (fora da comparação de preços)' AS etapa,
    COUNTIF(v.preco_suspeito) AS linhas,
    SUM(IF(v.preco_suspeito, v.valor_total, 0)) AS valor
FROM stg_item_valido AS v
UNION ALL
SELECT
    6 AS ordem,
    'Válidas em grupo com menos de 10 compras (fora da comparação de preços)' AS etapa,
    COUNTIF(v.compras_comparaveis < 10 AND NOT v.preco_suspeito) AS linhas,
    SUM(IF(v.compras_comparaveis < 10 AND NOT v.preco_suspeito, v.valor_total, 0)) AS valor
FROM stg_item_valido AS v
UNION ALL
SELECT
    7 AS ordem,
    'Comparáveis (base das perguntas 2 e 3)' AS etapa,
    COUNTIF(v.compras_comparaveis >= 10 AND NOT v.preco_suspeito) AS linhas,
    SUM(IF(v.compras_comparaveis >= 10 AND NOT v.preco_suspeito, v.valor_total, 0)) AS valor
FROM stg_item_valido AS v;
