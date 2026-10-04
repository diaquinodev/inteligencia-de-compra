"""Lê as medidas de `powerbi/medidas.dax` e as escreve como uma tabela TMDL.

O arquivo `.dax` é a fonte única: ele roda como está na exibição de consulta DAX do Power BI
(para testar) e é dele que sai a tabela `Medidas` do modelo.
"""

import re
import textwrap
from dataclasses import dataclass

TABELA = "Medidas"

MOEDA = r"\R\$ #,0"
PRECO = r"\R\$ #,0.00"
PERCENTUAL = "0.0%"
INTEIRO = "#,0"
RAZAO = "#,0.00"
TEXTO = ""

FORMATOS = {
    "Gasto Total": MOEDA,
    "Itens Comprados": INTEIRO,
    "Fornecedores": INTEIRO,
    "Órgãos": INTEIRO,
    "Ticket Médio por Item": MOEDA,
    "Participação no Gasto": PERCENTUAL,
    "Posição do Fornecedor": INTEIRO,
    "Participação Acumulada": PERCENTUAL,
    "Classe ABC": TEXTO,
    "HHI": INTEIRO,
    "Gasto Comparável": MOEDA,
    "Compras Comparáveis": INTEIRO,
    "Preço Mediano": PRECO,
    "Preço P25": PRECO,
    "Preço P75": PRECO,
    "Menor Preço": PRECO,
    "Maior Preço": PRECO,
    "Dispersão de Preço": RAZAO,
    "Compras Acima do P75": INTEIRO,
    "Gasto Acima do P75": MOEDA,
    "Ágio Médio sobre o P75": PERCENTUAL,
    "Itens com Preço Suspeito": INTEIRO,
    "Economia Teto": MOEDA,
    "Economia Conservadora": MOEDA,
    "Economia Defensável": MOEDA,
    "Gasto Homogêneo": MOEDA,
    "% Economia Defensável": PERCENTUAL,
    "Gasto Mês Anterior": MOEDA,
    "Variação Mensal": PERCENTUAL,
    "Gasto Acumulado no Ano": MOEDA,
}

_INICIO = re.compile(r"^\s*MEASURE\s+Medidas\[(?P<nome>[^\]]+)\]\s*=\s*(?P<resto>.*)$")
_SECAO = re.compile(r"^\s*//\s*-{3,}\s*(?P<titulo>.+?)\s*-{3,}\s*$")
_COMENTARIO = re.compile(r"^\s*//\s?(?P<texto>.*)$")


@dataclass(frozen=True)
class Medida:
    nome: str
    expressao: str
    pasta: str
    descricao: str
    formato: str


def ler(texto_dax: str) -> list[Medida]:
    """Medidas do bloco DEFINE, na ordem do arquivo.

    Comentário `// ---- Título ----` abre uma pasta; os demais comentários descrevem a medida
    que vem logo abaixo.
    """
    linhas = texto_dax.splitlines()
    try:
        inicio = next(i for i, linha in enumerate(linhas) if linha.strip() == "DEFINE")
    except StopIteration:
        raise ValueError("O arquivo de medidas não tem o bloco DEFINE") from None

    medidas: list[Medida] = []
    pasta = ""
    descricao: list[str] = []
    nome: str | None = None
    corpo: list[str] = []

    def fechar() -> None:
        nonlocal nome, corpo, descricao
        if nome is None:
            return
        if nome not in FORMATOS:
            raise ValueError(f"Medida sem formato definido em FORMATOS: {nome}")
        expressao = textwrap.dedent("\n".join(corpo)).strip()
        if not expressao:
            raise ValueError(f"Medida sem expressão: {nome}")
        medidas.append(Medida(nome, expressao, pasta, " ".join(descricao), FORMATOS[nome]))
        nome, corpo, descricao = None, [], []

    for linha in linhas[inicio + 1 :]:
        if linha.strip().startswith("EVALUATE"):
            break
        secao = _SECAO.match(linha)
        comentario = _COMENTARIO.match(linha)
        comeco = _INICIO.match(linha)
        if secao:
            fechar()
            pasta = secao["titulo"]
        elif comentario:
            fechar()
            descricao.append(comentario["texto"].strip())
        elif comeco:
            fechar()
            nome = comeco["nome"]
            corpo = [comeco["resto"]] if comeco["resto"].strip() else []
        elif linha.strip() and nome is not None:
            corpo.append(linha)
    fechar()

    nomes = [m.nome for m in medidas]
    repetidas = sorted({n for n in nomes if nomes.count(n) > 1})
    if repetidas:
        raise ValueError(f"Medidas repetidas: {', '.join(repetidas)}")
    return medidas


def para_tmdl(medidas: list[Medida]) -> str:
    """Tabela `Medidas`: só medidas, com uma coluna oculta e uma partição vazia."""
    partes = [f"table {TABELA}\n"]
    for medida in medidas:
        bloco = []
        if medida.descricao:
            bloco.append(f"\t/// {medida.descricao}")
        bloco.append(f"\tmeasure '{medida.nome.replace(chr(39), chr(39) * 2)}' =")
        bloco.extend(f"\t\t\t{linha}" for linha in medida.expressao.splitlines())
        if medida.formato:
            bloco.append(f"\t\tformatString: {medida.formato}")
        if medida.pasta:
            bloco.append(f"\t\tdisplayFolder: {medida.pasta}")
        partes.append("\n".join(bloco) + "\n")
    partes.append(
        "\tcolumn Coluna\n"
        "\t\tdataType: string\n"
        "\t\tisHidden\n"
        "\t\tsummarizeBy: none\n"
        "\t\tsourceColumn: Coluna\n"
    )
    partes.append(
        f"\tpartition {TABELA} = m\n"
        "\t\tmode: import\n"
        "\t\tsource = #table(type table [Coluna = text], {})\n"
    )
    return "\n".join(partes) + "\n"
