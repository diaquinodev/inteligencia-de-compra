-- A chave de negócio de cada dimensão não se repete.
SELECT
    'dim_item' AS dimensao,
    i.codigo_item AS chave,
    COUNT(*) AS repeticoes
FROM dim_item AS i
GROUP BY i.codigo_item
HAVING COUNT(*) > 1
UNION ALL
SELECT
    'dim_fornecedor' AS dimensao,
    f.documento AS chave,
    COUNT(*) AS repeticoes
FROM dim_fornecedor AS f
GROUP BY f.documento
HAVING COUNT(*) > 1
UNION ALL
SELECT
    'dim_orgao' AS dimensao,
    o.cnpj_orgao AS chave,
    COUNT(*) AS repeticoes
FROM dim_orgao AS o
GROUP BY o.cnpj_orgao
HAVING COUNT(*) > 1;
