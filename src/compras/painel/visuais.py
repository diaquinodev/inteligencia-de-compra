"""Construtores dos visuais no formato PBIR (um `visual.json` por visual).

Cada função devolve o dicionário de um visual. Estilo comum (fundo, borda, fontes) vem do
tema; aqui fica só o que é próprio de cada visual: campos, título, posição e ordenação.
"""

from dataclasses import dataclass
from typing import Any

from compras.painel.medidas import TABELA
from compras.painel.tema import Tema

SCHEMA_BASE = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
SCHEMA_VISUAL = f"{SCHEMA_BASE}/visualContainer/2.0.0/schema.json"
SCHEMA_CELULAR = f"{SCHEMA_BASE}/visualContainerMobileState/2.0.0/schema.json"

Json = dict[str, Any]


@dataclass(frozen=True)
class Coluna:
    tabela: str
    nome: str

    @property
    def ref(self) -> str:
        return f"{self.tabela}.{self.nome}"

    def expressao(self, fonte: str | None = None) -> Json:
        origem = {"Source": fonte} if fonte else {"Entity": self.tabela}
        return {"Column": {"Expression": {"SourceRef": origem}, "Property": self.nome}}


@dataclass(frozen=True)
class Medida:
    nome: str
    tabela: str = TABELA

    @property
    def ref(self) -> str:
        return f"{self.tabela}.{self.nome}"

    def expressao(self, fonte: str | None = None) -> Json:
        origem = {"Source": fonte} if fonte else {"Entity": self.tabela}
        return {"Measure": {"Expression": {"SourceRef": origem}, "Property": self.nome}}


Campo = Coluna | Medida


@dataclass(frozen=True)
class Posicao:
    x: float
    y: float
    largura: float
    altura: float


def literal(valor: bool | int | float | str) -> Json:
    """Valor constante na notação do Power BI: 'texto', 12D, true."""
    if isinstance(valor, bool):
        texto = "true" if valor else "false"
    elif isinstance(valor, int | float):
        texto = f"{valor}D"
    else:
        texto = "'" + valor.replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": texto}}}


def cor(hexadecimal: str) -> Json:
    return {"solid": {"color": literal(hexadecimal)}}


def _projecao(campo: Campo, rotulo: str | None = None) -> Json:
    projecao: Json = {"field": campo.expressao(), "queryRef": campo.ref}
    if rotulo:
        projecao["displayName"] = rotulo
    return projecao


def _papel(*campos: Campo | tuple[Campo, str]) -> Json:
    projecoes = []
    for campo in campos:
        if isinstance(campo, tuple):
            projecoes.append(_projecao(campo[0], campo[1]))
        else:
            projecoes.append(_projecao(campo))
    return {"projections": projecoes}


def _ordenar(campo: Campo, decrescente: bool = True) -> Json:
    direcao = "Descending" if decrescente else "Ascending"
    return {"sort": [{"field": campo.expressao(), "direction": direcao}], "isDefaultSort": False}


def _titulo(texto: str) -> Json:
    return {"title": [{"properties": {"show": literal(True), "text": literal(texto)}}]}


def _sem_titulo() -> Json:
    return {"title": [{"properties": {"show": literal(False)}}]}


def _fundo(hexadecimal: str) -> Json:
    """Fundo e borda do visual numa cor só (a borda mantém o canto arredondado do tema)."""
    return {
        "background": [{"properties": {"show": literal(True), "color": cor(hexadecimal)}}],
        "border": [{"properties": {"show": literal(True), "color": cor(hexadecimal)}}],
    }


def _visual(
    nome: str, posicao: Posicao, ordem: int, corpo: Json, filtros: list[Json] | None = None
) -> Json:
    visual: Json = {
        "$schema": SCHEMA_VISUAL,
        "name": nome,
        "position": {
            "x": posicao.x,
            "y": posicao.y,
            "z": ordem,
            "height": posicao.altura,
            "width": posicao.largura,
            "tabOrder": ordem,
        },
        "visual": corpo | {"drillFilterOtherVisuals": True},
    }
    if filtros:
        visual["filterConfig"] = {"filters": filtros}
    return visual


