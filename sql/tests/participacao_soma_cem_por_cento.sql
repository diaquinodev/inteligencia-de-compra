-- Em cada categoria, as participações dos fornecedores somam 100%.
SELECT
    m.categoria,
    SUM(m.participacao) AS soma
FROM mart_gasto_fornecedor AS m
GROUP BY m.categoria
HAVING ABS(SUM(m.participacao) - 1) > 0.0001;
