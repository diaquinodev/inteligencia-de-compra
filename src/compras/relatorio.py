"""Registro de uma execução: o que rodou, quanto custou, o que os testes disseram.

Só transforma dados em texto; quem acessa o BigQuery e o disco é `operacao` e a linha de
comando.
"""

from dataclasses import asdict, dataclass
from typing import Any

from compras.comparar import Desvio, Numero
from compras.executor import formatar_bytes
from compras.qualidade import Verificacao


@dataclass(frozen=True)
class PassoFeito:
    tabela: str
    linhas: int | None
    bytes_estimados: int | None
    segundos: float


@dataclass(frozen=True)
class Etapa:
    nome: str
    linhas: int
    valor: float | None


@dataclass(frozen=True)
class Execucao:
    inicio: str
    commit: str
    segundos: float
    passos: list[PassoFeito]
    regras: list[Verificacao]
    funil: list[Etapa]
    comparados: int
    desvios: list[Desvio]
    erro: str | None = None

    @property
    def regras_que_falharam(self) -> int:
        return sum(not regra.passou for regra in self.regras)

    @property
    def ok(self) -> bool:
        return self.erro is None and not self.regras_que_falharam and not self.desvios


def para_json(execucao: Execucao) -> dict[str, Any]:
    dados = asdict(execucao)
    dados["ok"] = execucao.ok
    for regra in dados["regras"]:
        regra["amostra"] = [{k: str(v) for k, v in linha.items()} for linha in regra["amostra"]]
    return dados


def _inteiro(numero: int | None) -> str:
    return "—" if numero is None else f"{numero:,}".replace(",", ".")


def _numero(numero: Numero | None) -> str:
    if numero is None:
        return "—"
    if isinstance(numero, int):
        return _inteiro(numero)
    return f"{numero:,.4f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def _milhoes(valor: float) -> str:
    return f"{valor / 1e6:,.1f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def _variacao(desvio: Desvio) -> str:
    if desvio.referencia is None:
        return "valor novo"
    if desvio.atual is None:
        return "sumiu"
    variacao = desvio.variacao
    return "—" if variacao is None else f"{100 * variacao:+.4f}%".replace(".", ",")


def para_markdown(execucao: Execucao) -> str:
    estado = "ok" if execucao.ok else "FALHOU"
    total_bytes = sum(passo.bytes_estimados or 0 for passo in execucao.passos)
    regras_ok = len(execucao.regras) - execucao.regras_que_falharam
    linhas = [
        f"# Execução de {execucao.inicio} — {estado}",
        "",
        f"Código `{execucao.commit}` · {execucao.segundos:.0f} s · "
        f"{formatar_bytes(total_bytes)} estimados",
        "",
    ]
    if execucao.erro:
        linhas += [f"**Parou:** {execucao.erro}", ""]
    linhas += [
        f"- {len(execucao.passos)} tabelas recriadas",
        f"- {regras_ok} de {len(execucao.regras)} testes de qualidade passaram",
        f"- {len(execucao.desvios)} desvios em {execucao.comparados} valores comparados "
        "com a referência",
        "",
    ]
    if execucao.desvios:
        linhas += [
            "## Mudou desde a referência",
            "",
            "| Valor | Referência | Atual | Variação |",
            "|---|---:|---:|---:|",
        ]
        linhas += [
            f"| {d.nome} | {_numero(d.referencia)} | {_numero(d.atual)} | {_variacao(d)} |"
            for d in execucao.desvios
        ]
        linhas.append("")
    if execucao.regras:
        linhas += ["## Testes de qualidade", "", "| Regra | Violações |", "|---|---:|"]
        linhas += [
            f"| {'✅' if regra.passou else '❌'} `{regra.regra}` | {regra.violacoes} |"
            for regra in execucao.regras
        ]
        linhas.append("")
    if execucao.funil:
        linhas += [
            "## Funil de exclusões",
            "",
            "| Etapa | Linhas | R$ milhões |",
            "|---|---:|---:|",
        ]
        linhas += [
            f"| {etapa.nome} | {_inteiro(etapa.linhas)} | "
            f"{'—' if etapa.valor is None else _milhoes(etapa.valor)} |"
            for etapa in execucao.funil
        ]
        linhas.append("")
    linhas += [
        "## Tabelas",
        "",
        "| Tabela | Linhas | Leitura estimada | Tempo |",
        "|---|---:|---:|---:|",
    ]
    linhas += [
        f"| `{passo.tabela}` | {_inteiro(passo.linhas)} | "
        f"{formatar_bytes(passo.bytes_estimados)} | {passo.segundos:.1f} s |"
        for passo in execucao.passos
    ]
    return "\n".join(linhas) + "\n"
