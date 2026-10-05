# Design do painel

As decisões de design estão no código ([tema.py](../src/compras/painel/tema.py) e
[paginas.py](../src/compras/painel/paginas.py)). Este documento explica o porquê de cada uma.

![Onde está o gasto](../docs/img/painel-gasto.png)

## Princípios

| Princípio | Como aparece no painel |
|---|---|
| **Uma pergunta por página** | cada página tem como título a pergunta que responde: onde está o gasto, onde se paga caro, quanto dá para economizar |
| **Hierarquia: do resumo ao detalhe** | faixa com a pergunta → um número principal → indicadores de apoio → gráficos e tabelas |
| **Um número lidera** | cada página tem um único indicador em destaque: maior e na cor da área |
| **Duas camadas de cor** | a cor de identidade diz de que área é o painel; a cor de dado fica só nos gráficos |
| **Tamanho de fonte faz a hierarquia** | uma família de fonte, seis tamanhos, com degraus visíveis entre eles |
| **Consistência** | as três páginas têm a mesma estrutura e o filtro no mesmo lugar; o leitor aprende uma vez |
| **A forma segue a tarefa** | nem tudo é gráfico: valores para comparar com exatidão vão em tabela |
| **Funciona no celular** | cada página tem um layout próprio para tela estreita, na mesma ordem de leitura |

## Tema por área de negócio

O tema é o recurso nativo do Power BI para personalizar um relatório: cores de dados,
classes de texto e estilo por tipo de visual, num arquivo JSON. Aqui esse arquivo é gerado
a partir de **duas cores por área**; o resto é derivado.

```powershell
python -m compras painel --tema financeiro
```

| Tema | Área | Identidade | Dado | Branco sobre a identidade | Texto suave sobre a identidade | Dado sobre o cartão |
|---|---|---|---|---|---|---|
| `compras` (padrão) | Compras e suprimentos | `#0B3F4C` | `#0E8FA8` | 11,5:1 | 8,2:1 | 3,7:1 |
| `financeiro` | Financeiro e controladoria | `#14305E` | `#2A78D6` | 13,0:1 | 9,3:1 | 4,3:1 |
| `vendas` | Vendas e comercial | `#3F1D6B` | `#7C4DDB` | 13,1:1 | 9,2:1 | 5,2:1 |
| `pessoas` | Pessoas (RH) | `#6B1D43` | `#C2477F` | 11,2:1 | 7,9:1 | 4,6:1 |
| `operacoes` | Operações e logística | `#263238` | `#2F8FC4` | 13,2:1 | 9,4:1 | 3,5:1 |

Os contrastes são calculados pela fórmula da WCAG em `tema.contraste`. Os alvos são 4,5:1
para texto e 3:1 para marcas de gráfico, e um teste falha se um tema novo ficar abaixo.

### As duas camadas

| Camada | Onde aparece | Papel |
|---|---|---|
| **Identidade** | faixa do cabeçalho, número principal, cabeçalho das tabelas | dizer de que área é o painel e para onde olhar primeiro |
| **Dado** | barras, linhas e áreas | carregar o valor; uma série, uma cor |
| **Neutros** | fundo da página, bordas, grade | recebem de 5% a 10% da cor de identidade, para não ficarem cinza puro |

A primeira versão do painel usava uma cor só para tudo e ficou genérica: a regra "uma série,
uma cor" vale para os gráficos, e tinha sido aplicada à página inteira. A identidade entra
na **estrutura** (faixa, destaque), onde não compete com o dado.

Verde e âmbar ficam fora das duas camadas: são cores de estado (bom, atenção) e, em barras
comuns, sugerem um julgamento que o dado não faz.

### Validação da cor de dado

Cada cor de dado passou num validador de paleta contra a superfície do cartão (faixa de
luminosidade, saturação mínima e contraste):

```
Palette (light, surface #FDFDFC, categorical): 1 slots
  [PASS] Lightness band         all 1 inside L 0.43–0.77
  [PASS] Chroma floor           all 1 >= 0.1
  [PASS] Contrast vs surface    all 1 >= 3:1
  → ALL CHECKS PASS
```

Duas candidatas foram reprovadas e trocadas: `#1789A0` e `#3D7EA6` ficaram abaixo da
saturação mínima (leem como cinza).

O teste `test_graficos_tem_uma_serie_so` falha se alguém acrescentar um gráfico com várias
séries: nesse caso a paleta precisa crescer e ser validada de novo, não improvisada.

### Como criar o tema de outra área

1. Escolha a cor de identidade (escura, para o texto branco ter contraste) e a cor de dado.
2. Acrescente uma linha em `TEMAS`, em `tema.py`.
3. Rode os testes: eles conferem os contrastes e se as cores não repetem as de outro tema.
4. Gere, abra e capture; olhe o resultado.

## Hierarquia de tamanhos

Uma família só, Segoe UI. Quem faz a hierarquia é o **tamanho**, em seis níveis:

| Nível | Tamanho | Onde |
|---|---|---|
| Destaque | 44 pt | o número principal da página |
| Indicador | 26 pt | os números de apoio |
| Pergunta | 20 pt | o título da página, na faixa |
| Título | 12 pt | o título de cada visual |
| Corpo | 10 pt | escopo, rótulo dos indicadores, filtro |
| Apoio | 9 pt | eixos, rótulos de barra, tabelas |

Cada nível é menor que o anterior, e os quatro primeiros degraus são de pelo menos 20%
(44 → 26 → 20 → 12 → 10). Abaixo disso a diferença não se percebe e a hierarquia some.
O teste `test_escala_de_tamanhos_tem_degraus_visiveis` protege essa regra.

