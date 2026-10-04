# Validação dos dados (antes de escrever o pipeline)

Pergunta desta etapa: os dados públicos permitem comparar o preço do mesmo item entre
compradores? Se não permitissem, o projeto mudaria de tema.

Fonte: [Base dos Dados](https://basedosdados.org/dataset/bb11d3e6-6bac-412e-bbb8-773369771a70),
conjunto `basedosdados.br_mgi_compras_publicas` no BigQuery. Consultas rodadas em 03/10/2026.

## Tabelas que servem ao projeto

| Tabela | Linhas | Tamanho | Uso |
|---|---|---|---|
| `contratacao_item` | 8.119.424 | 4,29 GB | itens comprados: código de catálogo, unidade, quantidade, preço, fornecedor |
| `contratacao` | 980.713 | 0,84 GB | cabeçalho: órgão, UF, modalidade |
| `catalogo_material` | 345.131 | 0,11 GB | hierarquia grupo > classe > item |
| `fornecedor` | 962.012 | 0,16 GB | cadastro: razão social, porte, UF |

## Cobertura dos campos em `contratacao_item`

```sql
SELECT
    ano,
    COUNT(*) AS itens,
    ROUND(100 * COUNTIF(codigo_item_catalogo IS NOT NULL AND codigo_item_catalogo != '') / COUNT(*), 1) AS pct_com_codigo,
    ROUND(100 * COUNTIF(valor_unitario_resultado > 0 AND quantidade_resultado > 0) / COUNT(*), 1) AS pct_preco_qtd,
    ROUND(100 * COUNTIF(unidade_medida IS NOT NULL AND unidade_medida != '') / COUNT(*), 1) AS pct_unidade,
    ROUND(SUM(valor_total_resultado) / 1e9, 2) AS total_bi
FROM `basedosdados.br_mgi_compras_publicas.contratacao_item`
GROUP BY ano
ORDER BY ano;
```

| Ano | Itens | Com código de catálogo | Com preço e quantidade | Com unidade | Total (R$ bi) |
|---|---|---|---|---|---|
| 2021 | 30.298 | 79,5% | 51,5% | 100% | 0,47 |
| 2022 | 151.951 | 96,0% | 68,6% | 100% | 4,46 |
| 2023 | 747.129 | 97,0% | 76,2% | 100% | 96,51 |
| 2024 | 2.500.503 | 93,8% | 79,2% | 100% | 6.099,45 |
| 2025 | 2.828.889 | 93,2% | 78,9% | 100% | 1.231,02 |
| 2026 | 505.496 | 68,5% | 77,4% | 100% | 78,98 |

## O que a validação mostrou

1. **Os dados servem.** Em 2024 e 2025, mais de 93% dos itens têm código de catálogo e cerca
   de 79% têm preço e quantidade do resultado.
2. **Os totais brutos não são confiáveis.** 2024 soma R$ 6,1 trilhões, valor impossível:
   há linhas com o valor do lote inteiro no campo de preço unitário. O pipeline precisa de
   uma regra para preço suspeito.
3. **A coluna de grupo vem vazia na tabela de itens.** A categoria só existe no catálogo e
   chega por junção pelo código do item.
4. **2021, 2022 e 2026 ficam de fora:** os dois primeiros têm pouca cobertura e 2026 está
   incompleto.

## Recorte escolhido: compras indiretas, 2024 e 2025

Itens de material com código e preço, por grupo do catálogo:

| Grupo | Linhas | Itens distintos | Órgãos | Fornecedores | Itens com 20+ compras |
|---|---|---|---|---|---|
| 75 — Utensílios de escritório e material de expediente | 186.618 | 7.885 | 1.981 | 8.164 | 2.232 |
| 70 — Informática: equipamentos, peças, acessórios e suprimentos | 77.674 | 4.460 | 2.094 | 6.952 | 1.001 |
| 79 — Equipamentos e materiais para limpeza | 72.750 | 1.112 | 1.670 | 6.077 | 636 |

São categorias que toda empresa compra, com volume para comparar preços e tamanho que cabe
no modo gratuito do BigQuery.

## Dois limites técnicos encontrados

- O BigQuery não devolve estimativa de bytes (dry run) para `contratacao_item` e
  `contratacao`, que são particionadas por ano. O executor trata isso: quando não há
  estimativa, a proteção é o teto de bytes aplicado pelo próprio BigQuery na execução.
- `INFORMATION_SCHEMA` do projeto `basedosdados` não é acessível a usuários externos; as
  tabelas foram mapeadas com `bq ls` e `bq show`.
