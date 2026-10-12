"""Linha de comando: `python -m compras executar`, `construir`, `testar`, `painel`, `esperado`."""

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from google.api_core.exceptions import NotFound

from compras import config, executor, operacao, qualidade, relatorio
from compras.cliente import BigQuery
from compras.comparar import achatar
from compras.painel import esperado, projeto, tema


def _construir(args: argparse.Namespace) -> int:
    cfg = config.carregar()
    passos = executor.listar_passos(cfg.pasta_sql, args.prefixo)
    if not passos:
        print(f"Nenhum passo em {cfg.pasta_sql} com o prefixo '{args.prefixo}'.")
        return 1
    banco = BigQuery(cfg)
    total = 0
    for passo in passos:
        try:
            resultado = executor.executar_passo(banco, passo, cfg.teto_bytes, args.estimar)
        except executor.TetoExcedido as erro:
            print(f"BLOQUEADO  {erro}")
            return 1
        except NotFound:
            print(f"PAROU      {passo.nome} depende de uma tabela que ainda não existe.")
            print("           Rode `python -m compras construir` sem --estimar.")
            return 1
        total += resultado.bytes_estimados or 0
        estado = f"{resultado.segundos:5.1f}s" if resultado.executado else "estimado"
        print(f"{estado}  {executor.formatar_bytes(resultado.bytes_estimados):>14}  {passo.nome}")
    print(f"Total estimado: {executor.formatar_bytes(total)}")
    return 0


def _testar(_: argparse.Namespace) -> int:
    cfg = config.carregar()
    regras = qualidade.listar_regras(cfg.pasta_testes)
    verificacoes = qualidade.verificar(BigQuery(cfg), regras, cfg.teto_bytes)
    for v in verificacoes:
        estado = "ok    " if v.passou else "FALHOU"
        print(f"{estado}  {v.regra}  ({v.violacoes} violações)")
        for linha in v.amostra:
            print(f"        {linha}")
    falhas = sum(not v.passou for v in verificacoes)
    print(f"{len(verificacoes) - falhas} de {len(verificacoes)} regras passaram.")
    return 1 if falhas else 0


_ESPERADO = config.RAIZ / "powerbi" / "esperado.json"
_LINHAS = config.RAIZ / "sql" / "linhas.json"
_RELATORIOS = config.RAIZ / "relatorios"


def _gravar_json(destino: Path, dados: Any) -> None:
    destino.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


def _commit() -> str:
    """O commit do código que rodou: o GitHub informa; na máquina, pergunta ao git."""
    if sha := os.getenv("GITHUB_SHA"):
        return sha[:7]
    git = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=config.RAIZ
    )
    return git.stdout.strip() or "desconhecido"


def _executar(args: argparse.Namespace) -> int:
    cfg = config.carregar()
    if not _ESPERADO.exists() or not _LINHAS.exists():
        if not args.aceitar:
            print(f"Sem referência ({_ESPERADO.name}, {_LINHAS.name}). Rode com --aceitar.")
            return 1
        referencia = operacao.Referencia({}, {})
    else:
        referencia = operacao.Referencia(
            achatar(json.loads(_ESPERADO.read_text(encoding="utf-8"))),
            json.loads(_LINHAS.read_text(encoding="utf-8")),
        )
    banco = BigQuery(cfg)
    passos = executor.listar_passos(cfg.pasta_sql)
    execucao = operacao.rodar(
        banco,
        passos,
        qualidade.listar_regras(cfg.pasta_testes),
        referencia,
        cfg.dataset,
        cfg.teto_bytes,
        inicio=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        commit=_commit(),
    )
    texto = relatorio.para_markdown(execucao)
    _RELATORIOS.mkdir(exist_ok=True)
    _gravar_json(_RELATORIOS / "ultima.json", relatorio.para_json(execucao))
    (_RELATORIOS / "ultima.md").write_text(texto, encoding="utf-8", newline="\n")
    # No GitHub Actions, este arquivo vira o resumo que aparece na página da execução.
    if resumo := os.getenv("GITHUB_STEP_SUMMARY"):
        with open(resumo, "a", encoding="utf-8") as arquivo:
            arquivo.write(texto)
    print(texto)
    print(f"Relatório em {_RELATORIOS / 'ultima.md'}")

    if args.aceitar and execucao.erro is None and not execucao.regras_que_falharam:
        _gravar_json(_ESPERADO, esperado.calcular(banco, cfg.teto_bytes))
        _, linhas = operacao.medir(banco, [p.nome[3:] for p in passos], cfg.dataset, cfg.teto_bytes)
        _gravar_json(_LINHAS, linhas)
        print("Referência regravada. Revise a diferença com `git diff` e abra um pull request.")
        return 0
    return 0 if execucao.ok else 1


def _painel(args: argparse.Namespace) -> int:
    pasta = config.RAIZ / "powerbi"
    texto_dax = (pasta / "medidas.dax").read_text(encoding="utf-8")
    escolhido = tema.TEMAS[args.tema]
    arquivos = projeto.gerar(pasta, texto_dax, escolhido)
    print(f"{len(arquivos)} arquivos em {pasta} (tema: {escolhido.area})")
    print(f"Abra {pasta / (projeto.NOME + '.pbip')} no Power BI Desktop.")
    return 0


def _esperado(_: argparse.Namespace) -> int:
    cfg = config.carregar()
    _gravar_json(_ESPERADO, esperado.calcular(BigQuery(cfg), cfg.teto_bytes))
    print(f"Valores de conferência gravados em {_ESPERADO}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="compras")
    comandos = parser.add_subparsers(required=True)

    completo = comandos.add_parser(
        "executar", help="recria tudo, testa, compara com a referência e grava o relatório"
    )
    completo.add_argument(
        "--aceitar", action="store_true", help="regrava a referência com os valores desta execução"
    )
    completo.set_defaults(func=_executar)

    construir = comandos.add_parser("construir", help="recria as tabelas a partir de sql/")
    construir.add_argument("--estimar", action="store_true", help="só estima o custo (dry run)")
    construir.add_argument("--prefixo", default="", help="roda só os passos com este prefixo")
    construir.set_defaults(func=_construir)

    testar = comandos.add_parser("testar", help="roda os testes de qualidade de sql/tests/")
    testar.set_defaults(func=_testar)

    painel = comandos.add_parser("painel", help="gera o projeto do Power BI em powerbi/")
    painel.add_argument(
        "--tema",
        choices=sorted(tema.TEMAS),
        default=tema.PADRAO.chave,
        help="área de negócio que define as cores do painel",
    )
    painel.set_defaults(func=_painel)

    valores = comandos.add_parser(
        "esperado", help="calcula no BigQuery os valores que o painel deve mostrar"
    )
    valores.set_defaults(func=_esperado)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
