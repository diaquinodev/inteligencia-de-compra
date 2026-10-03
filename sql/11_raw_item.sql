-- Itens de contratação de 2024 e 2025 cujo código está no catálogo do recorte.
-- Daqui em diante nenhuma consulta lê a tabela pública de itens (4 GB): só este recorte.
CREATE OR REPLACE TABLE raw_item AS
SELECT
    i.ano,
    i.id_compra,
    i.id_compra_item,
    i.cnpj_orgao,
    i.codigo_unidade,
    i.numero_item_compra,
    i.nome_tipo_item,
    i.codigo_item_catalogo,
    i.descricao_resumida,
    i.descricao_detalhada,
    i.unidade_medida,
    i.situacao_item,
    i.criterio_julgamento,
    i.quantidade,
    i.valor_unitario_estimado,
    i.valor_total,
    i.quantidade_resultado,
    i.valor_unitario_resultado,
    i.valor_total_resultado,
    i.id_fornecedor,
    i.nome_fornecedor,
    i.indicador_tem_resultado,
    i.data_resultado,
    i.data_inclusao_pncp
FROM `basedosdados.br_mgi_compras_publicas.contratacao_item` AS i
INNER JOIN raw_catalogo AS c ON i.codigo_item_catalogo = c.codigo_item
WHERE i.ano IN (2024, 2025);
