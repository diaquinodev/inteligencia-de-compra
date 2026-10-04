"""Tema do painel: cores, fontes e o estilo comum de todos os visuais.

Princípios (detalhados em powerbi/DESIGN.md):
- a cor carrega dado, não decoração: uma série, uma cor; texto nunca usa a cor da série;
- grade e eixos são discretos; quem aparece é o dado.
As cores foram conferidas com um validador de contraste e de daltonismo antes de entrar aqui.
"""

from typing import Any

NOME = "InteligenciaDeCompra"

# Superfícies e tinta
FUNDO_PAGINA = "#F4F4F1"
FUNDO_CARTAO = "#FCFCFB"
BORDA = "#E4E3DE"
GRADE = "#E1E0D9"
TEXTO = "#0B0B0B"
TEXTO_SUAVE = "#52514E"
TEXTO_APAGADO = "#898781"

# Dado. O painel só tem gráficos de uma série; todos usam a mesma cor.
AZUL = "#2A78D6"

FONTE = "Segoe UI"
FONTE_FORTE = "Segoe UI Semibold"


def _cor(hexadecimal: str) -> dict[str, Any]:
    return {"solid": {"color": hexadecimal}}


def _eixos() -> dict[str, Any]:
    """Eixos e grade comuns aos gráficos de barras, colunas e área."""
    return {
        "categoryAxis": [
            {
                "showAxisTitle": False,
                "labelColor": _cor(TEXTO_SUAVE),
                "fontSize": 9,
                "fontFamily": FONTE,
                "innerPadding": 45,
            }
        ],
        "valueAxis": [
            {
                "showAxisTitle": False,
                "labelColor": _cor(TEXTO_APAGADO),
                "fontSize": 9,
                "fontFamily": FONTE,
                "gridlineShow": True,
                "gridlineColor": _cor(GRADE),
                "gridlineStyle": "solid",
                "gridlineThickness": 1,
            }
        ],
        # Rótulo sempre fora da barra: dentro, o texto escuro some sobre o azul.
        "labels": [
            {
                "color": _cor(TEXTO_SUAVE),
                "fontSize": 9,
                "fontFamily": FONTE,
                "labelPosition": "OutsideEnd",
            }
        ],
        "legend": [
            {
                "position": "Top",
                "showTitle": False,
                "labelColor": _cor(TEXTO_SUAVE),
                "fontSize": 9,
                "fontFamily": FONTE,
            }
        ],
    }


def definicao() -> dict[str, Any]:
    """Tema no formato JSON de temas do Power BI."""
    return {
        "name": NOME,
        "dataColors": [AZUL],
        "background": FUNDO_CARTAO,
        "foreground": TEXTO,
        "tableAccent": GRADE,
        "textClasses": {
            "callout": {"fontFace": FONTE_FORTE, "fontSize": 24, "color": TEXTO},
            "title": {"fontFace": FONTE_FORTE, "fontSize": 11, "color": TEXTO},
            "header": {"fontFace": FONTE_FORTE, "fontSize": 9, "color": TEXTO_SUAVE},
            "label": {"fontFace": FONTE, "fontSize": 9, "color": TEXTO_SUAVE},
        },
        "visualStyles": {
            "*": {
                "*": {
                    "background": [{"show": True, "color": _cor(FUNDO_CARTAO), "transparency": 0}],
                    "border": [{"show": True, "color": _cor(BORDA), "radius": 10}],
                    "dropShadow": [{"show": False}],
                    "title": [
                        {
                            "fontFamily": FONTE_FORTE,
                            "fontSize": 11,
                            "fontColor": _cor(TEXTO),
                        }
                    ],
                    "padding": [{"top": 10, "bottom": 10, "left": 14, "right": 14}],
                }
            },
            "page": {
                "*": {
                    "background": [{"color": _cor(FUNDO_PAGINA), "transparency": 0}],
                    "outspace": [{"color": _cor(FUNDO_PAGINA), "transparency": 0}],
                }
            },
            "card": {
                "*": {
                    "labels": [{"fontSize": 22, "fontFamily": FONTE_FORTE, "color": _cor(TEXTO)}],
                    "categoryLabels": [
                        {
                            "show": True,
                            "fontSize": 9,
                            "fontFamily": FONTE,
                            "color": _cor(TEXTO_SUAVE),
                        }
                    ],
                }
            },
            "clusteredBarChart": {"*": _eixos()},
            "clusteredColumnChart": {"*": _eixos()},
            "areaChart": {"*": _eixos()},
            "tableEx": {
                "*": {
                    "grid": [
                        {
                            "gridVertical": False,
                            "gridHorizontal": True,
                            "gridHorizontalColor": _cor(GRADE),
                            "gridHorizontalWeight": 1,
                            "rowPadding": 5,
                            "outlineColor": _cor(GRADE),
                        }
                    ],
                    "columnHeaders": [
                        {
                            "fontFamily": FONTE_FORTE,
                            "fontSize": 9,
                            "fontColor": _cor(TEXTO_SUAVE),
                            "backColor": _cor(FUNDO_CARTAO),
                        }
                    ],
                    "values": [
                        {
                            "fontSize": 9,
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
                        {"fontFamily": FONTE_FORTE, "textSize": 9, "fontColor": _cor(TEXTO_SUAVE)}
                    ],
                    "items": [{"fontFamily": FONTE, "textSize": 10, "fontColor": _cor(TEXTO)}],
                }
            },
        },
    }