def filtro_n_maiores(nome: str, coluna: Coluna, por: Medida, quantidade: int) -> Json:
    """Mantém no visual só os N valores da coluna com a maior medida."""
    return {
        "name": nome,
        "field": coluna.expressao(),
        "type": "TopN",
        "filter": {
            "Version": 2,
            "From": [
                {
                    "Name": "subconsulta",
                    "Expression": {
                        "Subquery": {
                            "Query": {
                                "Version": 2,
                                "From": [
                                    {"Name": "c", "Entity": coluna.tabela, "Type": 0},
                                    {"Name": "m", "Entity": por.tabela, "Type": 0},
                                ],
                                "Select": [coluna.expressao("c") | {"Name": "campo"}],
                                "OrderBy": [{"Direction": 2, "Expression": por.expressao("m")}],
                                "Top": quantidade,
                            }
                        }
                    },
                    "Type": 2,
                },
                {"Name": "c", "Entity": coluna.tabela, "Type": 0},
            ],
            "Where": [
                {
                    "Condition": {
                        "In": {
                            "Expressions": [coluna.expressao("c")],
                            "Table": {"SourceRef": {"Source": "subconsulta"}},
                        }
                    }
                }
            ],
        },
    }


def cartao(
    nome: str,
    posicao: Posicao,
    ordem: int,
    medida: Medida,
    rotulo: str,
    *,
    destaque: Tema | None = None,
) -> Json:
    """Indicador. Com `destaque`, é o número que a página lidera: um só por página.

    O destaque usa a cor de identidade do tema como fundo, com o número em branco.
    """
    corpo: Json = {
        "visualType": "card",
        "query": {"queryState": {"Values": _papel((medida, rotulo))}},
        "visualContainerObjects": _sem_titulo(),
    }
    if destaque:
        corpo["objects"] = {
            "labels": [
                {
                    "properties": {
                        "fontSize": literal(destaque.escala.destaque),
                        "color": cor(destaque.sobre_identidade),
                    }
                }
            ],
            "categoryLabels": [{"properties": {"color": cor(destaque.sobre_identidade_suave)}}],
        }
        corpo["visualContainerObjects"] |= _fundo(destaque.identidade)
    return _visual(nome, posicao, ordem, corpo)


def barras(
    nome: str,
    posicao: Posicao,
    ordem: int,
    titulo: str,
    categoria: Coluna,
    valores: list[Medida],
    *,
    horizontal: bool = True,
    ordenar_por: Campo | None = None,
    decrescente: bool = True,
    n_maiores: int | None = None,
    rotulos: bool = True,
) -> Json:
    """Barras (horizontais) ou colunas (verticais), na cor de série do tema."""
    consulta: Json = {"queryState": {"Category": _papel(categoria), "Y": _papel(*valores)}}
    consulta["sortDefinition"] = _ordenar(ordenar_por or valores[0], decrescente)
    filtros = None
    if n_maiores:
        filtros = [filtro_n_maiores(f"{nome}_maiores", categoria, valores[0], n_maiores)]
    objetos: Json = {
        "labels": [{"properties": {"show": literal(rotulos)}}],
        "legend": [{"properties": {"show": literal(len(valores) > 1)}}],
    }
    return _visual(
        nome,
        posicao,
        ordem,
        {
            "visualType": "clusteredBarChart" if horizontal else "clusteredColumnChart",
            "query": consulta,
            "objects": objetos,
            "visualContainerObjects": _titulo(titulo),
        },
        filtros,
    )


def area(
    nome: str,
    posicao: Posicao,
    ordem: int,
    titulo: str,
    tempo: Coluna,
    medida: Medida,
) -> Json:
    """Evolução no tempo de uma medida: linha com preenchimento leve, sem rótulo por ponto."""
    return _visual(
        nome,
        posicao,
        ordem,
        {
            "visualType": "areaChart",
            "query": {
                "queryState": {"Category": _papel(tempo), "Y": _papel(medida)},
                "sortDefinition": _ordenar(tempo, decrescente=False),
            },
            "objects": {
                "labels": [{"properties": {"show": literal(False)}}],
                "legend": [{"properties": {"show": literal(False)}}],
            },
            "visualContainerObjects": _titulo(titulo),
        },
    )


