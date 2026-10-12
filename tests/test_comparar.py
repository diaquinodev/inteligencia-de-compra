from compras.comparar import Desvio, achatar, comparar


def test_achatar_junta_os_niveis_no_nome() -> None:
    assert achatar({"total": {"Gasto": 1.5}, "categoria": {"Limpeza": {"HHI": 2}}}) == {
        "total / Gasto": 1.5,
        "categoria / Limpeza / HHI": 2,
    }


def test_valores_iguais_nao_geram_desvio() -> None:
    assert comparar({"linhas": 10, "gasto": 1.5}, {"linhas": 10, "gasto": 1.5}) == []


def test_contagem_e_exata() -> None:
    assert comparar({"linhas": 1_000_000_000}, {"linhas": 1_000_000_001}) == [
        Desvio("linhas", 1_000_000_000, 1_000_000_001)
    ]


def test_soma_aceita_diferenca_dentro_da_tolerancia() -> None:
    assert comparar({"gasto": 100.0}, {"gasto": 100.0 + 1e-9}, tolerancia=1e-9) == []


def test_soma_fora_da_tolerancia_e_desvio() -> None:
    (desvio,) = comparar({"gasto": 100.0}, {"gasto": 101.0}, tolerancia=1e-9)
    assert desvio.nome == "gasto"
    assert desvio.variacao == 0.01


def test_valor_que_sumiu_e_valor_novo_sao_desvios() -> None:
    assert comparar({"antigo": 1}, {"novo": 2}) == [
        Desvio("antigo", 1, None),
        Desvio("novo", None, 2),
    ]


def test_variacao_sem_base_de_comparacao() -> None:
    assert Desvio("x", None, 2).variacao is None
    assert Desvio("x", 0, 2).variacao is None
