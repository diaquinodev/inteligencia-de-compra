"""Testes do gerador do painel: medidas, arquivos gerados, esquemas e campos do modelo."""

import json
import re
import shutil
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

from compras.painel import medidas, paginas, projeto
from compras.painel.visuais import campos_usados

RAIZ = Path(__file__).resolve().parents[1]
POWERBI = RAIZ / "powerbi"
ESQUEMAS = Path(__file__).parent / "schemas" / "fabric"
URL_ESQUEMAS = "https://developer.microsoft.com/json-schemas/fabric/"

DAX_MINIMO = """
// cabeçalho ignorado
DEFINE
    // ---------- Base ----------
    MEASURE Medidas[Gasto Total] = SUM ( fato_item_compra[valor_total] )

    // ---------- Pergunta 2: onde se paga caro ----------
    // Explicação da medida
    // em duas linhas.
    MEASURE Medidas[Preço Mediano] =
        CALCULATE (
            MEDIAN ( fato_item_compra[valor_unitario] ),
            fato_item_compra[comparavel] = TRUE ()
        )

EVALUATE
ROW ( "Gasto Total", [Gasto Total] )
"""


def _buscar_esquema(url: str) -> Resource[Any]:
    caminho = ESQUEMAS / url.removeprefix(URL_ESQUEMAS)
    return Resource(contents=json.loads(caminho.read_text(encoding="utf-8")), specification=DRAFT7)


REGISTRO: Registry[Any] = Registry(retrieve=_buscar_esquema)  # type: ignore[call-arg]


@pytest.fixture
def projeto_gerado(tmp_path: Path) -> Path:
    """Projeto gerado numa pasta temporária, a partir do modelo e das medidas do repositório."""
    origem = POWERBI / f"{projeto.NOME}.SemanticModel" / "definition"
    shutil.copytree(origem, tmp_path / f"{projeto.NOME}.SemanticModel" / "definition")
    projeto.gerar(tmp_path, (POWERBI / "medidas.dax").read_text(encoding="utf-8"))
    return tmp_path


def _colunas_do_modelo(pasta: Path) -> dict[str, set[str]]:
    tabelas: dict[str, set[str]] = {}
    for arquivo in (pasta / f"{projeto.NOME}.SemanticModel" / "definition" / "tables").glob(
        "*.tmdl"
    ):
        texto = arquivo.read_text(encoding="utf-8")
        nome = re.match(r"table '?(.+?)'?\n", texto)
        assert nome, arquivo
        tabelas[nome[1]] = {
            m[2] for m in re.finditer(r"^\t(column|measure) '?(.+?)'?(?: =.*)?$", texto, re.M)
        }
    return tabelas


def _visuais(pasta: Path) -> list[tuple[str, dict[str, Any]]]:
    paginas_dir = pasta / f"{projeto.NOME}.Report" / "definition" / "pages"
    return [
        (arquivo.parents[2].name, json.loads(arquivo.read_text(encoding="utf-8")))
        for arquivo in sorted(paginas_dir.glob("*/visuals/*/visual.json"))
    ]


def test_ler_medidas_com_pasta_descricao_e_formato() -> None:
    gasto, mediana = medidas.ler(DAX_MINIMO)
    assert (gasto.nome, gasto.pasta, gasto.descricao) == ("Gasto Total", "Base", "")
    assert gasto.expressao == "SUM ( fato_item_compra[valor_total] )"
    assert mediana.pasta == "Pergunta 2: onde se paga caro"
    assert mediana.descricao == "Explicação da medida em duas linhas."
    assert mediana.expressao.splitlines()[0] == "CALCULATE ("
    assert mediana.formato == medidas.PRECO


def test_medida_sem_formato_e_erro() -> None:
    with pytest.raises(ValueError, match="Medida Nova"):
        medidas.ler("DEFINE\n    MEASURE Medidas[Medida Nova] = 1\n")


def test_medida_repetida_e_erro() -> None:
    with pytest.raises(ValueError, match="repetidas: Gasto Total"):
        medidas.ler(
            "DEFINE\n    MEASURE Medidas[Gasto Total] = 1\n    MEASURE Medidas[Gasto Total] = 2\n"
        )


def test_arquivo_sem_define_e_erro() -> None:
    with pytest.raises(ValueError, match="DEFINE"):
        medidas.ler('EVALUATE ROW ( "a", 1 )')


def test_tmdl_tem_uma_medida_por_bloco_com_expressao_recuada() -> None:
    tmdl = medidas.para_tmdl(medidas.ler(DAX_MINIMO))
    assert tmdl.startswith("table Medidas\n")
    assert "\tmeasure 'Gasto Total' =\n\t\t\tSUM ( fato_item_compra[valor_total] )\n" in tmdl
    assert "\t/// Explicação da medida em duas linhas.\n\tmeasure 'Preço Mediano' =" in tmdl
    assert "\t\tdisplayFolder: Pergunta 2: onde se paga caro\n" in tmdl
    assert "\tpartition Medidas = m\n" in tmdl


