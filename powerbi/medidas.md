# Medidas DAX

O arquivo `.pbix` é binário e não aparece em revisão de código. As medidas ficam aqui, em
texto, como fonte da verdade. Crie uma tabela vazia chamada `Medidas` e cole cada uma.

## Base

```dax
Gasto Total = SUM ( fato_item_compra[valor_total] )

Itens Comprados = COUNTROWS ( fato_item_compra )

Fornecedores = DISTINCTCOUNT ( fato_item_compra[sk_fornecedor] )

Órgãos = DISTINCTCOUNT ( fato_item_compra[sk_orgao] )

Ticket Médio por Item = DIVIDE ( [Gasto Total], [Itens Comprados] )
```

## Pergunta 1 — onde está o gasto

```dax
Participação no Gasto =
DIVIDE (
    [Gasto Total],
    CALCULATE ( [Gasto Total], ALLSELECTED ( dim_fornecedor ) )
)

Posição do Fornecedor =
IF (
    HASONEVALUE ( dim_fornecedor[sk_fornecedor] ),
    RANKX ( ALLSELECTED ( dim_fornecedor ), [Gasto Total],, DESC, DENSE )
)

Participação Acumulada =
VAR GastoAtual = [Gasto Total]
RETURN
    DIVIDE (
        SUMX (
            FILTER (
                ALLSELECTED ( dim_fornecedor ),
                [Gasto Total] >= GastoAtual
            ),
            [Gasto Total]
        ),
        CALCULATE ( [Gasto Total], ALLSELECTED ( dim_fornecedor ) )
    )

Classe ABC =
SWITCH (
    TRUE (),
    [Participação Acumulada] - [Participação no Gasto] < 0.80, "A",
    [Participação Acumulada] - [Participação no Gasto] < 0.95, "B",
    "C"
)

HHI =
SUMX (
    VALUES ( dim_fornecedor[sk_fornecedor] ),
    VAR Participacao =
        DIVIDE ( [Gasto Total], CALCULATE ( [Gasto Total], ALLSELECTED ( dim_fornecedor ) ) )
    RETURN
        ( Participacao * 100 ) ^ 2
)
```

## Pergunta 2 — onde se paga caro

```dax
Gasto Comparável =
CALCULATE ( [Gasto Total], fato_item_compra[comparavel] = TRUE () )

Compras Comparáveis =
CALCULATE ( [Itens Comprados], fato_item_compra[comparavel] = TRUE () )

Preço Mediano =
CALCULATE (
    MEDIAN ( fato_item_compra[valor_unitario] ),
    fato_item_compra[comparavel] = TRUE ()
)

Compras Acima do P75 =
CALCULATE (
    [Itens Comprados],
    fato_item_compra[comparavel] = TRUE (),
    FILTER (
        fato_item_compra,
        fato_item_compra[valor_unitario] > fato_item_compra[preco_p75]
    )
)

% Compras Acima do P75 = DIVIDE ( [Compras Acima do P75], [Compras Comparáveis] )

Itens com Preço Suspeito =
CALCULATE ( [Itens Comprados], fato_item_compra[preco_suspeito] = TRUE () )
```

## Pergunta 3 — quanto dá para economizar

```dax
Economia Teto =
SUMX (
    FILTER ( fato_item_compra, fato_item_compra[comparavel] = TRUE () ),
    MAX ( fato_item_compra[valor_unitario] - fato_item_compra[preco_mediano], 0 )
        * fato_item_compra[quantidade]
)

Economia Conservadora =
SUMX (
    FILTER ( fato_item_compra, fato_item_compra[comparavel] = TRUE () ),
    MAX ( fato_item_compra[valor_unitario] - fato_item_compra[preco_p75], 0 )
        * fato_item_compra[quantidade]
)

Economia Defensável =
CALCULATE ( [Economia Conservadora], fato_item_compra[preco_homogeneo] = TRUE () )

Gasto Homogêneo =
CALCULATE ( [Gasto Comparável], fato_item_compra[preco_homogeneo] = TRUE () )

% Economia Defensável = DIVIDE ( [Economia Defensável], [Gasto Homogêneo] )
```

## Tempo

```dax
Gasto Mês Anterior =
CALCULATE ( [Gasto Total], DATEADD ( dim_tempo[data], -1, MONTH ) )

Variação Mensal = DIVIDE ( [Gasto Total] - [Gasto Mês Anterior], [Gasto Mês Anterior] )

Gasto Acumulado no Ano = TOTALYTD ( [Gasto Total], dim_tempo[data] )
```

## Conferência: os números que o painel precisa mostrar

Sem nenhum filtro, as medidas devem bater com as consultas do repositório (03/10/2026):

| Medida | Valor esperado | Consulta de origem |
|---|---|---|
| Gasto Total | R$ 15.805.333.119,66 | `SELECT SUM(valor_total) FROM fato_item_compra` |
| Itens Comprados | 334.901 | `SELECT COUNT(*) FROM fato_item_compra` |
| Fornecedores | 16.012 | `SELECT COUNT(*) FROM dim_fornecedor` |
| Órgãos | 2.470 | `SELECT COUNT(*) FROM dim_orgao` |
| Compras Comparáveis | 267.183 | `qualidade_resumo`, última linha |
| Gasto Comparável | R$ 10.741,2 milhões | `qualidade_resumo`, última linha |
| Itens com Preço Suspeito | 11.702 | `qualidade_resumo` |
| Economia Teto | R$ 2.269,8 milhões | soma de `mart_resumo_categoria.economia_teto` |
| Economia Conservadora | R$ 1.074,9 milhões | soma de `economia_conservadora` |
| Economia Defensável | R$ 263,7 milhões | soma de `economia_homogenea` |

Filtrando por categoria:

| Categoria | Gasto Total (R$ mi) | Economia Defensável (R$ mi) | HHI |
|---|---|---|---|
| Informática | 12.923,0 | 190,8 | 197 |
| Escritório | 2.274,2 | 55,2 | 318 |
| Limpeza | 608,2 | 17,7 | 45 |

Se um número não bater, o erro está no painel (relacionamento, filtro ou medida), não nos
dados: os totais do BigQuery são conferidos pelos testes de `sql/tests/`.
