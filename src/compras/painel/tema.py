"""Tema do painel: cores, fontes e o estilo comum de todos os visuais."""

from typing import Any

NOME = "InteligenciaDeCompra"

FUNDO_PAGINA = "#F3F4F6"
FUNDO_CARTAO = "#FFFFFF"
BORDA = "#E5E7EB"
TEXTO = "#111827"
TEXTO_SUAVE = "#6B7280"
AZUL = "#1D4ED8"
VERDE = "#15803D"
AMBAR = "#B45309"
CINZA = "#9CA3AF"

FONTE = "Segoe UI"
FONTE_FORTE = "Segoe UI Semibold"


def _cor(hexadecimal: str) -> dict[str, Any]:
    return {"solid": {"color": hexadecimal}}


def definicao() -> dict[str, Any]:
    """Tema no formato JSON de temas do Power BI."""
    return {
        "name": NOME,
        "dataColors": [AZUL, VERDE, AMBAR, "#7C3AED", "#0E7490", "#BE123C", CINZA, "#4D7C0F"],
        "background": FUNDO_CARTAO,
        "foreground": TEXTO,
        "tableAccent": AZUL,
        "textClasses": {
            "callout": {"fontFace": FONTE_FORTE, "fontSize": 26, "color": TEXTO},
            "title": {"fontFace": FONTE_FORTE, "fontSize": 11, "color": TEXTO},
            "header": {"fontFace": FONTE_FORTE, "fontSize": 10, "color": TEXTO},
            "label": {"fontFace": FONTE, "fontSize": 9, "color": TEXTO_SUAVE},
        },
        "visualStyles": {
            "*": {
                "*": {
                    "background": [{"show": True, "color": _cor(FUNDO_CARTAO), "transparency": 0}],
                    "border": [{"show": True, "color": _cor(BORDA), "radius": 8}],
                    "dropShadow": [{"show": False}],
                    "title": [
                        {
                            "fontFamily": FONTE_FORTE,
                            "fontSize": 11,
                            "fontColor": _cor(TEXTO),
                        }
                    ],
                    "padding": [{"top": 8, "bottom": 8, "left": 12, "right": 12}],
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
                    "labels": [{"fontSize": 24, "fontFamily": FONTE_FORTE, "color": _cor(TEXTO)}],
                    "categoryLabels": [
                        {
                            "show": True,
                            "fontSize": 10,
                            "fontFamily": FONTE,
                            "color": _cor(TEXTO_SUAVE),
                        }
                    ],
                }
            },
            "tableEx": {
                "*": {
                    "grid": [{"gridVertical": False, "rowPadding": 4}],
                    "columnHeaders": [{"fontFamily": FONTE_FORTE, "fontSize": 9}],
                    "values": [{"fontSize": 9}],
                    "total": [{"totals": False}],
                }
            },
        },
    }
