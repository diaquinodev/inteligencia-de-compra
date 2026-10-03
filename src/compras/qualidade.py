"""Testes de qualidade: cada arquivo de `sql/tests/` é uma consulta que deve voltar vazia.

As linhas que voltam são as que violam a regra. O nome do arquivo é o nome da regra.
"""

from dataclasses import dataclass
from pathlib import Path

from compras.cliente import Banco, Linha

_AMOSTRA = 5


@dataclass(frozen=True)
class Verificacao:
    regra: str
    violacoes: int
    amostra: list[Linha]

    @property
    def passou(self) -> bool:
        return self.violacoes == 0


def listar_regras(pasta: Path) -> list[tuple[str, str]]:
    return [(a.stem, a.read_text(encoding="utf-8")) for a in sorted(pasta.glob("*.sql"))]


def verificar(banco: Banco, regras: list[tuple[str, str]], teto_bytes: int) -> list[Verificacao]:
    verificacoes = []
    for regra, sql in regras:
        linhas = banco.executar(sql, teto_bytes)
        verificacoes.append(Verificacao(regra, len(linhas), list(linhas[:_AMOSTRA])))
    return verificacoes
