"""Uma execução completa: recria as tabelas, testa, compara com a referência.

Para no primeiro passo que falha, mas sempre devolve o registro do que chegou a acontecer.
"""

import time
from collections.abc import Mapping
from dataclasses import dataclass

from compras import executor, qualidade
from compras.cliente import Banco
from compras.comparar import Desvio, Numero, achatar, comparar
from compras.painel import esperado
from compras.relatorio import Etapa, Execucao, PassoFeito


@dataclass(frozen=True)
class Referencia:
    valores: Mapping[str, Numero]
    linhas: Mapping[str, int]


def _tabela(passo: executor.Passo) -> str:
    """`40_fato_item_compra` cria a tabela `fato_item_compra`."""
    return passo.nome[3:]


def _linhas_por_tabela(banco: Banco, dataset: str, teto_bytes: int) -> dict[str, int]:
    consulta = f"SELECT table_id, row_count FROM `{dataset}.__TABLES__`"
    return {
        linha["table_id"]: int(linha["row_count"]) for linha in banco.executar(consulta, teto_bytes)
    }


def _funil(banco: Banco, teto_bytes: int) -> list[Etapa]:
    consulta = "SELECT etapa, linhas, valor FROM qualidade_resumo ORDER BY ordem, etapa"
    return [
        Etapa(
            linha["etapa"],
            int(linha["linhas"]),
            None if linha["valor"] is None else float(linha["valor"]),
        )
        for linha in banco.executar(consulta, teto_bytes)
    ]


def medir(
    banco: Banco, tabelas: list[str], dataset: str, teto_bytes: int
) -> tuple[dict[str, Numero], dict[str, int]]:
    """Os valores que o painel mostra e as linhas de cada tabela, como estão agora."""
    contagens = _linhas_por_tabela(banco, dataset, teto_bytes)
    linhas = {tabela: contagens[tabela] for tabela in tabelas if tabela in contagens}
    return achatar(esperado.calcular(banco, teto_bytes)), linhas


def rodar(
    banco: Banco,
    passos: list[executor.Passo],
    regras: list[tuple[str, str]],
    referencia: Referencia,
    dataset: str,
    teto_bytes: int,
    inicio: str,
    commit: str,
) -> Execucao:
    relogio = time.monotonic()
    resultados: list[executor.Resultado] = []
    erro: str | None = None
    for passo in passos:
        try:
            resultados.append(executor.executar_passo(banco, passo, teto_bytes, so_estimar=False))
        except Exception as falha:
            erro = f"{passo.nome}: {falha}"
            break

    linhas: dict[str, int] = {}
    verificacoes: list[qualidade.Verificacao] = []
    funil: list[Etapa] = []
    desvios: list[Desvio] = []
    comparados = 0
    if erro is None:
        valores, linhas = medir(banco, [_tabela(p) for p in passos], dataset, teto_bytes)
        verificacoes = qualidade.verificar(banco, regras, teto_bytes)
        funil = _funil(banco, teto_bytes)
        desvios = comparar(referencia.valores, valores) + comparar(
            {f"linhas / {t}": n for t, n in referencia.linhas.items()},
            {f"linhas / {t}": n for t, n in linhas.items()},
        )
        comparados = len(referencia.valores.keys() | valores.keys()) + len(
            referencia.linhas.keys() | linhas.keys()
        )

    return Execucao(
        inicio=inicio,
        commit=commit,
        segundos=time.monotonic() - relogio,
        passos=[
            PassoFeito(r.nome[3:], linhas.get(r.nome[3:]), r.bytes_estimados, r.segundos)
            for r in resultados
        ],
        regras=verificacoes,
        funil=funil,
        comparados=comparados,
        desvios=desvios,
        erro=erro,
    )
