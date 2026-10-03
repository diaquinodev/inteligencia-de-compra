-- Camada limpa: uma linha por item de contratação, com tipos e textos padronizados.
-- Nenhuma linha é descartada aqui; `motivo_exclusao` diz por que ela não entra na análise.
CREATE OR REPLACE TABLE stg_item AS
WITH sem_duplicatas AS (
    SELECT r.*
    FROM raw_item AS r
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY r.id_compra_item ORDER BY r.data_inclusao_pncp DESC
    ) = 1
),

padronizado AS (
    SELECT
        id_compra_item,
        id_compra,
        ano AS ano_compra,
        cnpj_orgao,
        codigo_item_catalogo AS codigo_item,
        nome_tipo_item,
        situacao_item,
        id_fornecedor,
        unidade_medida AS unidade_medida_original,
        quantidade_resultado AS quantidade,
        valor_unitario_resultado AS valor_unitario,
        valor_total_resultado AS valor_total,
        valor_unitario_estimado,
        TRIM(descricao_resumida) AS descricao_resumida,
        TRIM(nome_fornecedor) AS nome_fornecedor,
        COALESCE(indicador_tem_resultado, FALSE) AS tem_resultado,
        DATE(data_resultado) AS data_resultado,
        -- "Caixa 12,00 UN" e "CAIXA 12 UN" são a mesma embalagem; "UN" é "UNIDADE".
        REGEXP_REPLACE(
            REGEXP_REPLACE(UPPER(TRIM(unidade_medida)), r',0+\b', ''), r'\s+', ' '
        ) AS unidade_sem_decimais
    FROM sem_duplicatas
)

SELECT
    p.* EXCEPT (unidade_sem_decimais),
    CASE
        WHEN p.unidade_sem_decimais IN ('UN', 'UNIDADE 0', 'UNIDADE 1') THEN 'UNIDADE'
        ELSE p.unidade_sem_decimais
    END AS unidade_medida,
    CASE
        WHEN p.nome_tipo_item != 'Material' THEN 'nao_e_material'
        WHEN p.situacao_item != 'Homologado' OR NOT p.tem_resultado THEN 'sem_resultado_homologado'
        WHEN p.id_fornecedor IS NULL THEN 'sem_fornecedor'
        WHEN
            COALESCE(p.valor_unitario, 0) <= 0 OR COALESCE(p.quantidade, 0) <= 0
            THEN 'preco_ou_quantidade_invalidos'
        WHEN p.data_resultado IS NULL THEN 'sem_data_de_resultado'
        WHEN COALESCE(TRIM(p.unidade_medida_original), '') = '' THEN 'sem_unidade_de_medida'
    END AS motivo_exclusao
FROM padronizado AS p;
