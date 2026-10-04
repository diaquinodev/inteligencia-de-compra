"""As três páginas do painel, uma por pergunta de negócio.

Página de 1280 x 720. Cada página tem a mesma estrutura: cabeçalho com título e filtro de
categoria, uma faixa de indicadores e os visuais que respondem à pergunta.
"""

from dataclasses import dataclass

from compras.painel import tema
from compras.painel.visuais import (
    Coluna,
    Json,
    Medida,
    Posicao,
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

CATEGORIA = Coluna("dim_item", "categoria")
ITEM = Coluna("dim_item", "nome_padrao")
CODIGO_ITEM = Coluna("dim_item", "codigo_item")
UNIDADE = Coluna("fato_item_compra", "unidade_medida")
UF = Coluna("fato_item_compra", "sigla_uf")
MES = Coluna("dim_tempo", "ano_mes")
FORNECEDOR = Coluna("dim_fornecedor", "nome")
DOCUMENTO = Coluna("dim_fornecedor", "documento")
ORGAO = Coluna("dim_orgao", "nome_orgao")


@dataclass(frozen=True)
class Pagina:
    nome: str
    titulo: str
    visuais: list[Json]


def _cabecalho(prefixo: str, titulo: str, subtitulo: str) -> list[Json]:
    return [
        texto(
            f"{prefixo}_titulo",
            Posicao(MARGEM, 12, 900, 68),
            0,
            [
                [(titulo, {"fontSize": "18pt", "fontWeight": "bold", "color": tema.TEXTO})],
                [(subtitulo, {"fontSize": "10pt", "color": tema.TEXTO_SUAVE})],
            ],
        ),
        segmentacao(
            f"{prefixo}_categoria",
            Posicao(LARGURA - MARGEM - 300, 16, 300, 60),
            1,
            CATEGORIA,
            "Categoria",
            "categoria",
        ),
    ]


def _indicadores(prefixo: str, medidas: list[tuple[str, str]]) -> list[Json]:
    """Faixa de cartões de mesma largura logo abaixo do cabeçalho."""
    largura = (UTIL - VAO * (len(medidas) - 1)) / len(medidas)
    return [
        cartao(
            f"{prefixo}_kpi_{indice}",
            Posicao(MARGEM + indice * (largura + VAO), 92, largura, 100),
            10 + indice,
            Medida(nome),
            rotulo,
        )
        for indice, (nome, rotulo) in enumerate(medidas)
    ]


def pagina_gasto() -> Pagina:
    p = "gasto"
    meia = 400
    return Pagina(
        "gasto",
        "1. Onde está o gasto",
        [
            *_cabecalho(
                p,
                "Onde está o gasto",
                "Compras federais de escritório, informática e limpeza · "
                "contratações de 2024 e 2025",
            ),
            *_indicadores(
                p,
                [
                    ("Gasto Total", "Gasto total"),
                    ("Itens Comprados", "Itens comprados"),
                    ("Fornecedores", "Fornecedores"),
                    ("Órgãos", "Órgãos compradores"),
                    ("HHI", "Concentração (HHI)"),
                ],
            ),
            barras(
                f"{p}_por_categoria",
                Posicao(MARGEM, 208, meia, 212),
                20,
                "Gasto por categoria",
                CATEGORIA,
                [Medida("Gasto Total")],
            ),
            barras(
                f"{p}_por_mes",
                Posicao(MARGEM + meia + VAO, 208, UTIL - meia - VAO, 212),
                21,
                "Gasto por mês do resultado",
                MES,
                [Medida("Gasto Total")],
                horizontal=False,
                ordenar_por=MES,
                decrescente=False,
                rotulos=False,
            ),
            tabela(
                f"{p}_fornecedores",
                Posicao(MARGEM, 436, UTIL - meia - VAO, 268),
                22,
                "15 maiores fornecedores (por CNPJ)",
                [
                    (Medida("Posição do Fornecedor"), "Posição", 56),
                    (FORNECEDOR, "Fornecedor", 268),
                    (DOCUMENTO, "CNPJ", 112),
                    (Medida("Gasto Total"), "Gasto", 116),
                    (Medida("Participação no Gasto"), "Participação", 84),
                    (Medida("Participação Acumulada"), "Acumulada", 80),
                    (Medida("Classe ABC"), "Classe", 52),
                ],
                ordenar_por=Medida("Gasto Total"),
                n_maiores=(DOCUMENTO, Medida("Gasto Total"), 15),
            ),
            barras(
                f"{p}_por_uf",
                Posicao(LARGURA - MARGEM - meia, 436, meia, 268),
                23,
                "10 UFs com maior gasto",
                UF,
                [Medida("Gasto Total")],
                n_maiores=10,
            ),
        ],
    )


def pagina_preco() -> Pagina:
    p = "preco"
    meia = 384
    return Pagina(
        "preco",
        "2. Onde se paga caro",
        [
            *_cabecalho(
                p,
                "Onde se paga caro",
                "Mesmo item, mesma unidade de medida, 10 ou mais compras · preços suspeitos fora",
            ),
            *_indicadores(
                p,
                [
                    ("Compras Comparáveis", "Compras comparáveis"),
                    ("Gasto Comparável", "Gasto comparável"),
                    ("Gasto Acima do P75", "Gasto em compras acima do P75"),
                    ("Ágio Médio sobre o P75", "Ágio médio sobre o P75"),
                    ("Itens com Preço Suspeito", "Compras com preço suspeito"),
                ],
            ),
            tabela(
                f"{p}_itens",
                Posicao(MARGEM, 208, UTIL - meia - VAO, 496),
                20,
                "20 itens com maior gasto acima do P75",
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
                Posicao(LARGURA - MARGEM - meia, 208, meia, 200),
                21,
                "Gasto acima do P75, por categoria",
                CATEGORIA,
                [Medida("Gasto Acima do P75")],
                cor_das_barras=tema.AMBAR,
            ),
            barras(
                f"{p}_por_orgao",
                Posicao(LARGURA - MARGEM - meia, 424, meia, 280),
                22,
                "10 órgãos com maior gasto acima do P75",
                ORGAO,
                [Medida("Gasto Acima do P75")],
                n_maiores=10,
                cor_das_barras=tema.AMBAR,
            ),
        ],
    )


def pagina_economia() -> Pagina:
    p = "economia"
    meia = 520
    return Pagina(
        "economia",
        "3. Quanto dá para economizar",
        [
            *_cabecalho(
                p,
                "Quanto dá para economizar",
                "Três estimativas: do teto à defensável · a decisão usa a menor",
            ),
            *_indicadores(
                p,
                [
                    ("Economia Teto", "Teto: todos pagam a mediana"),
                    ("Economia Conservadora", "Conservadora: acima do P75 cai para o P75"),
                    ("Economia Defensável", "Defensável: só itens de preço homogêneo"),
                    ("% Economia Defensável", "Defensável sobre o gasto homogêneo"),
                ],
            ),
            barras(
                f"{p}_por_item",
                Posicao(MARGEM, 208, meia, 496),
                20,
                "15 itens com maior economia defensável",
                ITEM,
                [Medida("Economia Defensável")],
                n_maiores=15,
                cor_das_barras=tema.VERDE,
            ),
            barras(
                f"{p}_por_categoria",
                Posicao(MARGEM + meia + VAO, 208, UTIL - meia - VAO, 200),
                21,
                "As três estimativas, por categoria",
                CATEGORIA,
                [
                    Medida("Economia Teto"),
                    Medida("Economia Conservadora"),
                    Medida("Economia Defensável"),
                ],
                horizontal=False,
            ),
            tabela(
                f"{p}_por_orgao",
                Posicao(MARGEM + meia + VAO, 424, UTIL - meia - VAO, 216),
                22,
                "12 órgãos com maior economia defensável",
                [
                    (ORGAO, "Órgão", 316),
                    (Medida("Gasto Homogêneo"), "Gasto homogêneo", 124),
                    (Medida("Economia Defensável"), "Economia defensável", 132),
                    (Medida("% Economia Defensável"), "% do gasto", 76),
                ],
                ordenar_por=Medida("Economia Defensável"),
                n_maiores=(ORGAO, Medida("Economia Defensável"), 12),
            ),
            texto(
                f"{p}_aviso",
                Posicao(MARGEM + meia + VAO, 648, UTIL - meia - VAO, 56),
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
