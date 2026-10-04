-- Dimensão fornecedor: quem venceu itens válidos, com o cadastro quando ele existe.
-- Pessoa física entra sem CPF e sem nome (ver stg_fornecedor_documento).
CREATE OR REPLACE TABLE dim_fornecedor AS
WITH vencedores AS (
    SELECT
        v.id_fornecedor,
        -- O nome mais frequente nas compras, usado quando não há cadastro.
        APPROX_TOP_COUNT(v.nome_fornecedor, 1)[OFFSET(0)].value AS nome_nas_compras
    FROM stg_item_valido AS v
    GROUP BY v.id_fornecedor
)

SELECT
    ROW_NUMBER() OVER (ORDER BY d.documento_publico) AS sk_fornecedor,
    d.documento_publico AS documento,
    d.tipo_documento,
    IF(
        d.tipo_documento = 'CPF',
        'Pessoa física',
        COALESCE(f.nome_razao_social, v.nome_nas_compras)
    ) AS nome,
    COALESCE(f.sigla_uf, 'Não informado') AS sigla_uf,
    COALESCE(f.porte_empresa, 'Não informado') AS porte,
    f.cnpj IS NOT NULL OR f.cpf IS NOT NULL AS tem_cadastro
FROM vencedores AS v
INNER JOIN stg_fornecedor_documento AS d ON v.id_fornecedor = d.id_fornecedor
LEFT JOIN raw_fornecedor AS f ON v.id_fornecedor = COALESCE(f.cnpj, f.cpf);
