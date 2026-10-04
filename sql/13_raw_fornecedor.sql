-- Cadastro dos fornecedores que venceram itens do recorte (extração mais recente).
CREATE OR REPLACE TABLE raw_fornecedor AS
SELECT
    f.cnpj,
    f.cpf,
    f.nome_razao_social,
    f.sigla_uf,
    f.nome_municipio,
    f.porte_empresa,
    f.natureza_juridica,
    f.nome_cnae,
    f.data_extracao
FROM `basedosdados.br_mgi_compras_publicas.fornecedor` AS f
WHERE COALESCE(f.cnpj, f.cpf) IN (SELECT DISTINCT r.id_fornecedor FROM raw_item AS r)
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY COALESCE(f.cnpj, f.cpf) ORDER BY f.data_extracao DESC
) = 1;
