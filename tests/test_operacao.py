import json
from collections.abc import Sequence

from compras.cliente import Linha
from compras.comparar import Desvio
from compras.executor import Passo
from compras.operacao import Referencia, rodar
from compras.relatorio import para_json, para_markdown

PASSOS = [Passo("10_raw_item", "CRIA BRUTA"), Passo("40_fato_item_compra", "CRIA FATO")]
REGRAS = [("fato_chave_unica", "TESTE CHAVE")]
TOTAL = {
    "Gasto Total": 100.0,
    "Economia Defensável": 10.0,
    "Economia Conservadora": 20.0,
    "Gasto Acima do P75": 60.0,
    "gasto_homogeneo": 50.0,
}
VALORES = {
    "total / Gasto Total": 100.0,
    "total / Economia Defensável": 10.0,
    "total / Economia Conservadora": 20.0,
    "total / Gasto Acima do P75": 60.0,
    "total / % Economia Defensável": 0.2,
    "total / Ágio Médio sobre o P75": 0.5,
}
LINHAS = {"raw_item": 5, "fato_item_compra": 3}


class BancoFalso:
    """Responde pelo trecho da consulta; registra o que foi executado."""

    def __init__(self, violacoes: int = 0, quebra_em: str | None = None) -> None:
        self.violacoes = violacoes
        self.quebra_em = quebra_em
        self.executados: list[str] = []

    def estimar_bytes(self, sql: str) -> int | None:
        return 1024

    def executar(self, sql: str, teto_bytes: int) -> Sequence[Linha]:
        self.executados.append(sql)
        if sql == self.quebra_em:
            raise RuntimeError("tabela de origem indisponível")
        if "__TABLES__" in sql:
            return [{"table_id": t, "row_count": n} for t, n in LINHAS.items()]
        if "qualidade_resumo" in sql:
            return [{"etapa": "Válidas", "linhas": 3, "valor": 100.0}]
        if "GROUP BY i.categoria" in sql:
            return []
        if "FROM fato_item_compra" in sql:
            return [dict(TOTAL)]
        if sql == "TESTE CHAVE":
            return [{"id": n} for n in range(self.violacoes)]
        return []


def test_execucao_sem_mudanca_esta_ok() -> None:
    execucao = rodar(
        BancoFalso(), PASSOS, REGRAS, Referencia(VALORES, LINHAS), "compras", 10**9, "agora", "abc"
    )
    assert execucao.ok
    assert execucao.desvios == []
    assert execucao.comparados == len(VALORES) + len(LINHAS)
    assert [(p.tabela, p.linhas) for p in execucao.passos] == [
        ("raw_item", 5),
        ("fato_item_compra", 3),
    ]


def test_linha_a_menos_na_referencia_vira_desvio_com_nome() -> None:
    referencia = Referencia(VALORES, {**LINHAS, "fato_item_compra": 4})
    execucao = rodar(BancoFalso(), PASSOS, REGRAS, referencia, "compras", 10**9, "agora", "abc")
    assert not execucao.ok
    assert execucao.desvios == [Desvio("linhas / fato_item_compra", 4, 3)]
    assert "linhas / fato_item_compra" in para_markdown(execucao)


def test_valor_do_painel_diferente_vira_desvio() -> None:
    referencia = Referencia({**VALORES, "total / Gasto Total": 90.0}, LINHAS)
    execucao = rodar(BancoFalso(), PASSOS, REGRAS, referencia, "compras", 10**9, "agora", "abc")
    assert [d.nome for d in execucao.desvios] == ["total / Gasto Total"]


def test_teste_de_qualidade_que_falha_derruba_a_execucao() -> None:
    execucao = rodar(
        BancoFalso(violacoes=2),
        PASSOS,
        REGRAS,
        Referencia(VALORES, LINHAS),
        "compras",
        10**9,
        "agora",
        "abc",
    )
    assert not execucao.ok
    assert execucao.regras_que_falharam == 1
    assert "0 de 1 testes de qualidade passaram" in para_markdown(execucao)


def test_passo_que_quebra_para_tudo_e_fica_registrado() -> None:
    banco = BancoFalso(quebra_em="CRIA FATO")
    execucao = rodar(
        banco, PASSOS, REGRAS, Referencia(VALORES, LINHAS), "compras", 10**9, "agora", "abc"
    )
    assert not execucao.ok
    assert execucao.erro == "40_fato_item_compra: tabela de origem indisponível"
    assert [p.tabela for p in execucao.passos] == ["raw_item"]
    assert execucao.regras == []
    assert banco.executados == ["CRIA BRUTA", "CRIA FATO"]
    assert "**Parou:**" in para_markdown(execucao)


def test_relatorio_em_json_vai_e_volta() -> None:
    execucao = rodar(
        BancoFalso(violacoes=1),
        PASSOS,
        REGRAS,
        Referencia(VALORES, LINHAS),
        "compras",
        10**9,
        "agora",
        "abc",
    )
    dados = json.loads(json.dumps(para_json(execucao)))
    assert dados["ok"] is False
    assert dados["commit"] == "abc"
    assert dados["regras"][0] == {
        "regra": "fato_chave_unica",
        "violacoes": 1,
        "amostra": [{"id": "0"}],
    }
    assert dados["passos"][1]["linhas"] == 3
