# Roteiro de montagem do painel no Power BI

Tempo estimado: 2 a 3 horas na primeira vez. As medidas estão em [medidas.md](medidas.md).

## 1. Conectar ao BigQuery

1. Power BI Desktop → **Obter dados** → **Google BigQuery** → **Conectar**.
2. Entre com a conta Google dona do projeto `inteligencia-de-compra`.
3. No navegador de tabelas, abra o projeto → conjunto `compras` e marque:
   `fato_item_compra`, `dim_item`, `dim_fornecedor`, `dim_orgao`, `dim_tempo`.
4. Modo de conectividade: **Importar**. As tabelas do modo gratuito do BigQuery expiram em
   60 dias; importadas, ficam guardadas no arquivo do painel.
5. **Carregar**.

## 2. Relacionamentos (exibição de Modelo)

Todos "um para muitos", da dimensão para a fato, direção de filtro única:

| De (um) | Para (muitos) |
|---|---|
| `dim_item[sk_item]` | `fato_item_compra[sk_item]` |
| `dim_fornecedor[sk_fornecedor]` | `fato_item_compra[sk_fornecedor]` |
| `dim_orgao[sk_orgao]` | `fato_item_compra[sk_orgao]` |
| `dim_tempo[data]` | `fato_item_compra[data]` |

Depois: selecione `dim_tempo` → **Ferramentas da tabela** → **Marcar como tabela de data** →
coluna `data`. Sem isso, as medidas de tempo não funcionam.

## 3. Medidas

1. **Página inicial** → **Inserir dados** → sem preencher nada, nome `Medidas` → **Carregar**.
2. Exibição de **consulta DAX** (ícone DAX na barra da esquerda): cole o conteúdo de
   [medidas.dax](medidas.dax) e clique em **Executar**.
3. Compare os dois resultados com a seção "Conferência" de [medidas.md](medidas.md). Se o
   Gasto Total não mostrar R$ 15,8 bilhões, pare e revise os relacionamentos.
4. Clique em **Atualizar o modelo com alterações** para gravar as 24 medidas.
5. Formate as de valor como moeda (R$) e as de participação como percentual; oculte a
   `Coluna 1` da tabela `Medidas`.

## 4. Página 1 — Onde está o gasto

| Visual | Campos |
|---|---|
| 4 cartões no topo | Gasto Total, Itens Comprados, Fornecedores, Órgãos |
| Barras horizontais | eixo `dim_item[categoria]`, valor Gasto Total |
| Linha | eixo `dim_tempo[ano_mes]`, valor Gasto Total |
| Tabela (top 20 fornecedores) | `dim_fornecedor[documento]`, `dim_fornecedor[nome]`, Posição do Fornecedor, Gasto Total, Participação no Gasto, Participação Acumulada, Classe ABC; filtro "N superiores" = 20 por Gasto Total |
| Mapa ou barras | `fato_item_compra[sigla_uf]`, Gasto Total |
| Cartão | HHI |
| Segmentação | `dim_item[categoria]` (sincronizada entre as páginas) |

Pergunta que a página responde: em que categoria e com quais fornecedores o dinheiro está?

## 5. Página 2 — Onde se paga caro

| Visual | Campos |
|---|---|
| Cartões | Compras Comparáveis, % Compras Acima do P75, Itens com Preço Suspeito |
| Tabela de itens | `dim_item[nome_padrao]`, `fato_item_compra[unidade_medida]`, Compras Comparáveis, Preço Mediano, mínimo e máximo de `valor_unitario`, % Compras Acima do P75 |
| Dispersão | X = `fato_item_compra[quantidade]` (escala logarítmica), Y = `valor_unitario`, detalhe = `id_compra_item`, filtrado por um item escolhido na tabela |
| Segmentações | `dim_item[categoria]`, `dim_item[nome_classe]` |

Filtro de página: `fato_item_compra[comparavel]` = Verdadeiro.

Pergunta: para um mesmo item, quanto o preço varia e quem pagou acima do terceiro quartil?

## 6. Página 3 — Quanto dá para economizar

| Visual | Campos |
|---|---|
| 3 cartões | Economia Teto, Economia Conservadora, Economia Defensável |
| Cartão | % Economia Defensável |
| Barras (top 15 itens) | `dim_item[nome_padrao]`, Economia Defensável |
| Barras por categoria | `dim_item[categoria]`, as três economias lado a lado |
| Tabela por órgão | `dim_orgao[nome_orgao]`, Gasto Homogêneo, Economia Defensável, % Economia Defensável |
| Caixa de texto | "A estimativa defensável considera só itens de preço homogêneo. Preço acima da referência não significa irregularidade." |

Pergunta: qual o ganho possível e por onde começar?

## 7. Publicar

1. **Arquivo** → **Salvar como** → `powerbi/inteligencia-de-compra.pbix` (dentro do repositório).
2. **Publicar** → "Meu workspace".
3. No serviço (app.powerbi.com): abra o relatório → **Arquivo** → **Inserir relatório** →
   **Publicar na Web**. Se a opção não aparecer, a instituição bloqueou o recurso; nesse
   caso, exporte as três páginas como imagem para `docs/img/` e grave um vídeo curto.
4. Coloque o link (ou as imagens) no README.

## 8. Antes de considerar pronto

- [ ] Os valores da tabela "Conferência" batem, sem filtro e por categoria.
- [ ] A segmentação de categoria filtra as três páginas.
- [ ] Nenhuma tabela ou gráfico mostra CPF ou nome de pessoa física.
- [ ] Você consegue explicar cada medida sem olhar o `medidas.md`.
