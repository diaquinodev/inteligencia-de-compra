-- Classifica o documento de cada fornecedor e confere os dígitos verificadores do CNPJ.
-- `documento_publico` é o que segue para o modelo: o CNPJ como está, e o CPF trocado por
-- um código sem volta, porque pessoa física não precisa ser identificada na análise.
-- CNPJ: 12 dígitos de base + 2 verificadores, cada um calculado por módulo 11 com pesos.
CREATE OR REPLACE TABLE stg_fornecedor_documento AS
WITH documentos AS (
    SELECT DISTINCT r.id_fornecedor
    FROM raw_item AS r
    WHERE r.id_fornecedor IS NOT NULL
),

somas AS (
    SELECT
        d.id_fornecedor,
        SUM(
            IF(
                pos < 12,
                SAFE_CAST(digito AS INT64) * [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2][OFFSET(pos)],
                0
            )
        ) AS soma_1,
        SUM(
            IF(
                pos < 13,
                SAFE_CAST(digito AS INT64) * [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2][OFFSET(pos)],
                0
            )
        ) AS soma_2
    FROM documentos AS d, UNNEST(SPLIT(d.id_fornecedor, '')) AS digito WITH OFFSET AS pos
    WHERE REGEXP_CONTAINS(d.id_fornecedor, r'^\d{14}$')
    GROUP BY d.id_fornecedor
)

SELECT
    d.id_fornecedor,
    CASE
        WHEN REGEXP_CONTAINS(d.id_fornecedor, r'^\d{14}$') THEN 'CNPJ'
        WHEN REGEXP_CONTAINS(d.id_fornecedor, r'^\d{11}$') THEN 'CPF'
        ELSE 'OUTRO'
    END AS tipo_documento,
    IF(
        REGEXP_CONTAINS(d.id_fornecedor, r'^\d{11}$'),
        CONCAT('PF-', SUBSTR(TO_HEX(SHA256(d.id_fornecedor)), 1, 12)),
        d.id_fornecedor
    ) AS documento_publico,
    CASE
        WHEN s.id_fornecedor IS NULL THEN NULL
        ELSE
            SUBSTR(d.id_fornecedor, 13, 2) = CONCAT(
                CAST(IF(MOD(s.soma_1, 11) < 2, 0, 11 - MOD(s.soma_1, 11)) AS STRING),
                CAST(IF(MOD(s.soma_2, 11) < 2, 0, 11 - MOD(s.soma_2, 11)) AS STRING)
            )
    END AS cnpj_valido
FROM documentos AS d
LEFT JOIN somas AS s ON d.id_fornecedor = s.id_fornecedor;
