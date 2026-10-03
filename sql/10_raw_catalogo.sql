-- Catálogo de materiais do recorte: escritório (75), informática (70) e limpeza (79).
-- O catálogo público tem uma linha por item e por data de extração; fica a mais recente.
CREATE OR REPLACE TABLE raw_catalogo AS
SELECT
    codigo_item,
    codigo_grupo,
    nome_grupo,
    codigo_classe,
    nome_classe,
    codigo_pdm,
    nome_pdm,
    descricao_item,
    indicador_item_ativo,
    data_extracao
FROM `basedosdados.br_mgi_compras_publicas.catalogo_material`
WHERE codigo_grupo IN ('70', '75', '79')
QUALIFY ROW_NUMBER() OVER (PARTITION BY codigo_item ORDER BY data_extracao DESC) = 1;
