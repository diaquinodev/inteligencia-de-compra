-- O recorte guardado tem, por ano, as mesmas linhas que a tabela pública tem hoje.
-- A origem é republicada inteira sem aviso; se o recorte mudar lá, este teste acusa.
WITH origem AS (
    SELECT
        i.ano,
        COUNT(*) AS linhas
    FROM `basedosdados.br_mgi_compras_publicas.contratacao_item` AS i
    INNER JOIN raw_catalogo AS c ON i.codigo_item_catalogo = c.codigo_item
    WHERE i.ano IN (2024, 2025)
    GROUP BY i.ano
),

recorte AS (
    SELECT
        r.ano,
        COUNT(*) AS linhas
    FROM raw_item AS r
    GROUP BY r.ano
)

SELECT
    COALESCE(origem.ano, recorte.ano) AS ano,
    origem.linhas AS linhas_na_origem,
    recorte.linhas AS linhas_no_recorte
FROM origem
FULL OUTER JOIN recorte ON origem.ano = recorte.ano
WHERE origem.linhas IS NULL OR recorte.linhas IS NULL OR origem.linhas != recorte.linhas;