def test_toda_medida_do_repositorio_tem_formato() -> None:
    lidas = medidas.ler((POWERBI / "medidas.dax").read_text(encoding="utf-8"))
    assert {m.nome for m in lidas} == set(medidas.FORMATOS)


def test_arquivos_gerados_seguem_os_esquemas_da_microsoft(projeto_gerado: Path) -> None:
    conferidos = 0
    for arquivo in projeto_gerado.rglob("*"):
        if arquivo.suffix not in {".json", ".pbip", ".pbir", ".pbism"}:
            continue
        conteudo = json.loads(arquivo.read_text(encoding="utf-8"))
        if "$schema" not in conteudo:
            continue
        esquema = _buscar_esquema(conteudo["$schema"]).contents
        erros = list(Draft7Validator(esquema, registry=REGISTRO).iter_errors(conteudo))
        assert not erros, f"{arquivo.relative_to(projeto_gerado)}: {erros[0].message}"
        conferidos += 1
    assert conferidos >= 3 + 3 + 3 + 20


def test_todo_campo_usado_existe_no_modelo(projeto_gerado: Path) -> None:
    modelo = _colunas_do_modelo(projeto_gerado)
    for pagina, visual in _visuais(projeto_gerado):
        for _tipo, tabela, campo in campos_usados(visual):
            assert tabela in modelo, f"{pagina}/{visual['name']}: tabela {tabela} não existe"
            assert campo in modelo[tabela], (
                f"{pagina}/{visual['name']}: {tabela}[{campo}] não existe"
            )


def test_nomes_unicos_e_iguais_aos_das_pastas(projeto_gerado: Path) -> None:
    nomes = [visual["name"] for _, visual in _visuais(projeto_gerado)]
    assert len(nomes) == len(set(nomes))
    for arquivo in projeto_gerado.glob("*.Report/definition/pages/*/visuals/*/visual.json"):
        assert json.loads(arquivo.read_text(encoding="utf-8"))["name"] == arquivo.parent.name
    filtros = [
        filtro["name"]
        for _, visual in _visuais(projeto_gerado)
        for filtro in visual.get("filterConfig", {}).get("filters", [])
    ]
    assert len(filtros) == len(set(filtros))


@pytest.mark.parametrize("pagina", paginas.todas(), ids=lambda p: p.nome)
def test_visuais_cabem_na_pagina_e_nao_se_sobrepoem(pagina: paginas.Pagina) -> None:
    caixas = []
    for visual in pagina.visuais:
        p = visual["position"]
        caixa = (p["x"], p["y"], p["x"] + p["width"], p["y"] + p["height"])
        assert caixa[0] >= 0 and caixa[1] >= 0, visual["name"]
        assert caixa[2] <= paginas.LARGURA and caixa[3] <= paginas.ALTURA, visual["name"]
        caixas.append((visual["name"], caixa))
    for i, (nome_a, a) in enumerate(caixas):
        for nome_b, b in caixas[i + 1 :]:
            separados = a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1]
            assert separados, f"{nome_a} e {nome_b} se sobrepõem"


@pytest.mark.parametrize("pagina", paginas.todas(), ids=lambda p: p.nome)
def test_cada_pagina_tem_um_unico_numero_em_destaque(pagina: paginas.Pagina) -> None:
    cartoes = [v for v in pagina.visuais if v["visual"]["visualType"] == "card"]
    em_destaque = [v for v in cartoes if "objects" in v["visual"]]
    assert len(em_destaque) == 1
    assert 3 <= len(cartoes) <= 5


@pytest.mark.parametrize("pagina", paginas.todas(), ids=lambda p: p.nome)
def test_graficos_tem_uma_serie_so(pagina: paginas.Pagina) -> None:
    """O tema tem uma cor de dado; um gráfico com várias séries precisaria de paleta validada."""
    for visual in pagina.visuais:
        papeis = visual["visual"].get("query", {}).get("queryState", {})
        if "Y" in papeis:
            assert len(papeis["Y"]["projections"]) == 1, visual["name"]


def test_gerar_de_novo_da_o_mesmo_resultado_e_remove_visual_antigo(projeto_gerado: Path) -> None:
    def retrato() -> dict[str, str]:
        return {
            str(a.relative_to(projeto_gerado)): a.read_text(encoding="utf-8")
            for a in projeto_gerado.rglob("*")
            if a.is_file()
        }

    antes = retrato()
    sobra = (
        projeto_gerado
        / f"{projeto.NOME}.Report"
        / "definition"
        / "pages"
        / "gasto"
        / "visuals"
        / "antigo"
    )
    sobra.mkdir()
    (sobra / "visual.json").write_text("{}", encoding="utf-8")
    projeto.gerar(projeto_gerado, (POWERBI / "medidas.dax").read_text(encoding="utf-8"))
    assert retrato() == antes


def test_modelo_sem_a_tabela_de_medidas_e_erro(tmp_path: Path) -> None:
    definicao = tmp_path / f"{projeto.NOME}.SemanticModel" / "definition"
    definicao.mkdir(parents=True)
    (definicao / "model.tmdl").write_text("model Model\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Medidas"):
        projeto.gerar(tmp_path, DAX_MINIMO)
