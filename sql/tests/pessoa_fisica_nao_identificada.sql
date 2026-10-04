-- Nenhum CPF nem nome de pessoa física chega à dimensão de fornecedores.
SELECT
    f.sk_fornecedor,
    f.documento,
    f.nome
FROM dim_fornecedor AS f
WHERE
    f.tipo_documento = 'CPF'
    AND (NOT STARTS_WITH(f.documento, 'PF-') OR f.nome != 'Pessoa física');
