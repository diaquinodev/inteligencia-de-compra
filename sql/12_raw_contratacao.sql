-- Cabeçalho das contratações que têm itens no recorte: órgão, local, modalidade e datas.
CREATE OR REPLACE TABLE raw_contratacao AS
SELECT
    c.id_compra,
    c.ano,
    c.sigla_uf,
    c.nome_municipio,
    c.cnpj_orgao,
    c.nome_orgao,
    c.esfera,
    c.poder,
    c.codigo_unidade,
    c.nome_unidade,
    c.modalidade,
    c.modo_disputa,
    c.situacao_compra,
    c.indicador_srp,
    c.indicador_contratacao_excluida,
    c.data_publicacao_pncp
FROM `basedosdados.br_mgi_compras_publicas.contratacao` AS c
WHERE c.id_compra IN (SELECT DISTINCT r.id_compra FROM raw_item AS r);
