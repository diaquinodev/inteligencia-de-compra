"""Temas do painel: um por área de negócio, com cores, escala de tamanhos e estilo dos visuais.

O tema é o recurso nativo do Power BI para personalizar um relatório (cores de dados,
classes de texto e estilo por tipo de visual). Aqui ele é gerado a partir de três decisões
por área, e o resto é derivado:

- `identidade`: a cor da área. Vai na faixa do cabeçalho e no número principal, com texto
  branco. Dá personalidade à página sem tocar nos gráficos.
- `dado`: a cor das barras, linhas e áreas. Uma série, uma cor.
- os neutros (fundo, borda, grade) recebem uma fração da cor de identidade.

Princípios e validação das cores em powerbi/DESIGN.md.
"""

from dataclasses import dataclass
from typing import Any

NOME = "InteligenciaDeCompra"

FONTE = "Segoe UI"
FONTE_FORTE = "Segoe UI Semibold"

FUNDO_CARTAO = "#FDFDFC"
BRANCO = "#FFFFFF"
TEXTO = "#111417"
TEXTO_SUAVE = "#52514E"
TEXTO_APAGADO = "#85837D"


@dataclass(frozen=True)
class Escala:
    """Tamanhos de fonte, em pontos, do nível mais alto da hierarquia ao mais baixo."""

    destaque: int = 44
    indicador: int = 26
    pergunta: int = 20
    titulo: int = 12
    corpo: int = 10
    apoio: int = 9

    def niveis(self) -> list[int]:
        return [self.destaque, self.indicador, self.pergunta, self.titulo, self.corpo, self.apoio]


def _canais(hexadecimal: str) -> tuple[int, int, int]:
    h = hexadecimal.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def misturar(base: str, outra: str, fracao: float) -> str:
    """Cor entre `base` e `outra`; `fracao` é quanto de `outra` entra (0 a 1)."""
    return "#" + "".join(
        f"{round(a + (b - a) * fracao):02X}"
        for a, b in zip(_canais(base), _canais(outra), strict=True)
    )


