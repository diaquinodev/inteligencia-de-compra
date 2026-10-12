"""Compara os valores de uma execução com a referência versionada no repositório.

O código não mudou e o número mudou: a origem foi republicada, uma regra passou a barrar
mais linhas ou um total saiu do lugar. Em qualquer caso alguém precisa olhar antes de o
número novo valer.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

Numero = int | float

# Somas em reais variam nas últimas casas entre execuções (medido: cerca de 1e-15 do valor,
# em 12/10/2026); a tolerância fica mil vezes acima disso. Contagens são exatas.
TOLERANCIA = 1e-12


@dataclass(frozen=True)
class Desvio:
    nome: str
    referencia: Numero | None
    atual: Numero | None

    @property
    def variacao(self) -> float | None:
        """Variação relativa; None quando o valor apareceu, sumiu ou a referência é zero."""
        if self.referencia is None or self.atual is None or self.referencia == 0:
            return None
        return (self.atual - self.referencia) / abs(self.referencia)


def achatar(valores: Mapping[str, Any], prefixo: str = "") -> dict[str, Numero]:
    """`{"total": {"Gasto Total": 1}}` vira `{"total / Gasto Total": 1}`."""
    plano: dict[str, Numero] = {}
    for chave, valor in valores.items():
        nome = f"{prefixo}{chave}"
        if isinstance(valor, Mapping):
            plano.update(achatar(valor, f"{nome} / "))
        else:
            plano[nome] = valor
    return plano


def _igual(referencia: Numero, atual: Numero, tolerancia: float) -> bool:
    if isinstance(referencia, int) and isinstance(atual, int):
        return referencia == atual
    return abs(atual - referencia) <= tolerancia * max(abs(referencia), abs(atual))


def comparar(
    referencia: Mapping[str, Numero], atual: Mapping[str, Numero], tolerancia: float = TOLERANCIA
) -> list[Desvio]:
    """Valores que mudaram, sumiram ou apareceram, em ordem de nome."""
    desvios = []
    for nome in sorted(referencia.keys() | atual.keys()):
        antes, agora = referencia.get(nome), atual.get(nome)
        if antes is None or agora is None or not _igual(antes, agora, tolerancia):
            desvios.append(Desvio(nome, antes, agora))
    return desvios
