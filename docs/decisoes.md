# Decisões de projeto

Por etapa: o que foi feito, por que assim e as objeções que cada escolha precisa responder.

## Em uma frase

Peguei 8 milhões de itens de compras públicas, recortei três categorias que toda empresa
compra, limpei, modelei em estrela e respondi onde está o gasto, onde se paga caro e quanto
dá para economizar — chegando a R$ 263,7 milhões defensáveis em R$ 15,8 bilhões analisados.

## Validação antes de construir

- **O quê:** antes de qualquer pipeline, medi se os campos necessários estavam preenchidos.
- **Por quê:** se o código de catálogo ou o preço fossem raros, o projeto inteiro seria
  inviável. Melhor descobrir em uma consulta do que depois de modelar.
- **Achado:** o total de 2024 somava R$ 6,1 trilhões. Dado público não é dado limpo.

## Executor e teto de custo

- **O quê:** um programa pequeno roda os arquivos SQL em ordem. Cada consulta passa por
  estimativa de custo e tem um teto de bytes.
- **Por quê:** a tabela pública tem 4 GB e a cota gratuita é de 1 TiB por mês. Um
  `SELECT *` repetido algumas vezes compromete a cota. A trava está no código, não na
  disciplina de quem escreve a consulta.
- **Objeção:** "e se a estimativa falhar?" Ela falha de fato para tabelas
  particionadas (o BigQuery não devolve o número). Nesse caso a proteção é o
  `maximum_bytes_billed`, aplicado pelo próprio BigQuery: a consulta é recusada, não cobrada.
- **Idempotência:** tudo é `CREATE OR REPLACE TABLE`. Rodar duas vezes dá o mesmo
  resultado, e as tabelas que expiram em 60 dias voltam com um comando.

## Camadas bruta e limpa

- **Bruta:** só o recorte, sem transformar. Depois dela, nenhuma consulta lê a tabela
  pública grande.
- **Limpa:** nenhuma linha some sem explicação. A coluna `motivo_exclusao` registra por que
  cada linha ficou de fora, e isso vira um relatório.
- **Objeção:** "por que não apagar as linhas ruins?" Porque quem lê a análise
  precisa saber quanto ficou de fora. 30 mil linhas de serviço com R$ 13,7 bilhões estavam
  misturadas aos materiais; sem o registro, ninguém saberia que o filtro existe.

## Unidade de medida

- **O quê:** 948 grafias viraram 570. "Caixa 12,00 UN" e "CAIXA 12 UN" são a mesma coisa.
- **Por quê:** comparar o preço de uma caixa com o de uma unidade gera falso alarme. O grupo
  de comparação é sempre item + unidade.
- **Limite honesto:** não converti embalagens para uma unidade base (preço por folha, por
  litro). Caixa de 50 e caixa de 100 são grupos separados.

## Preço suspeito

- **O quê:** preço mais de 10 vezes acima ou abaixo da mediana do grupo fica fora da
  comparação. A referência é recalculada sem ele.
- **Por quê:** um microcomputador por R$ 144,9 milhões é o valor do lote digitado como
  preço unitário. Entrando na conta, criaria uma "economia" imaginária.
- **Objeção:** "por que 10 vezes e não 3?" O corte é deliberadamente largo: tira
  erro de digitação sem esconder variação real de preço. A variação entre 1 e 10 vezes
  continua na análise, que é justamente o que se quer estudar.
- **Detalhe:** a compra continua no gasto total. O valor pago é real; só o preço unitário
  não serve de referência.

## Window functions usadas

| Onde | Função | Para quê |
|---|---|---|
| `stg_item` | `ROW_NUMBER() OVER (PARTITION BY ...)` com `QUALIFY` | ficar com uma linha por item repetido |
| `stg_item_valido` | `PERCENTILE_CONT(...) OVER (PARTITION BY item, unidade)` | mediana e quartis do grupo em cada linha |
| `stg_item_valido` | `COUNT(*) OVER` e `COUNTIF(...) OVER` | tamanho do grupo de comparação |
| `mart_gasto_fornecedor` | `RANK()`, `SUM() OVER (... ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` | posição e participação acumulada (curva ABC) |
| `mart_economia_item` | `RANK() OVER (PARTITION BY categoria ...)` | prioridade dentro da categoria |

Diferença para o `GROUP BY`: a window function calcula sobre o grupo e mantém cada linha.
Por isso dá para comparar o preço de uma compra com a mediana do seu grupo na mesma linha.

## Modelo estrela

- **Grão:** um item de uma contratação. Definir o grão primeiro evita o erro clássico de
  somar duas vezes.
- **Erro real:** a primeira versão da fato tinha 269 linhas a mais. O cabeçalho da
  contratação se repete a cada republicação e a junção duplicava itens. Quem pegou foi o
  teste que compara os totais da fato com os da camada limpa.
- **Por que estrela:** o Power BI filtra da dimensão para a fato. Uma tabela única
  funcionaria, mas repetiria nome de fornecedor e descrição de item em 334 mil linhas.

## As três estimativas de economia

- **Teto (R$ 2.269,8 mi):** todo mundo paga a mediana. Irreal, serve de limite superior.
- **Conservadora (R$ 1.074,9 mi):** só quem pagou acima do p75 cai para o p75.
- **Defensável (R$ 263,7 mi):** a conservadora, só nos itens em que o preço varia pouco.
- **Por que não ficar com o número maior:** o mesmo código de catálogo cobre notebooks de
  R$ 3 mil e de R$ 12 mil. Chamar essa diferença de economia não se sustenta diante de
  quem conhece o assunto. Um número menor que resiste a perguntas vale mais.

## O que eu faria diferente com mais tempo

- Ler a descrição livre dos itens para separar especificações dentro do mesmo código (é
  onde um modelo de linguagem ajuda, com medição de acerto).
- Converter embalagens para unidade base.
- Rodar o pipeline agendado e migrar o SQL para dbt.