def contraste(cor_a: str, cor_b: str) -> float:
    """Razão de contraste da WCAG entre duas cores (1 a 21)."""

    def luminancia(hexadecimal: str) -> float:
        linear = [
            c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
            for c in (canal / 255 for canal in _canais(hexadecimal))
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    clara, escura = sorted((luminancia(cor_a), luminancia(cor_b)), reverse=True)
    return (clara + 0.05) / (escura + 0.05)


@dataclass(frozen=True)
class Tema:
    chave: str
    area: str
    identidade: str
    dado: str
    escala: Escala = Escala()

    @property
    def sobre_identidade(self) -> str:
        """Texto principal sobre a cor de identidade."""
        return BRANCO

    @property
    def sobre_identidade_suave(self) -> str:
        """Texto secundário sobre a cor de identidade."""
        return misturar(self.identidade, BRANCO, 0.82)

    @property
    def fundo_pagina(self) -> str:
        return misturar("#F5F5F3", self.identidade, 0.05)

    @property
    def borda(self) -> str:
        return misturar("#E4E3DE", self.identidade, 0.10)

    @property
    def grade(self) -> str:
        return misturar("#E6E5E0", self.identidade, 0.08)


# A cor de dado de cada área passou no validador de paleta contra a superfície do cartão
# (faixa de luminosidade, saturação mínima e contraste de 3:1). Ver powerbi/DESIGN.md.
TEMAS: dict[str, Tema] = {
    t.chave: t
    for t in (
        Tema("compras", "Compras e suprimentos", "#0B3F4C", "#0E8FA8"),
        Tema("financeiro", "Financeiro e controladoria", "#14305E", "#2A78D6"),
        Tema("vendas", "Vendas e comercial", "#3F1D6B", "#7C4DDB"),
        Tema("pessoas", "Pessoas (RH)", "#6B1D43", "#C2477F"),
        Tema("operacoes", "Operações e logística", "#263238", "#2F8FC4"),
    )
}
PADRAO = TEMAS["compras"]


def _cor(hexadecimal: str) -> dict[str, Any]:
    return {"solid": {"color": hexadecimal}}


def _eixos(t: Tema) -> dict[str, Any]:
    """Eixos e grade comuns aos gráficos de barras, colunas e área."""
    e = t.escala
    return {
        "categoryAxis": [
            {
                "showAxisTitle": False,
                "labelColor": _cor(TEXTO_SUAVE),
                "fontSize": e.apoio,
                "fontFamily": FONTE,
                "innerPadding": 45,
                # Até 40% da largura para os nomes: órgãos e itens têm nomes longos.
                "maxMarginFactor": 40,
            }
        ],
        "valueAxis": [
            {
                "showAxisTitle": False,
                "labelColor": _cor(TEXTO_APAGADO),
                "fontSize": e.apoio,
                "fontFamily": FONTE,
                "gridlineShow": True,
                "gridlineColor": _cor(t.grade),
                "gridlineStyle": "solid",
                "gridlineThickness": 1,
            }
        ],
        # Rótulo sempre fora da barra: dentro, o texto escuro some sobre a cor.
        "labels": [
            {
                "color": _cor(TEXTO_SUAVE),
                "fontSize": e.apoio,
                "fontFamily": FONTE,
                "labelPosition": "OutsideEnd",
            }
        ],
        "legend": [
            {
                "position": "Top",
                "showTitle": False,
                "labelColor": _cor(TEXTO_SUAVE),
                "fontSize": e.apoio,
                "fontFamily": FONTE,
            }
        ],
    }


def definicao(t: Tema = PADRAO) -> dict[str, Any]:
    """Tema no formato JSON de temas do Power BI."""
    e = t.escala
    return {
        "name": NOME,
        "dataColors": [t.dado],
        "background": FUNDO_CARTAO,
        "foreground": TEXTO,
        "tableAccent": t.identidade,
        "textClasses": {
            "callout": {"fontFace": FONTE_FORTE, "fontSize": e.indicador, "color": TEXTO},
            "title": {"fontFace": FONTE_FORTE, "fontSize": e.titulo, "color": TEXTO},
            "header": {"fontFace": FONTE_FORTE, "fontSize": e.apoio, "color": TEXTO_SUAVE},
            "label": {"fontFace": FONTE, "fontSize": e.apoio, "color": TEXTO_SUAVE},
        },
        "visualStyles": {
            "*": {
                "*": {
                    "background": [{"show": True, "color": _cor(FUNDO_CARTAO), "transparency": 0}],
                    "border": [{"show": True, "color": _cor(t.borda), "radius": 10}],
                    "dropShadow": [{"show": False}],
                    "title": [
                        {
                            "fontFamily": FONTE_FORTE,
                            "fontSize": e.titulo,
                            "fontColor": _cor(TEXTO),
                        }
                    ],
                    "padding": [{"top": 10, "bottom": 10, "left": 14, "right": 14}],
                }
            },
            "page": {
                "*": {
                    "background": [{"color": _cor(t.fundo_pagina), "transparency": 0}],
                    "outspace": [{"color": _cor(t.fundo_pagina), "transparency": 0}],
                }
            },
            "card": {
                "*": {
                    "labels": [
                        {"fontSize": e.indicador, "fontFamily": FONTE_FORTE, "color": _cor(TEXTO)}
                    ],
                    "categoryLabels": [
                        {
                            "show": True,
                            "fontSize": e.corpo,
                            "fontFamily": FONTE,
                            "color": _cor(TEXTO_SUAVE),
                        }
                    ],
                }
            },
            "clusteredBarChart": {"*": _eixos(t)},
            "clusteredColumnChart": {"*": _eixos(t)},
            "areaChart": {"*": _eixos(t)},
            "tableEx": {
                "*": {
                    "grid": [
                        {
                            "gridVertical": False,
                            "gridHorizontal": True,
                            "gridHorizontalColor": _cor(t.grade),
                            "gridHorizontalWeight": 1,
                            "rowPadding": 3,
                            "outlineColor": _cor(t.identidade),
                        }
                    ],
                    "columnHeaders": [
                        {
                            "fontFamily": FONTE_FORTE,
                            "fontSize": e.apoio,
                            "fontColor": _cor(t.identidade),
                            "backColor": _cor(FUNDO_CARTAO),
                        }
                    ],
                    "values": [
                        {
                            "fontSize": e.apoio,
                            "fontColorPrimary": _cor(TEXTO),
                            "fontColorSecondary": _cor(TEXTO),
                            "backColorPrimary": _cor(FUNDO_CARTAO),
                            "backColorSecondary": _cor(FUNDO_CARTAO),
                        }
                    ],
                    "total": [{"totals": False}],
                }
            },
            "slicer": {
                "*": {
                    "header": [
                        {
                            "fontFamily": FONTE_FORTE,
                            "textSize": e.apoio,
                            "fontColor": _cor(TEXTO_SUAVE),
                        }
                    ],
                    "items": [{"fontFamily": FONTE, "textSize": e.corpo, "fontColor": _cor(TEXTO)}],
                }
            },
        },
    }