def tabela(
    nome: str,
    posicao: Posicao,
    ordem: int,
    titulo: str,
    campos: list[tuple[Campo, str, int]],
    *,
    ordenar_por: Campo,
    n_maiores: tuple[Coluna, Medida, int] | None = None,
) -> Json:
    """Tabela sem linha de total. Cada campo é (campo, rótulo da coluna, largura em pixels)."""
    filtros = None
    if n_maiores:
        filtros = [filtro_n_maiores(f"{nome}_maiores", *n_maiores)]
    return _visual(
        nome,
        posicao,
        ordem,
        {
            "visualType": "tableEx",
            "query": {
                "queryState": {"Values": _papel(*[(c, rotulo) for c, rotulo, _ in campos])},
                "sortDefinition": _ordenar(ordenar_por),
            },
            "objects": {
                "total": [{"properties": {"totals": literal(False)}}],
                "columnWidth": [
                    {"properties": {"value": literal(largura)}, "selector": {"metadata": c.ref}}
                    for c, _, largura in campos
                ],
            },
            "visualContainerObjects": _titulo(titulo),
        },
        filtros,
    )


def segmentacao(
    nome: str, posicao: Posicao, ordem: int, coluna: Coluna, rotulo: str, grupo: str
) -> Json:
    """Filtro em lista suspensa. Visuais do mesmo `grupo` ficam sincronizados entre páginas."""
    return _visual(
        nome,
        posicao,
        ordem,
        {
            "visualType": "slicer",
            "query": {"queryState": {"Values": _papel((coluna, rotulo))}},
            "objects": {"data": [{"properties": {"mode": literal("Dropdown")}}]},
            "visualContainerObjects": _sem_titulo(),
            "syncGroup": {"groupName": grupo, "fieldChanges": True, "filterChanges": True},
        },
    )


def paragrafos_de_texto(paragrafos: list[list[tuple[str, Json]]]) -> Json:
    """Objeto `general` de uma caixa de texto. Cada parágrafo é uma lista de (trecho, estilo)."""
    return {
        "general": [
            {
                "properties": {
                    "paragraphs": [
                        {
                            "textRuns": [
                                {"value": trecho, "textStyle": estilo}
                                for trecho, estilo in paragrafo
                            ]
                        }
                        for paragrafo in paragrafos
                    ]
                }
            }
        ]
    }


def texto(
    nome: str,
    posicao: Posicao,
    ordem: int,
    paragrafos: list[list[tuple[str, Json]]],
    *,
    fundo: str | None = None,
    margem: tuple[int, int] = (0, 0),
) -> Json:
    """Caixa de texto. Com `fundo`, vira uma faixa colorida; `margem` é (vertical, horizontal)."""
    moldura = (
        _fundo(fundo)
        if fundo
        else {
            "background": [{"properties": {"show": literal(False)}}],
            "border": [{"properties": {"show": literal(False)}}],
        }
    )
    return _visual(
        nome,
        posicao,
        ordem,
        {
            "visualType": "textbox",
            "objects": paragrafos_de_texto(paragrafos),
            "visualContainerObjects": _sem_titulo()
            | moldura
            | {
                "padding": [
                    {
                        "properties": {
                            "top": literal(margem[0]),
                            "bottom": literal(margem[0]),
                            "left": literal(margem[1]),
                            "right": literal(margem[1]),
                        }
                    }
                ],
            },
        },
    )


def campos_usados(visual: Json) -> set[tuple[str, str, str]]:
    """(tipo, tabela, nome) de cada coluna ou medida citada num visual, para conferir o modelo."""
    achados: set[tuple[str, str, str]] = set()

    def percorrer(no: Any, apelidos: dict[str, str]) -> None:
        if isinstance(no, dict):
            if isinstance(no.get("From"), list):
                apelidos = apelidos | {
                    f["Name"]: f["Entity"] for f in no["From"] if "Entity" in f and "Name" in f
                }
            for tipo in ("Column", "Measure"):
                item = no.get(tipo)
                if isinstance(item, dict) and "Property" in item:
                    origem = item["Expression"]["SourceRef"]
                    entidade = origem.get("Entity") or apelidos[origem["Source"]]
                    achados.add((tipo, entidade, item["Property"]))
            for valor in no.values():
                percorrer(valor, apelidos)
        elif isinstance(no, list):
            for valor in no:
                percorrer(valor, apelidos)

    percorrer(visual, {})
    return achados
