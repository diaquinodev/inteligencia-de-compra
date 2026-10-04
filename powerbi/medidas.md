# Medidas DAX

O arquivo `.pbix` é binário e não aparece em revisão de código. As medidas ficam em texto em
[medidas.dax](medidas.dax), que é a fonte da verdade: 24 medidas e duas consultas de
conferência, prontas para colar na exibição de consulta DAX do Power BI Desktop.

## Grupos de medidas

| Grupo | Medidas |
|---|---|
| Base | Gasto Total, Itens Comprados, Fornecedores, Órgãos, Ticket Médio por Item |
| Onde está o gasto | Participação no Gasto, Posição do Fornecedor, Participação Acumulada, Classe ABC, HHI |
| Onde se paga caro | Gasto Comparável, Compras Comparáveis, Preço Mediano, Compras Acima do P75, % Compras Acima do P75, Itens com Preço Suspeito |
| Quanto dá para economizar | Economia Teto, Economia Conservadora, Economia Defensável, Gasto Homogêneo, % Economia Defensável |
| Tempo | Gasto Mês Anterior, Variação Mensal, Gasto Acumulado no Ano |

## Duas decisões que valem explicação

- **`REMOVEFILTERS ( dim_fornecedor )` no denominador, e não `ALLSELECTED`.** Com um filtro
  "N superiores" no visual, `ALLSELECTED` calcula a participação só entre os N fornecedores
  que aparecem: os 5 maiores somariam 100%. `REMOVEFILTERS` compara com todos os
  fornecedores do contexto (categoria, período, órgão).
- **Participação Acumulada guarda o gasto por fornecedor numa variável.** A primeira versão
  recalculava o gasto de todos os fornecedores para cada fornecedor (6.913 × 6.913 contas em
  informática) e não terminou em 5 minutos. Com a tabela calculada uma vez, a mesma consulta
  leva segundos.

O grão das medidas de fornecedor é o CNPJ (`dim_fornecedor[documento]`), o mesmo do SQL. Um
visual só com `nome` junta matriz e filiais e deixa a Posição em branco.

## Conferência

As medidas foram executadas no modelo e comparadas com as tabelas do BigQuery em
04/10/2026. Sem filtro:

| Medida | Power BI | Consulta de origem no BigQuery |
|---|---|---|
| Gasto Total | 15.805.333.119,66 | `SELECT SUM(valor_total) FROM fato_item_compra` |
| Itens Comprados | 334.901 | `SELECT COUNT(*) FROM fato_item_compra` |
| Fornecedores | 16.012 | `SELECT COUNT(*) FROM dim_fornecedor` |
| Órgãos | 2.470 | `SELECT COUNT(*) FROM dim_orgao` |
| Compras Comparáveis | 267.183 | `qualidade_resumo`, última linha |
| Gasto Comparável | 10.741.223.456,65 | `qualidade_resumo`, última linha |
| Itens com Preço Suspeito | 11.702 | `qualidade_resumo` |
| Economia Teto | 2.269.801.345,61 | soma de `mart_resumo_categoria.economia_teto` |
| Economia Conservadora | 1.074.849.587,12 | soma de `economia_conservadora` |
| Economia Defensável | 263.690.362,49 | soma de `economia_homogenea` |
| % Economia Defensável | 6,80% | `economia_homogenea / gasto_homogeneo` |

Por categoria:

| Categoria | Gasto Total | Economia Defensável | HHI |
|---|---|---|---|
| Informática | 12.922.963.783,40 | 190.829.142,09 | 197,03 |
| Escritório | 2.274.192.364,35 | 55.172.503,65 | 317,78 |
| Limpeza | 608.176.971,91 | 17.688.716,75 | 44,90 |

Cinco maiores fornecedores de informática (iguais a `mart_gasto_fornecedor`):

| Posição | Fornecedor | Gasto | Participação | Acumulada | Classe |
|---|---|---|---|---|---|
| 1 | Positivo Tecnologia S.A. | 989.979.438,72 | 7,66% | 7,66% | A |
| 2 | Kona Indústria e Comércio Ltda | 570.900.000,00 | 4,42% | 12,08% | A |
| 3 | Lenovo Tecnologia (Brasil) Limitada | 552.239.324,06 | 4,27% | 16,35% | A |
| 4 | Lider Notebooks Comércio e Serviços Ltda | 536.639.541,70 | 4,15% | 20,50% | A |
| 5 | Grupo Multilaser S.A. | 431.254.399,00 | 3,34% | 23,84% | A |

Se um número do painel não bater com estes, o erro está no visual (campo, filtro ou
relacionamento): os totais do BigQuery são conferidos pelos testes de `sql/tests/`.