O texto nunca usa a cor do dado: valores e rótulos ficam em tinta escura ou cinza.

## Estrutura da página

Página de 1280 × 720, margem de 24 e espaço de 16 entre os blocos.

```
┌──────────────────────────────────────────────────────────────────┐
│ INTELIGÊNCIA DE COMPRA                              ┌───────────┐ │
│ A pergunta da página                                │ Categoria │ │  faixa (identidade)
│ Escopo dos dados                                    └───────────┘ │
├──────────────┬─────────┬─────────┬─────────┬─────────────────────┤
│ NÚMERO       │ apoio   │ apoio   │ apoio   │ apoio               │  indicadores
│ PRINCIPAL    │         │         │         │                     │
├──────────────┴─────────┴─────────┴─────────┴─────────────────────┤
│              gráficos e tabelas que detalham a resposta          │  corpo
└──────────────────────────────────────────────────────────────────┘
```

- **O filtro fica sempre no canto superior direito**, sobre a faixa, e vale para as três
  páginas ao mesmo tempo.
- **O número principal é a resposta curta da página:** gasto total, gasto acima do terceiro
  quartil, economia defensável.
- **Na página de economia, o número em destaque é o menor dos três**, porque é o que
  sustenta a decisão.

## Celular

![Layout de celular](../docs/img/celular-gasto.png)

O Power BI guarda, para cada visual, uma posição própria para o celular (arquivo
`mobile.json` ao lado do `visual.json`). O gerador escreve os dois.

| Decisão | Por quê |
|---|---|
| Uma coluna, 320 de largura | é a largura da tela de celular no Power BI; nada exige rolar para o lado |
| Mesma ordem da página: pergunta → filtro → número principal → apoio → detalhe | a hierarquia não muda com o tamanho da tela |
| Indicadores de apoio em pares | quatro números cabem na primeira tela junto com o principal |
| Gráficos antes das tabelas | gráfico de barras lê bem em tela estreita; tabela larga pede rolagem lateral |
| Fontes ajustadas só no celular | a pergunta desce para 16 pt e os números de apoio para 20 pt; títulos longos quebram em duas linhas |

Os testes garantem que todo visual da página aparece no celular, que nenhum passa da
largura da tela ou fica estreito demais para tocar, que não há sobreposição e que a ordem
segue a hierarquia.

## Escolha da forma

| Dado | Forma | Por quê |
|---|---|---|
| Um valor que resume a página | número em destaque | um gráfico de uma barra não diz nada que o número não diga |
| Comparar magnitudes entre categorias | barras horizontais, ordenadas do maior ao menor | nomes longos cabem; a ordem já responde "quem é o maior" |
| Evolução no tempo | área com linha | mostra tendência; sem rótulo em cada ponto |
| Muitos atributos por linha (fornecedor, item, órgão) | tabela | o leitor precisa do valor exato e do nome |
| Três estimativas × três categorias | tabela | nove valores com escalas muito diferentes: em colunas agrupadas, as duas categorias menores viravam traços |

Todo visual de ranking é limitado aos N maiores, e o título diz o N ("Os 8 maiores…").

## Detalhes que vieram de olhar o resultado

As capturas de tela fazem parte do processo (`scripts/capturar.ps1`, com `-Celular` para o
layout de celular). Os testes garantem estrutura; só olhando aparece o que segue, tudo
corrigido no código:

| O que a captura mostrou | Correção |
|---|---|
| Rótulo dentro da barra, texto escuro sobre a cor | rótulos sempre fora da ponta da barra |
| Um rótulo em cada mês do gráfico de tempo | sem rótulos; o eixo carrega os valores |
| Subtítulo e aviso cortados, com barra de rolagem | caixas de texto com altura para o texto que levam |
| Última coluna das tabelas cortada | largura de cada coluna definida no código |
| Linha de total somando percentis | tabelas sem linha de total |
| Colunas agrupadas ilegíveis para as três estimativas | trocadas por tabela |
| Rótulo do número principal cortado ("Gasto em compras acima do terceiro quar…") | rótulo curto; a explicação foi para o escopo, na faixa |
| Nomes de órgãos cortados no eixo | até 40% da largura do gráfico para os nomes; os mais longos ainda terminam em reticências |
| No celular, pergunta em duas linhas empurrando o escopo para fora da faixa | pergunta menor no celular e faixa mais alta onde o texto é longo |
| No celular, rótulo de indicador cortado ("Órgãos comprado…") | rótulos de até 16 letras nos indicadores em par |
| No celular, título de gráfico cortado | títulos quebram em duas linhas |

## Limites

- **Sem modo escuro.** O Power BI aplica um tema por relatório; um tema escuro pediria
  outra seleção de tons, validada contra a superfície escura.
- **Um tema por relatório.** Trocar de área é gerar de novo com `--tema`; não há troca
  dentro do painel aberto.
- **Só o tema `compras` foi aberto e capturado.** Os outros quatro passam nos testes de
  contraste, mas não foram vistos renderizados.
- **Tabelas no celular rolam para o lado.** O Power BI não esconde colunas por layout; as
  primeiras colunas (posição e nome) aparecem, as demais pedem rolagem.
- **Barras com cantos retos.** O visual de barras usado não oferece canto arredondado.
- **Sem variação entre períodos nos indicadores.** O recorte são dois anos fechados de
  contratações; comparar "com o período anterior" não faria sentido aqui.
- **Acabamento de um analista, não de um designer.** O objetivo é leitura clara, hierarquia
  e consistência; marca gráfica (logotipo, ícones, ilustração) está fora do escopo.
