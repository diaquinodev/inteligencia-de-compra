"""Prova, a cada execução no GitHub, que o robô não consegue sair do limite dele.

Roda com a identidade da conta de serviço do workflow. Esperado:

- consultar a tabela fato dentro do conjunto `compras`: permitido (controle positivo, para
  garantir que uma recusa abaixo não é só falta de login);
- criar um conjunto novo no projeto: recusado.

O projeto só tem o conjunto `compras`. Sem poder criar outro, o robô não tem onde escrever
fora dele.

Sai com erro se qualquer resultado for diferente do esperado. Não roda fora do GitHub
Actions: com o login do dono do projeto tudo seria permitido e o teste criaria um conjunto.
"""

import os
import sys
from collections.abc import Callable

from google.api_core.exceptions import Forbidden, GoogleAPIError
from google.cloud import bigquery

PROJETO = os.getenv("COMPRAS_PROJETO", "inteligencia-de-compra")
CONJUNTO = os.getenv("COMPRAS_DATASET", "compras")
FORA = "prova_fora_do_limite"


def consultar(cliente: bigquery.Client) -> None:
    cliente.query(f"SELECT COUNT(*) FROM `{PROJETO}.{CONJUNTO}.fato_item_compra`").result()


def criar_conjunto(cliente: bigquery.Client) -> None:
    conjunto = bigquery.Dataset(f"{PROJETO}.{FORA}")
    conjunto.location = "US"
    cliente.create_dataset(conjunto)
    # Só chega aqui se o limite falhou: desfaz o que criou.
    cliente.delete_dataset(f"{PROJETO}.{FORA}", delete_contents=True)


def resultado(acao: Callable[[bigquery.Client], None], cliente: bigquery.Client) -> str:
    try:
        acao(cliente)
    except Forbidden:
        return "recusado"
    except GoogleAPIError as erro:
        return f"erro inesperado ({type(erro).__name__}: {erro})"
    return "permitido"


def main() -> int:
    if os.getenv("GITHUB_ACTIONS") != "true":
        print("Este teste só roda no GitHub Actions, com a identidade do robô.")
        return 2
    cliente = bigquery.Client(project=PROJETO, location="US")
    provas = [
        ("consultar a tabela fato em compras", consultar, "permitido"),
        ("criar um conjunto novo no projeto", criar_conjunto, "recusado"),
    ]
    falhas = 0
    linhas = ["## Limite do robô", "", "| Tentativa | Esperado | Aconteceu |", "|---|---|---|"]
    for descricao, acao, esperado in provas:
        aconteceu = resultado(acao, cliente)
        certo = aconteceu.startswith(esperado)
        falhas += not certo
        linhas.append(f"| {'✅' if certo else '❌'} {descricao} | {esperado} | {aconteceu} |")
    texto = "\n".join(linhas) + "\n\n"
    print(texto)
    if resumo := os.getenv("GITHUB_STEP_SUMMARY"):
        with open(resumo, "a", encoding="utf-8") as arquivo:
            arquivo.write(texto)
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
