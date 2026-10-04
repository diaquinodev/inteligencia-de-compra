"""As três páginas do painel, uma por pergunta de negócio.

Página de 1280 x 720, com a mesma estrutura nas três, para o leitor aprender uma vez:
cabeçalho (pergunta, escopo e o filtro de categoria), faixa de indicadores liderada pelo
número principal da página, e os visuais que detalham a resposta.
"""

from dataclasses import dataclass

from compras.painel import tema
from compras.painel.visuais import (
    Coluna,
    Json,
    Medida,
    Posicao,
    area,
    barras,
    cartao,
    segmentacao,
    tabela,
    texto,
)

LARGURA = 1280
ALTURA = 720
MARGEM = 24
VAO = 16
UTIL = LARGURA - 2 * MARGEM

# Faixas verticais comuns às três páginas.
Y_CABECALHO = 12
ALTURA_CABECALHO = 80
Y_INDICADORES = 100
ALTURA_INDICADORES = 96
Y_CORPO = Y_INDICADORES + ALTURA_INDICADORES + VAO
FIM = ALTURA - MARGEM

LARGURA_DESTAQUE = 304

CATEGORIA = Coluna("dim_item", "categoria")
ITEM = Coluna("dim_item", "nome_padrao")
CODIGO_ITEM = Coluna("dim_item", "codigo_item")
UNIDADE = Coluna("fato_item_compra", "unidade_medida")
UF = Coluna("fato_item_compra", "sigla_uf")
MES = Coluna("dim_tempo", "inicio_do_mes")
FORNECEDOR = Coluna("dim_fornecedor", "nome")
DOCUMENTO = Coluna("dim_fornecedor", "documento")
ORGAO = Coluna("dim_orgao", "nome_orgao")


@dataclass(frozen=True)
class Pagina:
    nome: str
    titulo: str
    visuais: list[Json]


def _cabecalho(prefixo: str, pergunta: str, escopo: str) -> list[Json]:
    """Nome do painel, a pergunta da página e o escopo dos dados; à direita, o filtro."""
    return [
        texto(
            f"{prefixo}_titulo",
            Posicao(MARGEM, Y_CABECALHO, 900, ALTURA_CABECALHO),
            0,
            [
                [
                    (
                        "INTELIGÊNCIA DE COMPRA",
                        {"fontSize": "8pt", "fontWeight": "bold", "color": tema.TEXTO_APAGADO},
                    )
                ],
                [(pergunta, {"fontSize": "18pt", "fontWeight": "bold", "color": tema.TEXTO})],
                [(escopo, {"fontSize": "10pt", "color": tema.TEXTO_SUAVE})],
            ],
        ),
        segmentacao(
            f"{prefixo}_categoria",
            Posicao(LARGURA - MARGEM - 280, 16, 280, 72),
            1,
            CATEGORIA,
            "Categoria",
            "categoria",
        ),
    ]


def _indicadores(
    prefixo: str, principal: tuple[str, str], apoio: list[tuple[str, str]]
) -> list[Json]:
    """Um número principal, maior, e os indicadores de apoio em cartões iguais."""
    largura = (UTIL - LARGURA_DESTAQUE - VAO * len(apoio)) / len(apoio)
    inicio = MARGEM + LARGURA_DESTAQUE + VAO
    return [
        cartao(
            f"{prefixo}_kpi_principal",
            Posicao(MARGEM, Y_INDICADORES, LARGURA_DESTAQUE, ALTURA_INDICADORES),
            10,
            Medida(principal[0]),
            principal[1],
            destaque=True,
        ),
        *[
            cartao(
                f"{prefixo}_kpi_{indice}",
                Posicao(
                    inicio + indice * (largura + VAO), Y_INDICADORES, largura, ALTURA_INDICADORES
                ),
                11 + indice,
                Medida(nome),
                rotulo,
            )
            for indice, (nome, rotulo) in enumerate(apoio)
        ],
    ]


