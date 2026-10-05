"""As três páginas do painel, uma por pergunta de negócio.

Página de 1280 x 720, com a mesma estrutura nas três, para o leitor aprender uma vez:
cabeçalho (pergunta, escopo e o filtro de categoria), faixa de indicadores liderada pelo
número principal da página, e os visuais que detalham a resposta.
"""

import copy
from dataclasses import dataclass

from compras.painel.tema import PADRAO, TEXTO_SUAVE, Tema
from compras.painel.visuais import (
    SCHEMA_CELULAR,
    Coluna,
    Json,
    Medida,
    Posicao,
    area,
    barras,
    cartao,
    literal,
    paragrafos_de_texto,
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
Y_FAIXA = 16
ALTURA_FAIXA = 96
Y_INDICADORES = Y_FAIXA + ALTURA_FAIXA + VAO
ALTURA_INDICADORES = 104
Y_CORPO = Y_INDICADORES + ALTURA_INDICADORES + VAO
FIM = ALTURA - MARGEM

LARGURA_DESTAQUE = 304

# Layout para celular: uma coluna, com os indicadores de apoio em pares.
LARGURA_CELULAR = 320
MARGEM_CELULAR = 8
VAO_CELULAR = 8

CATEGORIA = Coluna("dim_item", "categoria")
ITEM = Coluna("dim_item", "nome_padrao")
CODIGO_ITEM = Coluna("dim_item", "codigo_item")
UNIDADE = Coluna("fato_item_compra", "unidade_medida")
UF = Coluna("fato_item_compra", "sigla_uf")
MES = Coluna("dim_tempo", "inicio_do_mes")
FORNECEDOR = Coluna("dim_fornecedor", "nome")
DOCUMENTO = Coluna("dim_fornecedor", "documento")
ORGAO = Coluna("dim_orgao", "nome_orgao")

Linha = tuple[int, tuple[str, ...]]


@dataclass(frozen=True)
class Pagina:
    nome: str
    titulo: str
    visuais: list[Json]
    # Estado de cada visual no layout para celular (posição e ajustes de formato), por nome.
    celular: dict[str, Json]


def _textos_da_faixa(t: Tema, pergunta: str, escopo: str, tamanho: int) -> Json:
    """Nome do painel, a pergunta da página e o escopo dos dados, sobre a cor de identidade."""
    e = t.escala
    return paragrafos_de_texto(
        [
            [
                (
                    "INTELIGÊNCIA DE COMPRA",
                    {
                        "fontSize": f"{e.apoio}pt",
                        "fontWeight": "bold",
                        "color": t.sobre_identidade_suave,
                    },
                )
            ],
            [
                (
                    pergunta,
                    {"fontSize": f"{tamanho}pt", "fontWeight": "bold", "color": t.sobre_identidade},
                )
            ],
            [(escopo, {"fontSize": f"{e.corpo}pt", "color": t.sobre_identidade_suave})],
        ]
    )


def _cabecalho(t: Tema, prefixo: str, pergunta: str, escopo: str) -> list[Json]:
    """Faixa na cor de identidade com a pergunta da página; sobre ela, à direita, o filtro."""
    faixa = texto(
        f"{prefixo}_faixa",
        Posicao(MARGEM, Y_FAIXA, UTIL, ALTURA_FAIXA),
        0,
        [],
        fundo=t.identidade,
        margem=(10, 20),
    )
    faixa["visual"]["objects"] = _textos_da_faixa(t, pergunta, escopo, t.escala.pergunta)
    return [
        faixa,
        segmentacao(
            f"{prefixo}_categoria",
            Posicao(LARGURA - MARGEM - 12 - 260, Y_FAIXA + 12, 260, 72),
            1,
            CATEGORIA,
            "Categoria",
            "categoria",
        ),
    ]


def _indicadores(
    t: Tema, prefixo: str, principal: tuple[str, str], apoio: list[tuple[str, str]]
) -> list[Json]:
    """Um número principal, maior e na cor de identidade, e os indicadores de apoio."""
    largura = (UTIL - LARGURA_DESTAQUE - VAO * len(apoio)) / len(apoio)
    inicio = MARGEM + LARGURA_DESTAQUE + VAO
    return [
        cartao(
            f"{prefixo}_kpi_principal",
            Posicao(MARGEM, Y_INDICADORES, LARGURA_DESTAQUE, ALTURA_INDICADORES),
            10,
            Medida(principal[0]),
            principal[1],
            destaque=t,
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


def _celular(t: Tema, visuais: list[Json], linhas: list[Linha]) -> dict[str, Json]:
    """Empilha os visuais em linhas para a tela do celular.

    Cada linha é (altura, nomes); os nomes dividem a largura em partes iguais. O celular
    herda o formato da página; aqui entram só os ajustes de tamanho de fonte que a tela
    estreita pede.
    """
    por_nome = {v["name"]: v for v in visuais}
    util = LARGURA_CELULAR - 2 * MARGEM_CELULAR
    estados: dict[str, Json] = {}
    y = MARGEM_CELULAR
    for altura, nomes in linhas:
        largura = (util - VAO_CELULAR * (len(nomes) - 1)) / len(nomes)
        for indice, nome in enumerate(nomes):
            visual = por_nome[nome]["visual"]
            estado: Json = {
                "$schema": SCHEMA_CELULAR,
                "position": {
                    "x": MARGEM_CELULAR + indice * (largura + VAO_CELULAR),
                    "y": y,
                    "z": len(estados),
                    "width": largura,
                    "height": altura,
                    "tabOrder": len(estados),
                },
            }
            if visual["visualType"] == "card" and "objects" not in visual:
                # Indicador de apoio: número menor, para o rótulo caber abaixo dele.
                estado["objects"] = {
                    "labels": [{"properties": {"fontSize": literal(t.escala.pergunta)}}],
                    "categoryLabels": [{"properties": {"fontSize": literal(t.escala.apoio)}}],
                }
            if "title" in visual["visualContainerObjects"] and visual["visualContainerObjects"][
                "title"
            ][0]["properties"].get("text"):
                # Título longo quebra em duas linhas em vez de terminar em reticências.
                estado["visualContainerObjects"] = {
                    "title": [{"properties": {"titleWrap": literal(True)}}]
                }
            if nome.endswith("_faixa"):
                # A pergunta desce um degrau para caber em uma ou duas linhas na tela estreita.
                textos = copy.deepcopy(visual["objects"])
                pergunta = textos["general"][0]["properties"]["paragraphs"][1]["textRuns"][0]
                pergunta["textStyle"]["fontSize"] = f"{t.escala.titulo + 4}pt"
                estado["objects"] = textos
            estados[nome] = estado
        y += altura + VAO_CELULAR
    return estados


def pagina_gasto(t: Tema = PADRAO) -> Pagina:
    p = "gasto"
    lateral = 384
    alto = 168
    y_baixo = Y_CORPO + alto + VAO
    visuais = [
        *_cabecalho(
            t,
            p,
            "Onde está o gasto?",
            "Compras federais de escritório, informática e limpeza · contratações de 2024 e 2025",
        ),
        *_indicadores(
            t,
            p,
            ("Gasto Total", "Gasto total"),
            [
                ("Itens Comprados", "Itens comprados"),
                ("Fornecedores", "Fornecedores"),
                ("Órgãos", "Órgãos"),
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
            "Gasto por mês do resultado",
            MES,
            Medida("Gasto Total"),
        ),
        tabela(
            f"{p}_fornecedores",
            Posicao(MARGEM, y_baixo, UTIL - lateral - VAO, FIM - y_baixo),
            22,
            "Os 8 maiores fornecedores, por CNPJ",
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
            n_maiores=(DOCUMENTO, Medida("Gasto Total"), 8),
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
    ]
    celular = _celular(
        t,
        visuais,
        [
            (116, (f"{p}_faixa",)),
            (64, (f"{p}_categoria",)),
            (104, (f"{p}_kpi_principal",)),
            (88, (f"{p}_kpi_0", f"{p}_kpi_1")),
            (88, (f"{p}_kpi_2", f"{p}_kpi_3")),
            (168, (f"{p}_por_categoria",)),
            (200, (f"{p}_por_mes",)),
            (280, (f"{p}_por_uf",)),
            (300, (f"{p}_fornecedores",)),
        ],
    )
    return Pagina("gasto", "1. Onde está o gasto", visuais, celular)


def pagina_preco(t: Tema = PADRAO) -> Pagina:
    p = "preco"
    lateral = 384
    alto = 160
    y_baixo = Y_CORPO + alto + VAO
    visuais = [
        *_cabecalho(
            t,
            p,
            "Onde se paga caro?",
            "P75 é o terceiro quartil do preço do mesmo item e unidade, com 10 ou mais compras · "
            "preços suspeitos fora",
        ),
        *_indicadores(
            t,
            p,
            ("Gasto Acima do P75", "Gasto acima do P75"),
            [
                ("Ágio Médio sobre o P75", "Ágio médio (P75)"),
                ("Compras Comparáveis", "Compras comparáveis"),
                ("Gasto Comparável", "Gasto comparável"),
                ("Itens com Preço Suspeito", "Preço suspeito"),
            ],
        ),
        tabela(
            f"{p}_itens",
            Posicao(MARGEM, Y_CORPO, UTIL - lateral - VAO, FIM - Y_CORPO),
            20,
            "Os 15 itens com maior gasto acima do P75",
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
            n_maiores=(CODIGO_ITEM, Medida("Gasto Acima do P75"), 15),
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
    ]
    celular = _celular(
        t,
        visuais,
        [
            (132, (f"{p}_faixa",)),
            (64, (f"{p}_categoria",)),
            (104, (f"{p}_kpi_principal",)),
            (88, (f"{p}_kpi_0", f"{p}_kpi_1")),
            (88, (f"{p}_kpi_2", f"{p}_kpi_3")),
            (168, (f"{p}_por_categoria",)),
            (300, (f"{p}_por_orgao",)),
            (360, (f"{p}_itens",)),
        ],
    )
    return Pagina("preco", "2. Onde se paga caro", visuais, celular)


def pagina_economia(t: Tema = PADRAO) -> Pagina:
    p = "economia"
    esquerda = 500
    direita = UTIL - esquerda - VAO
    x_direita = MARGEM + esquerda + VAO
    alto = 150
    altura_aviso = 36
    y_tabela = Y_CORPO + alto + VAO
    y_aviso = FIM - altura_aviso
    visuais = [
        *_cabecalho(
            t,
            p,
            "Quanto dá para economizar?",
            "Três estimativas, da mais otimista à mais defensável · a decisão usa a menor, "
            "que só conta itens de preço homogêneo",
        ),
        *_indicadores(
            t,
            p,
            ("Economia Defensável", "Economia defensável"),
            [
                ("% Economia Defensável", "Defensável sobre o gasto homogêneo"),
                ("Economia Conservadora", "Conservadora: acima do P75 cai para o P75"),
                ("Economia Teto", "Teto: todos pagam a mediana"),
            ],
        ),
        barras(
            f"{p}_por_item",
            Posicao(MARGEM, Y_CORPO, esquerda, y_aviso - VAO - Y_CORPO),
            20,
            "Os 15 itens com maior economia defensável",
            ITEM,
            [Medida("Economia Defensável")],
            n_maiores=15,
        ),
        texto(
            f"{p}_aviso",
            Posicao(MARGEM, y_aviso, esquerda, altura_aviso),
            23,
            [
                [
                    (
                        "Preço acima da referência não indica irregularidade: frete, "
                        "lote, prazo e marca explicam parte da diferença. A análise aponta "
                        "onde olhar.",
                        {"fontSize": f"{t.escala.apoio}pt", "color": TEXTO_SUAVE},
                    )
                ]
            ],
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
            Posicao(x_direita, y_tabela, direita, FIM - y_tabela),
            22,
            "Os 8 órgãos com maior economia defensável",
            [
                (ORGAO, "Órgão", 330),
                (Medida("Gasto Homogêneo"), "Gasto homogêneo", 124),
                (Medida("Economia Defensável"), "Economia defensável", 132),
                (Medida("% Economia Defensável"), "% do gasto", 76),
            ],
            ordenar_por=Medida("Economia Defensável"),
            n_maiores=(ORGAO, Medida("Economia Defensável"), 8),
        ),
    ]
    celular = _celular(
        t,
        visuais,
        [
            (168, (f"{p}_faixa",)),
            (64, (f"{p}_categoria",)),
            (104, (f"{p}_kpi_principal",)),
            (88, (f"{p}_kpi_0",)),
            (88, (f"{p}_kpi_1",)),
            (88, (f"{p}_kpi_2",)),
            (64, (f"{p}_aviso",)),
            (440, (f"{p}_por_item",)),
            (180, (f"{p}_por_categoria",)),
            (300, (f"{p}_por_orgao",)),
        ],
    )
    return Pagina("economia", "3. Quanto dá para economizar", visuais, celular)


def todas(t: Tema = PADRAO) -> list[Pagina]:
    return [pagina_gasto(t), pagina_preco(t), pagina_economia(t)]
