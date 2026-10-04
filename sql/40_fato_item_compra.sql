-- Fato: uma linha por item comprado (item de contratação homologado, com fornecedor e preço).
-- `comparavel` marca as linhas que servem para comparar preço: grupo com 10+ compras
-- e preço não suspeito. `preco_homogeneo` marca os grupos em que o preço varia pouco.
CREATE OR REPLACE TABLE fato_item_compra AS
SELECT
    v.id_compra_item,
    v.id_compra,
    i.sk_item,
    f.sk_fornecedor,
    o.sk_orgao,
    v.data_resultado AS data,
    COALESCE(c.sigla_uf, 'Não informado') AS sigla_uf,
    COALESCE(c.modalidade, 'Não informado') AS modalidade,
    v.unidade_medida,
    v.quantidade,
    v.valor_unitario,
    v.valor_total,
    v.preco_suspeito,
    v.compras_comparaveis,
    v.preco_p25,
    v.preco_mediano,
    v.preco_p75,
    v.preco_homogeneo,
    v.compras_comparaveis >= 10 AND NOT v.preco_suspeito AS comparavel
FROM stg_item_valido AS v
INNER JOIN dim_item AS i ON v.codigo_item = i.codigo_item
INNER JOIN stg_fornecedor_documento AS d ON v.id_fornecedor = d.id_fornecedor
INNER JOIN dim_fornecedor AS f ON d.documento_publico = f.documento
INNER JOIN dim_orgao AS o ON v.cnpj_orgao = o.cnpj_orgao
LEFT JOIN stg_contratacao AS c ON v.id_compra = c.id_compra;
