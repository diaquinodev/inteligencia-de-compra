# Análises: as três perguntas

Todos os números saem das tabelas `mart_` e foram lidos em 03/10/2026. Recorte: compras
federais de material de escritório, informática e limpeza com resultado em contratações de
2024 e 2025.

## 1. Onde está o gasto?

`mart_gasto_fornecedor` e `mart_resumo_categoria`.

| Categoria | Gasto (R$ mi) | Itens comprados | Órgãos | Fornecedores | Top 10 | HHI |
|---|---|---|---|---|---|---|
| Informática | 12.923,0 | 77.068 | 2.089 | 6.913 | 37,7% | 197 |
| Escritório | 2.274,2 | 185.629 | 1.978 | 8.131 | 39,9% | 318 |
| Limpeza | 608,2 | 72.204 | 1.669 | 6.060 | 15,5% | 45 |

**Leitura:** o dinheiro está em informática (82% do gasto), mas o trabalho está em escritório
(55% dos itens comprados). O mercado é pulverizado: o HHI fica muito abaixo de 2.500, o
limite usual para "concentrado". Não há dependência de poucos fornecedores; o problema é o
oposto.

### Curva ABC de fornecedores

| Categoria | Classe A (80% do gasto) | Classe B (até 95%) | Classe C (5% finais) |
|---|---|---|---|
| Informática | 116 fornecedores | 413 | 6.384 |
| Escritório | 309 | 876 | 6.946 |
| Limpeza | 565 | 980 | 4.515 |

**Leitura:** em informática, 116 fornecedores respondem por 80% do gasto e outros 6.384
dividem os últimos 5%. É a "cauda longa": milhares de fornecedores que custam para
contratar, cadastrar e pagar, e somam pouco valor.

## 2. Onde se paga caro?

`mart_preco_item`. A comparação é sempre dentro do **grupo de comparação**: mesmo item de
catálogo, mesma unidade de medida, com pelo menos 10 compras e sem preços suspeitos. São
6.822 grupos e 267.183 compras.

Exemplos em que o mesmo produto tem preços bem diferentes:

| Item | Unidade | Compras | Órgãos | p25 | Mediana | p75 | Máximo |
|---|---|---|---|---|---|---|---|
| Papel A4 75 g/m² | unidade (resma) | 377 | 169 | R$ 19,78 | R$ 22,04 | R$ 26,16 | R$ 225,00 |
| Água sanitária | litro | 182 | 89 | R$ 1,72 | R$ 1,99 | R$ 2,62 | R$ 18,36 |
| Monitor 23 a 30 pol. LED | unidade | 58 | 27 | R$ 622,00 | R$ 724,00 | R$ 962,00 | R$ 3.625,00 |
| Disco de feltro de enceradeira 380 mm | unidade | 162 | 52 | R$ 19,98 | R$ 26,50 | R$ 36,48 | R$ 167,00 |

**Leitura:** um quarto das compras de papel A4 pagou mais de R$ 26,16 por um produto cuja
metade das compras saiu por até R$ 22,04.

## 3. Quanto dá para economizar?

`mart_economia_item`. Três estimativas, da mais otimista à mais defensável:

| Estimativa | Regra | Informática | Escritório | Limpeza | Total (R$ mi) |
|---|---|---|---|---|---|
| Teto | toda compra acima da mediana passa a pagar a mediana | 1.978,1 | 213,8 | 77,9 | 2.269,8 |
| Conservadora | só as compras acima do p75 caem para o p75 | 930,1 | 105,5 | 39,3 | 1.074,9 |
| **Defensável** | conservadora, só em grupos de preço homogêneo | **190,8** | **55,2** | **17,7** | **263,7** |

A estimativa defensável vale para R$ 3.876,9 milhões de gasto (os grupos de preço homogêneo)
e representa 6,8% desse valor.

### Por que três números

O código de catálogo não garante produto idêntico. "Notebook, tela até 14 pol." tem p25 de
R$ 3.442 e p75 de R$ 11.812: a diferença vem de configurações diferentes, não de alguém
pagando caro. Tratar isso como economia seria errado.

Por isso a estimativa defensável só usa grupos de **preço homogêneo**, em que o p75 custa no
máximo 2 vezes o p25 (3.987 dos 6.822 grupos). Neles, uma compra acima do p75 dificilmente
se explica por um produto diferente.

### Onde agir primeiro (grupos homogêneos com 50+ compras)

| Categoria | Item | Compras | Acima do p75 | Economia (R$ mi) |
|---|---|---|---|---|
| Informática | Monitor 23 a 30 pol. LED | 58 | 15 | 10,36 |
| Informática | Notebook, tela acima de 14 pol. | 106 | 27 | 8,50 |
| Informática | Monitor 23 a 30 pol. LED (outra especificação) | 109 | 27 | 4,85 |
| Escritório | Papel A4 75 g/m² | 377 | 94 | 4,20 |
| Escritório | Caderno, papel off-set 63 g/m² | 78 | 20 | 3,18 |
| Escritório | Caderno, papel off-set 56 g/m² | 80 | 20 | 2,28 |
| Limpeza | Água sanitária (litro) | 182 | 45 | 1,81 |
| Limpeza | Disco de feltro de enceradeira 380 mm | 162 | 41 | 1,13 |

## A decisão que os dados sustentam

1. **Preço de referência por item** para os grupos homogêneos: nenhuma compra acima do p75
   sem justificativa. Potencial de R$ 263,7 milhões no período.
2. **Compra centralizada** (ata de registro de preços) para os itens de alto volume e preço
   homogêneo, começando por monitores, notebooks e papel A4.
3. **Reduzir a cauda de fornecedores** de classe C: mais de 6 mil fornecedores por categoria
   para 5% do gasto.

## O que os dados não permitem concluir

- **Sobrepreço ou irregularidade.** Preço acima do p75 pode ter razão legítima: frete para
  local remoto, lote pequeno, prazo curto, marca exigida. A análise aponta onde olhar.
- **Economia em itens heterogêneos.** As estimativas "teto" e "conservadora" incluem
  diferenças de especificação e superestimam o ganho. Separar as especificações exige ler a
  descrição livre de cada item, o próximo passo do projeto.
- **Gasto total do governo nessas categorias.** Ficaram de fora itens sem código de
  catálogo, compras sem resultado homologado e anos com cobertura baixa.
- **Conclusões sobre uma empresa privada.** Os dados são de compras públicas, usados aqui
  como substituto de um ERP corporativo. O método se aplica igual; os números, não.
