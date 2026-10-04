"""Valores que o painel deve mostrar, calculados no BigQuery direto da tabela fato.

São as mesmas grandezas das medidas DAX, escritas de novo em SQL. Se o Power BI e o BigQuery
chegam ao mesmo número por caminhos diferentes, a medida está certa.
"""

from typing import Any

from compras.cliente import Banco

_TOTAL = """
SELECT
    SUM(valor_total) AS `Gasto Total`,
    COUNT(*) AS `Itens Comprados`,
    COUNT(DISTINCT sk_fornecedor) AS `Fornecedores`,
    COUNT(DISTINCT sk_orgao) AS `Órgãos`,
    COUNTIF(comparavel) AS `Compras Comparáveis`,
    SUM(IF(comparavel, valor_total, 0)) AS `Gasto Comparável`,
    COUNTIF(preco_suspeito) AS `Itens com Preço Suspeito`,
    SUM(IF(comparavel, GREATEST(valor_unitario - preco_mediano, 0) * quantidade, 0))
        AS `Economia Teto`,
    SUM(IF(comparavel, GREATEST(valor_unitario - preco_p75, 0) * quantidade, 0))
        AS `Economia Conservadora`,
    SUM(
        IF(
            comparavel AND preco_homogeneo,
            GREATEST(valor_unitario - preco_p75, 0) * quantidade,
            0
        )
    ) AS `Economia Defensável`,
    SUM(IF(comparavel AND preco_homogeneo, valor_total, 0)) AS gasto_homogeneo,
    COUNTIF(comparavel AND valor_unitario > preco_p75) AS `Compras Acima do P75`,
    SUM(IF(comparavel AND valor_unitario > preco_p75, valor_total, 0)) AS `Gasto Acima do P75`
FROM fato_item_compra
"""

_POR_CATEGORIA = """
WITH por_fornecedor AS (
    SELECT
        i.categoria,
        c.sk_fornecedor,
        SUM(c.valor_total) AS gasto
    FROM fato_item_compra AS c
    INNER JOIN dim_item AS i ON c.sk_item = i.sk_item
    GROUP BY i.categoria, c.sk_fornecedor
),

concentracao AS (
    SELECT
        categoria,
        SUM(POW(100 * gasto / total, 2)) AS hhi
    FROM (
        SELECT
            categoria,
            gasto,
            SUM(gasto) OVER (PARTITION BY categoria) AS total
        FROM por_fornecedor
    )
    GROUP BY categoria
)

SELECT
    i.categoria,
    SUM(c.valor_total) AS `Gasto Total`,
    SUM(
        IF(
            c.comparavel AND c.preco_homogeneo,
            GREATEST(c.valor_unitario - c.preco_p75, 0) * c.quantidade,
            0
        )
    ) AS `Economia Defensável`,
    ANY_VALUE(k.hhi) AS `HHI`
FROM fato_item_compra AS c
INNER JOIN dim_item AS i ON c.sk_item = i.sk_item
INNER JOIN concentracao AS k ON i.categoria = k.categoria
GROUP BY i.categoria
"""


def calcular(banco: Banco, teto_bytes: int) -> dict[str, Any]:
    total = dict(banco.executar(_TOTAL, teto_bytes)[0])
    gasto_homogeneo = total.pop("gasto_homogeneo")
    total["% Economia Defensável"] = total["Economia Defensável"] / gasto_homogeneo
    total["Ágio Médio sobre o P75"] = total["Economia Conservadora"] / (
        total["Gasto Acima do P75"] - total["Economia Conservadora"]
    )
    categorias = {
        linha["categoria"]: {k: v for k, v in linha.items() if k != "categoria"}
        for linha in banco.executar(_POR_CATEGORIA, teto_bytes)
    }
    return {"total": total, "categoria": categorias}
