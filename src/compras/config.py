"""Configuração lida do ambiente uma única vez, na borda do programa."""

import os
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

GIB = 1024**3


@dataclass(frozen=True)
class Config:
    projeto: str
    dataset: str
    local: str
    teto_bytes: int
    pasta_sql: Path
    pasta_testes: Path


def carregar() -> Config:
    teto_gib = float(os.getenv("COMPRAS_TETO_GIB", "6"))
    if teto_gib <= 0:
        raise ValueError("COMPRAS_TETO_GIB precisa ser maior que zero")
    return Config(
        projeto=os.getenv("COMPRAS_PROJETO", "inteligencia-de-compra"),
        dataset=os.getenv("COMPRAS_DATASET", "compras"),
        local=os.getenv("COMPRAS_LOCAL", "US"),
        teto_bytes=int(teto_gib * GIB),
        pasta_sql=RAIZ / "sql",
        pasta_testes=RAIZ / "sql" / "tests",
    )
