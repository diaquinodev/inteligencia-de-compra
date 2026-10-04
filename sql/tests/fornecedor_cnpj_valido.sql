-- Todo CNPJ de fornecedor tem os dois dígitos verificadores corretos.
SELECT
    d.id_fornecedor,
    d.cnpj_valido
FROM stg_fornecedor_documento AS d
WHERE d.tipo_documento = 'CNPJ' AND NOT d.cnpj_valido;