def pagina_gasto() -> Pagina:
    p = "gasto"
    lateral = 384
    alto = 196
    y_baixo = Y_CORPO + alto + VAO
    return Pagina(
        "gasto",
        "1. Onde está o gasto",
        [
            *_cabecalho(
                p,
                "Onde está o gasto?",
                "Compras federais de escritório, informática e limpeza · "
                "contratações de 2024 e 2025",
            ),
            *_indicadores(
                p,
                ("Gasto Total", "Gasto total"),
                [
                    ("Itens Comprados", "Itens comprados"),
                    ("Fornecedores", "Fornecedores"),
                    ("Órgãos", "Órgãos compradores"),
                    ("HHI", "Concentração (HHI)"),
                ],
            ),
            barras(
                f"{p}_por_categoria",
                Posicao(MARGEM, Y_CORPO, lateral, alto),
                20,
                "Gasto por categoria",
                CATEGORIA,
                [Medida("Gasto Total")],
            ),
            area(
                f"{p}_por_mes",
                Posicao(MARGEM + lateral + VAO, Y_CORPO, UTIL - lateral - VAO, alto),
                21,
                "Gasto por mês do resultado da compra",
                MES,
                Medida("Gasto Total"),
            ),
            tabela(
                f"{p}_fornecedores",
                Posicao(MARGEM, y_baixo, UTIL - lateral - VAO, FIM - y_baixo),
                22,
                "Os 10 maiores fornecedores, por CNPJ",
                [
                    (Medida("Posição do Fornecedor"), "#", 36),
                    (FORNECEDOR, "Fornecedor", 280),
                    (DOCUMENTO, "CNPJ", 112),
                    (Medida("Gasto Total"), "Gasto", 116),
                    (Medida("Participação no Gasto"), "Participação", 84),
                    (Medida("Participação Acumulada"), "Acumulada", 80),
                    (Medida("Classe ABC"), "Classe", 52),
                ],
                ordenar_por=Medida("Gasto Total"),
                n_maiores=(DOCUMENTO, Medida("Gasto Total"), 10),
            ),
            barras(
                f"{p}_por_uf",
                Posicao(LARGURA - MARGEM - lateral, y_baixo, lateral, FIM - y_baixo),
                23,
                "As 8 UFs com maior gasto",
                UF,
                [Medida("Gasto Total")],
                n_maiores=8,
            ),
        ],
    )


def pagina_preco() -> Pagina:
    p = "preco"
    lateral = 384
    alto = 176
    y_baixo = Y_CORPO + alto + VAO
    return Pagina(
        "preco",
        "2. Onde se paga caro",
        [
            *_cabecalho(
                p,
                "Onde se paga caro?",
                "Comparação dentro do mesmo item e da mesma unidade, com 10 ou mais compras · "
                "preços suspeitos fora",
            ),
            *_indicadores(
                p,
                ("Gasto Acima do P75", "Gasto em compras acima do terceiro quartil (P75)"),
                [
                    ("Ágio Médio sobre o P75", "Ágio médio sobre o P75"),
                    ("Compras Comparáveis", "Compras comparáveis"),
                    ("Gasto Comparável", "Gasto comparável"),
                    ("Itens com Preço Suspeito", "Compras com preço suspeito"),
                ],
            ),
            tabela(
                f"{p}_itens",
                Posicao(MARGEM, Y_CORPO, UTIL - lateral - VAO, FIM - Y_CORPO),
                20,
                "Os 20 itens com maior gasto acima do P75",
                [
                    (ITEM, "Item", 164),
                    (CODIGO_ITEM, "Código", 56),
                    (UNIDADE, "Unidade", 72),
                    (Medida("Compras Comparáveis"), "Compras", 60),
                    (Medida("Preço P25"), "P25", 88),
                    (Medida("Preço Mediano"), "Mediana", 88),
                    (Medida("Preço P75"), "P75", 88),
                    (Medida("Dispersão de Preço"), "P75 ÷ P25", 68),
                    (Medida("Gasto Acima do P75"), "Acima do P75", 108),
                ],
                ordenar_por=Medida("Gasto Acima do P75"),
                n_maiores=(CODIGO_ITEM, Medida("Gasto Acima do P75"), 20),
            ),
            barras(
                f"{p}_por_categoria",
                Posicao(LARGURA - MARGEM - lateral, Y_CORPO, lateral, alto),
                21,
                "Gasto acima do P75, por categoria",
                CATEGORIA,
                [Medida("Gasto Acima do P75")],
            ),
            barras(
                f"{p}_por_orgao",
                Posicao(LARGURA - MARGEM - lateral, y_baixo, lateral, FIM - y_baixo),
                22,
                "Os 8 órgãos com maior gasto acima do P75",
                ORGAO,
                [Medida("Gasto Acima do P75")],
                n_maiores=8,
            ),
        ],
    )


