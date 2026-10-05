# Design do painel

As decisões de design estão no código ([tema.py](../src/compras/painel/tema.py) e
[paginas.py](../src/compras/painel/paginas.py)). Este documento explica o porquê de cada uma.

![Onde está o gasto](../docs/img/painel-gasto.png)

## Princípios

| Princípio | Como aparece no painel |
|---|---|
| **Uma pergunta por página** | cada página tem como título a pergunta que responde: onde está o gasto, onde se paga caro, quanto dá para economizar |
| **Hierarquia: do resumo ao detalhe** | cabeçalho → um número principal → indicadores de apoio → gráficos e tabelas |
| **Um número lidera** | cada página tem um único indicador em destaque (maior); os outros são contexto |
| **Consistência** | as três páginas têm a mesma estrutura, as mesmas margens e o filtro no mesmo lugar; o leitor aprende uma vez |
| **A cor carrega dado, não decoração** | todo gráfico usa a mesma cor de série; não há cor "para enfeitar" nem para diferenciar páginas |
| **O dado é a única coisa que chama atenção** | grade, eixos, bordas e rótulos são discretos |
| **A forma segue a tarefa** | nem tudo é gráfico: valores para comparar com exatidão vão em tabela |

## Estrutura da página

Página de 1280 × 720, margem de 24 e espaço de 16 entre os blocos.

```
┌──────────────────────────────────────────────────────┬───────────┐
│ INTELIGÊNCIA DE COMPRA                                │ Categoria │  cabeçalho
│ A pergunta da página                                  │ [filtro]  │
│ Escopo dos dados                                      │           │
├──────────────┬─────────┬─────────┬─────────┬─────────┴───────────┤
│ NÚMERO       │ apoio   │ apoio   │ apoio   │ apoio               │  indicadores
│ PRINCIPAL    │         │         │         │                     │
├──────────────┴─────────┴─────────┴─────────┴─────────────────────┤
│                                                                  │
│              gráficos e tabelas que detalham a resposta          │  corpo
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

- **O filtro fica sempre no canto superior direito** e vale para as três páginas ao mesmo
  tempo. Um filtro por gráfico obrigaria o leitor a conferir qual recorte cada um mostra.
- **O número principal é a resposta curta da página:** gasto total, gasto em compras acima
  do terceiro quartil, economia defensável.
- **Na página de economia, a ordem dos indicadores vai do mais defensável ao mais otimista.**
  O número em destaque é o menor dos três, porque é o que sustenta a decisão.

## Cor

| Papel | Cor | Uso |
|---|---|---|
| Dado | `#2A78D6` | toda barra, linha e área |
| Texto principal | `#0B0B0B` | títulos e valores |
| Texto secundário | `#52514E` | rótulos, legendas, cabeçalhos de tabela |
| Texto apagado | `#898781` | eixos |
| Superfície do cartão | `#FCFCFB` | fundo dos visuais |
| Plano da página | `#F4F4F1` | fundo da página |
| Borda e grade | `#E4E3DE` / `#E1E0D9` | linhas de um tom acima da superfície |

### Por que uma cor só

Todos os gráficos do painel têm **uma série**. Com uma série, a cor não tem nada a
distinguir: variar o tom por barra repetiria o que o comprimento já mostra e gastaria o
único canal livre. Cada barra de categoria com uma cor diferente sugeriria que a cor
significa algo, e não significa.

A primeira versão usava azul, verde e âmbar para "dar identidade" a cada página. Foi
retirada por dois motivos:

1. **Verde e âmbar são cores de estado** (bom, atenção). Usá-las em séries comuns ensina o
   leitor a ler um julgamento que o dado não faz: gasto acima do P75 não é, por si, um erro.
2. **O validador reprovou a combinação para daltonismo:** verde e âmbar ficaram com
   separação 6,8, abaixo do alvo de 8 (ΔE em OKLab × 100, simulação de protanopia).

### Validação

A cor de dado foi conferida com um validador de paleta (faixa de luminosidade, saturação
mínima, contraste com a superfície):

```
Palette (light, surface #fcfcfb, categorical): 1 slot
  [PASS] Chroma floor           all 1 >= 0.1
  [PASS] Contrast vs surface    all 1 >= 3:1
  → ALL CHECKS PASS
```

O teste `test_graficos_tem_uma_serie_so` falha se alguém acrescentar um gráfico com várias
séries: nesse caso a paleta precisa crescer e ser validada de novo, não improvisada.

## Tipografia

Uma família só, Segoe UI, em dois pesos. Tamanhos fixos por papel:

| Papel | Tamanho | Peso |
|---|---|---|
| Número principal | 36 pt | semibold |
| Indicador de apoio | 22 pt | semibold |
| Pergunta da página | 18 pt | bold |
| Título de visual | 11 pt | semibold |
| Escopo, rótulos, tabela | 9–10 pt | regular |
| Nome do painel | 8 pt | bold, cinza |

O texto nunca usa a cor do dado. Valores e rótulos ficam em tinta preta ou cinza; quem
carrega a cor é a marca ao lado.

## Escolha da forma

| Dado | Forma | Por quê |
|---|---|---|
| Um valor que resume a página | número em destaque | um gráfico de uma barra não diz nada que o número não diga |
| Comparar magnitudes entre categorias | barras horizontais, ordenadas do maior ao menor | nomes longos cabem; a ordem já responde "quem é o maior" |
| Evolução no tempo | área com linha | mostra tendência; sem rótulo em cada ponto |
| Muitos atributos por linha (fornecedor, item, órgão) | tabela | o leitor precisa do valor exato e do nome |
| Três estimativas × três categorias | tabela | nove valores com escalas muito diferentes: em colunas agrupadas, as duas categorias menores viravam traços e os rótulos se sobrepunham |

Todo visual de ranking é limitado aos N maiores, e o título diz o N ("Os 10 maiores…").
Uma lista de 16 mil fornecedores com barra de rolagem não é um ranking.

## Detalhes que vieram de olhar o resultado

As capturas de tela fazem parte do processo (`scripts/capturar.ps1`). Os testes garantem
estrutura; só olhando aparece o que segue, tudo corrigido no código:

| O que a captura mostrou | Correção |
|---|---|
| Rótulo dentro da barra, texto escuro sobre azul | rótulos sempre fora da ponta da barra |
| Um rótulo em cada mês do gráfico de tempo | sem rótulos; o eixo carrega os valores |
| Subtítulo e aviso cortados, com barra de rolagem | caixas de texto sem margem interna e com altura para três linhas |
| Filtro de categoria cortado embaixo | altura maior |
| Última coluna das tabelas cortada | largura de cada coluna definida no código |
| Linha de total somando percentis | tabelas sem linha de total |
| Colunas agrupadas ilegíveis para as três estimativas | trocadas por tabela |
| Rótulo de indicador truncado | texto mais curto |

## Limites

- **Sem modo escuro.** O Power BI aplica um tema por relatório; um tema escuro pediria
  outra seleção de tons, validada contra a superfície escura.
- **Barras com cantos retos.** O visual de barras usado não oferece canto arredondado na
  ponta.
- **Sem variação entre períodos nos indicadores.** O recorte são dois anos fechados de
  contratações; comparar "com o período anterior" não faria sentido aqui.
- **Acabamento de um analista, não de um designer.** O objetivo é leitura clara e
  consistente; identidade visual de marca está fora do escopo.
