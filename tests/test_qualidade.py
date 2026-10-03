from collections.abc import Sequence
from pathlib import Path

from compras.cliente import Linha
from compras.qualidade import listar_regras, verificar


class BancoFalso:
    def __init__(self, linhas_por_sql: dict[str, list[Linha]]) -> None:
        self.linhas_por_sql = linhas_por_sql

    def estimar_bytes(self, sql: str) -> int | None:
        return 0

    def executar(self, sql: str, teto_bytes: int) -> Sequence[Linha]:
        return self.linhas_por_sql[sql]


def test_regra_sem_linhas_passa_e_com_linhas_falha() -> None:
    banco = BancoFalso({"limpa": [], "suja": [{"id": n} for n in range(8)]})
    limpa, suja = verificar(banco, [("limpa", "limpa"), ("suja", "suja")], teto_bytes=1)
    assert limpa.passou
    assert not suja.passou
    assert suja.violacoes == 8
    assert len(suja.amostra) == 5


def test_nome_da_regra_e_o_nome_do_arquivo(tmp_path: Path) -> None:
    (tmp_path / "preco_positivo.sql").write_text("SELECT 1", encoding="utf-8")
    assert listar_regras(tmp_path) == [("preco_positivo", "SELECT 1")]