def pagina_economia() -> Pagina:
    p = "economia"
    esquerda = 500
    direita = UTIL - esquerda - VAO
    x_direita = MARGEM + esquerda + VAO
    alto = 172
    altura_aviso = 36
    y_tabela = Y_CORPO + alto + VAO
    y_aviso = FIM - altura_aviso
    return Pagina(
        "economia",
        "3. Quanto dá para economizar",
        [
            *_cabecalho(
                p,
                "Quanto dá para economizar?",
                "Três estimativas, da mais otimista à mais defensável · a decisão usa a menor",
            ),
            *_indicadores(
                p,
                ("Economia Defensável", "Economia defensável: só itens de preço homogêneo"),
                [
                    ("% Economia Defensável", "Defensável sobre o gasto homogêneo"),
                    ("Economia Conservadora", "Conservadora: acima do P75 cai para o P75"),
                    ("Economia Teto", "Teto: todos pagam a mediana"),
                ],
            ),
            barras(
                f"{p}_por_item",
                Posicao(MARGEM, Y_CORPO, esquerda, FIM - Y_CORPO),
                20,
                "Os 15 itens com maior economia defensável",
                ITEM,
                [Medida("Economia Defensável")],
                n_maiores=15,
            ),
            tabela(
                f"{p}_por_categoria",
                Posicao(x_direita, Y_CORPO, direita, alto),
                21,
                "As três estimativas, por categoria",
                [
                    (CATEGORIA, "Categoria", 120),
                    (Medida("Economia Teto"), "Teto", 140),
                    (Medida("Economia Conservadora"), "Conservadora", 140),
                    (Medida("Economia Defensável"), "Defensável", 140),
                    (Medida("% Economia Defensável"), "% do gasto", 100),
                ],
                ordenar_por=Medida("Economia Defensável"),
            ),
            tabela(
                f"{p}_por_orgao",
                Posicao(x_direita, y_tabela, direita, y_aviso - VAO - y_tabela),
                22,
                "Os 10 órgãos com maior economia defensável",
                [
                    (ORGAO, "Órgão", 330),
                    (Medida("Gasto Homogêneo"), "Gasto homogêneo", 124),
                    (Medida("Economia Defensável"), "Economia defensável", 132),
                    (Medida("% Economia Defensável"), "% do gasto", 76),
                ],
                ordenar_por=Medida("Economia Defensável"),
                n_maiores=(ORGAO, Medida("Economia Defensável"), 10),
            ),
            texto(
                f"{p}_aviso",
                Posicao(x_direita, y_aviso, direita, altura_aviso),
                23,
                [
                    [
                        (
                            "Preço acima da referência não indica irregularidade: frete, "
                            "lote, prazo e marca explicam parte da diferença. A análise aponta "
                            "onde olhar.",
                            {"fontSize": "9pt", "color": tema.TEXTO_SUAVE},
                        )
                    ]
                ],
            ),
        ],
    )


def todas() -> list[Pagina]:
    return [pagina_gasto(), pagina_preco(), pagina_economia()]
