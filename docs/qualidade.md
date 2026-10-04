# Qualidade de dados

Duas coisas diferentes acontecem aqui:

- **Regras de limpeza** decidem quais linhas entram na análise. Elas não escondem nada: a
  linha fica na camada limpa com o motivo da exclusão, e a tabela `qualidade_resumo` conta
  quantas linhas e quanto valor cada regra tirou.
- **Testes** conferem se o resultado final está íntegro. Cada teste é uma consulta em
  `sql/tests/` que deve voltar vazia; qualquer linha devolvida é uma violação.

## O funil, com os números reais

Saída de `SELECT * FROM qualidade_resumo ORDER BY ordem` (03/10/2026):

| Etapa | Linhas | Valor (R$ milhões) |
|---|---|---|
| Linhas do recorte na origem | 426.237 | 31.065,6 |
| Removidas: item repetido na origem | 417 | — |
| Fora da análise: sem resultado homologado | 59.880 | 1.549,1 |
| Fora da análise: não é material | 30.238 | 13.692,2 |
| Fora da análise: preço ou quantidade inválidos | 801 | 0,0 |
| **Válidas (entram na fato)** | **334.901** | **15.805,3** |
| Válidas com preço suspeito | 11.702 | 3.136,8 |
| Válidas em grupo com menos de 10 compras | 56.016 | 1.927,3 |
| **Comparáveis (base das perguntas de preço)** | **267.183** | **10.741,2** |

## As regras de limpeza e por que existem

| Regra | O que foi encontrado | Decisão |
|---|---|---|
| Item repetido | 417 linhas com o mesmo `id_compra_item` | fica a inclusão mais recente |
| Não é material | 30.238 linhas de **serviço** cujo código coincide com um código de material do catálogo; somam R$ 13,7 bi | fora: sem o filtro, o gasto quase dobraria com itens de outra natureza |
| Sem resultado homologado | itens desertos, fracassados, cancelados ou em andamento | fora: não houve compra |
| Preço ou quantidade inválidos | zero ou vazio | fora |
| Unidade de medida | 948 grafias ("Caixa 12,00 UN", "CAIXA 12 UN", "UN", "Unidade") | padronizadas para 570; a comparação de preço é sempre dentro da mesma unidade |
| Preço suspeito | preço mais de 10 vezes acima ou abaixo da mediana do grupo (ex.: 1 microcomputador por R$ 144,9 milhões) | a compra continua no gasto, mas sai da comparação de preços e da referência |
| Grupo pequeno | menos de 10 compras do mesmo item na mesma unidade | sai da comparação: não há base para uma referência de preço |
| Cabeçalho repetido | 95 contratações republicadas aparecem mais de uma vez | fica a publicação mais recente |
| Pessoa física | 12 fornecedores com CPF | o CPF vira um código sem volta e o nome é omitido |

A regra do cabeçalho repetido nasceu de um teste: a primeira versão da fato saiu com 269
linhas a mais que a camada limpa, porque a junção com o cabeçalho duplicava itens. A
conferência de totais acusou a diferença antes de qualquer análise.

## Os testes

`python -m compras testar` — resultado em 03/10/2026: **11 de 11 regras passaram**.

| Teste | O que garante |
|---|---|
| `fato_chave_unica` | cada item de contratação aparece uma vez |
| `fato_dimensoes_presentes` | toda linha da fato encontra item, fornecedor, órgão e data |
| `fato_valores_positivos` | quantidade, preço e total maiores que zero |
| `fato_total_igual_preco_vezes_quantidade` | total = preço × quantidade (tolerância de 1%) |
| `fato_total_bate_com_camada_limpa` | nada se perde nem se duplica entre a camada limpa e a fato |
| `dimensoes_chave_unica` | código do item, documento do fornecedor e CNPJ do órgão não se repetem |
| `fornecedor_cnpj_valido` | os dois dígitos verificadores de cada CNPJ conferem (23.261 CNPJs) |
| `pessoa_fisica_nao_identificada` | nenhum CPF ou nome de pessoa física chega ao modelo |
| `preco_de_referencia_coerente` | p25 ≤ mediana ≤ p75 e grupo com 10+ compras |
| `economia_coerente` | economia ≥ 0, conservadora ≤ teto, teto ≤ gasto |
| `participacao_soma_cem_por_cento` | as participações dos fornecedores somam 100% por categoria |

## Os testes pegam erro de verdade?

Teste que nunca falha não prova nada. As tabelas foram copiadas para um conjunto descartável
e três erros foram plantados na fato: uma linha duplicada, um preço negativo e um fornecedor
inexistente. Resultado:

```
ok      dimensoes_chave_unica  (0 violações)
ok      economia_coerente  (0 violações)
FALHOU  fato_chave_unica  (1 violações)
FALHOU  fato_dimensoes_presentes  (1 violações)
FALHOU  fato_total_bate_com_camada_limpa  (1 violações)
FALHOU  fato_total_igual_preco_vezes_quantidade  (1 violações)
FALHOU  fato_valores_positivos  (1 violações)
ok      fornecedor_cnpj_valido  (0 violações)
ok      participacao_soma_cem_por_cento  (0 violações)
ok      pessoa_fisica_nao_identificada  (0 violações)
ok      preco_de_referencia_coerente  (0 violações)
6 de 11 regras passaram.
```

Os três erros foram pegos por cinco regras. O conjunto descartável foi apagado em seguida.
