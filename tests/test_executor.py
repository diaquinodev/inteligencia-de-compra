from collections.abc import Sequence
from pathlib import Path

import pytest

from compras.cliente import Linha
from compras.executor import (
    Passo,
    TetoExcedido,
    construir,
    executar_passo,
    formatar_bytes,
    listar_passos,
)


class BancoFalso:
    def __init__(self, bytes_por_sql: dict[str, int | None]) -> None:
        self.bytes_por_sql = bytes_por_sql
        self.executados: list[str] = []

    def estimar_bytes(self, sql: str) -> int | None:
        return self.bytes_por_sql[sql]

    def executar(self, sql: str, teto_bytes: int) -> Sequence[Linha]:
        self.executados.append(sql)
        return []


def _escrever(pasta: Path, nome: str, sql: str) -> None:
    (pasta / nome).write_text(sql, encoding="utf-8")


def test_passos_saem_em_ordem_de_nome(tmp_path: Path) -> None:
    _escrever(tmp_path, "20_limpo.sql", "b")
    _escrever(tmp_path, "10_bruto.sql", "a")
    assert [p.nome for p in listar_passos(tmp_path)] == ["10_bruto", "20_limpo"]


def test_prefixo_filtra_os_passos(tmp_path: Path) -> None:
    _escrever(tmp_path, "10_bruto.sql", "a")
    _escrever(tmp_path, "20_limpo.sql", "b")
    assert [p.nome for p in listar_passos(tmp_path, "20")] == ["20_limpo"]


def test_arquivo_fora_do_padrao_e_erro(tmp_path: Path) -> None:
    _escrever(tmp_path, "rascunho.sql", "a")
    with pytest.raises(ValueError, match=r"rascunho\.sql"):
        listar_passos(tmp_path)


def test_consulta_acima_do_teto_nao_executa() -> None:
    banco = BancoFalso({"caro": 11})
    with pytest.raises(TetoExcedido, match="10_caro"):
        executar_passo(banco, Passo("10_caro", "caro"), teto_bytes=10, so_estimar=False)
    assert banco.executados == []


def test_so_estimar_nao_executa() -> None:
    banco = BancoFalso({"a": 5})
    resultado = executar_passo(banco, Passo("10_a", "a"), teto_bytes=10, so_estimar=True)
    assert (resultado.bytes_estimados, resultado.executado) == (5, False)
    assert banco.executados == []


def test_construir_para_no_primeiro_passo_bloqueado() -> None:
    banco = BancoFalso({"a": 1, "caro": 99, "c": 1})
    passos = [Passo("10_a", "a"), Passo("20_caro", "caro"), Passo("30_c", "c")]
    with pytest.raises(TetoExcedido):
        construir(banco, passos, teto_bytes=10)
    assert banco.executados == ["a"]


def test_sem_estimativa_executa_e_deixa_o_teto_para_o_banco() -> None:
    banco = BancoFalso({"a": None})
    resultado = executar_passo(banco, Passo("10_a", "a"), teto_bytes=10, so_estimar=False)
    assert resultado.bytes_estimados is None
    assert banco.executados == ["a"]


def test_formatar_bytes() -> None:
    assert formatar_bytes(None) == "sem estimativa"
    assert formatar_bytes(1024**3) == "1.00 GiB"
    assert formatar_bytes(5 * 1024**2) == "5.0 MiB"
