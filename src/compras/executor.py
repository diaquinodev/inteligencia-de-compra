"""Roda os arquivos de `sql/` em ordem, com estimativa de custo e teto por consulta.

Cada arquivo cria uma tabela com `CREATE OR REPLACE TABLE`, então rodar de novo chega ao
mesmo resultado. Toda consulta passa antes pela estimativa (dry run) e roda com um teto de
bytes aplicado pelo BigQuery, que vale mesmo quando a estimativa não está disponível.
"""

import re
import time
from dataclasses import dataclass
from pathlib import Path

from compras.cliente import Banco

_NOME_DE_PASSO = re.compile(r"^\d{2}_[a-z0-9_]+\.sql$")


class TetoExcedido(Exception):
    """A consulta leria mais bytes do que o teto permite; ela não foi executada."""


@dataclass(frozen=True)
class Passo:
    nome: str
    sql: str


@dataclass(frozen=True)
class Resultado:
    nome: str
    bytes_estimados: int | None
    segundos: float
    executado: bool


def listar_passos(pasta: Path, prefixo: str = "") -> list[Passo]:
    """Passos em ordem de nome. Arquivo fora do padrão `NN_nome.sql` é erro, não é ignorado."""
    arquivos = sorted(pasta.glob("*.sql"))
    fora_do_padrao = [a.name for a in arquivos if not _NOME_DE_PASSO.match(a.name)]
    if fora_do_padrao:
        raise ValueError(f"Arquivos fora do padrão NN_nome.sql: {', '.join(fora_do_padrao)}")
    return [
        Passo(nome=a.stem, sql=a.read_text(encoding="utf-8"))
        for a in arquivos
        if a.name.startswith(prefixo)
    ]


def executar_passo(banco: Banco, passo: Passo, teto_bytes: int, so_estimar: bool) -> Resultado:
    estimado = banco.estimar_bytes(passo.sql)
    if estimado is not None and estimado > teto_bytes:
        raise TetoExcedido(
            f"{passo.nome}: a consulta leria {formatar_bytes(estimado)}, "
            f"acima do teto de {formatar_bytes(teto_bytes)}"
        )
    if so_estimar:
        return Resultado(passo.nome, estimado, 0.0, executado=False)
    inicio = time.monotonic()
    banco.executar(passo.sql, teto_bytes)
    return Resultado(passo.nome, estimado, time.monotonic() - inicio, executado=True)


def construir(
    banco: Banco, passos: list[Passo], teto_bytes: int, so_estimar: bool = False
) -> list[Resultado]:
    """Para no primeiro erro: os passos seguintes dependem das tabelas dos anteriores."""
    return [executar_passo(banco, passo, teto_bytes, so_estimar) for passo in passos]


def formatar_bytes(quantidade: int | None) -> str:
    if quantidade is None:
        return "sem estimativa"
    if quantidade >= 1024**3:
        return f"{quantidade / 1024**3:.2f} GiB"
    return f"{quantidade / 1024**2:.1f} MiB"
