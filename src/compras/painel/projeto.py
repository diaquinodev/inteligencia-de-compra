"""Escreve o projeto do Power BI (PBIP) em disco: tabela de medidas, tema e páginas.

O modelo (tabelas, colunas e relacionamentos em TMDL) já está versionado na pasta do
projeto; daqui saem a tabela `Medidas` e todo o relatório. Rodar de novo recria o relatório
inteiro, sem deixar visual antigo para trás.
"""

import json
import shutil
from pathlib import Path
from typing import Any

from compras.painel import medidas, paginas, tema
from compras.painel.visuais import SCHEMA_BASE

NOME = "inteligencia-de-compra"
_RAIZ_SCHEMAS = "https://developer.microsoft.com/json-schemas/fabric"
_ARQUIVO_TEMA = f"{tema.NOME}.json"


def _gravar(caminho: Path, conteudo: dict[str, Any]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


def _pbip() -> dict[str, Any]:
    return {
        "$schema": f"{_RAIZ_SCHEMAS}/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{NOME}.Report"}}],
        "settings": {"enableAutoRecovery": True},
    }


def _pbism() -> dict[str, Any]:
    return {
        "$schema": f"{_RAIZ_SCHEMAS}/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.2",
        "settings": {},
    }


def _pbir() -> dict[str, Any]:
    return {
        "$schema": f"{_RAIZ_SCHEMAS}/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{NOME}.SemanticModel"}},
    }


def _relatorio() -> dict[str, Any]:
    return {
        "$schema": f"{SCHEMA_BASE}/report/2.0.0/schema.json",
        "themeCollection": {
            "customTheme": {
                "name": _ARQUIVO_TEMA,
                "reportVersionAtImport": "5.59",
                "type": "RegisteredResources",
            }
        },
        "resourcePackages": [
            {
                "name": "RegisteredResources",
                "type": "RegisteredResources",
                "items": [{"name": _ARQUIVO_TEMA, "path": _ARQUIVO_TEMA, "type": "CustomTheme"}],
            }
        ],
        "settings": {
            "useStylableVisualContainerHeader": True,
            "exportDataMode": "AllowSummarized",
            "defaultDrillFilterOtherVisuals": True,
            "allowChangeFilterTypes": True,
            "useEnhancedTooltips": True,
        },
    }


def _pagina(pagina: paginas.Pagina) -> dict[str, Any]:
    return {
        "$schema": f"{SCHEMA_BASE}/page/2.0.0/schema.json",
        "name": pagina.nome,
        "displayName": pagina.titulo,
        "displayOption": "FitToPage",
        "height": paginas.ALTURA,
        "width": paginas.LARGURA,
    }


def gerar(pasta: Path, texto_dax: str) -> list[Path]:
    """Gera o projeto em `pasta` e devolve os arquivos escritos."""
    modelo = pasta / f"{NOME}.SemanticModel"
    definicao_modelo = modelo / "definition"
    arquivo_modelo = definicao_modelo / "model.tmdl"
    if not arquivo_modelo.exists():
        raise FileNotFoundError(f"Modelo TMDL não encontrado em {definicao_modelo}")
    if f"ref table {medidas.TABELA}" not in arquivo_modelo.read_text(encoding="utf-8"):
        raise ValueError(f"model.tmdl não referencia a tabela {medidas.TABELA}")

    _gravar(pasta / f"{NOME}.pbip", _pbip())
    _gravar(modelo / "definition.pbism", _pbism())
    tabela_medidas = definicao_modelo / "tables" / f"{medidas.TABELA}.tmdl"
    tabela_medidas.write_text(
        medidas.para_tmdl(medidas.ler(texto_dax)), encoding="utf-8", newline="\n"
    )

    relatorio = pasta / f"{NOME}.Report"
    if relatorio.exists():
        shutil.rmtree(relatorio)
    definicao = relatorio / "definition"
    _gravar(relatorio / "definition.pbir", _pbir())
    _gravar(
        definicao / "version.json",
        {"$schema": f"{SCHEMA_BASE}/versionMetadata/1.0.0/schema.json", "version": "2.0.0"},
    )
    _gravar(definicao / "report.json", _relatorio())
    _gravar(relatorio / "StaticResources" / "RegisteredResources" / _ARQUIVO_TEMA, tema.definicao())

    todas = paginas.todas()
    _gravar(
        definicao / "pages" / "pages.json",
        {
            "$schema": f"{SCHEMA_BASE}/pagesMetadata/1.0.0/schema.json",
            "pageOrder": [p.nome for p in todas],
            "activePageName": todas[0].nome,
        },
    )
    for pagina in todas:
        pasta_pagina = definicao / "pages" / pagina.nome
        _gravar(pasta_pagina / "page.json", _pagina(pagina))
        for visual in pagina.visuais:
            _gravar(pasta_pagina / "visuals" / visual["name"] / "visual.json", visual)

    return sorted(
        [
            pasta / f"{NOME}.pbip",
            modelo / "definition.pbism",
            tabela_medidas,
            *(p for p in relatorio.rglob("*") if p.is_file()),
        ]
    )
