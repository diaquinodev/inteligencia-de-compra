-- Cabeçalho limpo: uma linha por contratação.
-- A origem repete a contratação a cada republicação; fica a publicação mais recente.
CREATE OR REPLACE TABLE stg_contratacao AS
SELECT
    c.id_compra,
    c.cnpj_orgao,
    c.sigla_uf,
    c.modalidade,
    TRIM(c.nome_orgao) AS nome_orgao,
    c.esfera,
    c.poder
FROM raw_contratacao AS c
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY c.id_compra ORDER BY c.data_publicacao_pncp DESC
) = 1;
