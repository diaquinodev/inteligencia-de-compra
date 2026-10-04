"""Borda com o BigQuery: credenciais, cliente e as duas operações que o pipeline usa."""

import shutil
import subprocess
from collections.abc import Sequence
from typing import Any, Protocol

import google.auth
from google.auth.credentials import Credentials
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import bigquery
from google.oauth2.credentials import Credentials as CredenciaisDeUsuario

from compras.config import Config

Linha = dict[str, Any]


class Banco(Protocol):
    """O que o pipeline precisa de um banco. Os testes usam uma implementação falsa."""

    def estimar_bytes(self, sql: str) -> int | None: ...

    def executar(self, sql: str, teto_bytes: int) -> Sequence[Linha]: ...


def _credenciais() -> Credentials:
    """Usa a credencial padrão; sem ela, o login já feito no `gcloud`."""
    try:
        credenciais: Credentials = google.auth.default()[0]
        return credenciais
    except DefaultCredentialsError:
        gcloud = shutil.which("gcloud")
        if gcloud is None:
            raise RuntimeError(
                "Sem credencial do Google. Instale o gcloud e rode `gcloud auth login`."
            ) from None
        token = subprocess.run(
            [gcloud, "auth", "print-access-token"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        return CredenciaisDeUsuario(token=token)  # type: ignore[no-untyped-call]


class BigQuery:
    def __init__(self, config: Config) -> None:
        self._cliente = bigquery.Client(
            project=config.projeto, credentials=_credenciais(), location=config.local
        )
        self._dataset = bigquery.DatasetReference(config.projeto, config.dataset)
        dataset = bigquery.Dataset(self._dataset)
        dataset.location = config.local
        self._cliente.create_dataset(dataset, exists_ok=True)

    def estimar_bytes(self, sql: str) -> int | None:
        """Bytes que a consulta leria, ou None quando o BigQuery não informa a estimativa.

        Acontece com algumas tabelas públicas particionadas. Nesse caso quem protege a cota é
        o `maximum_bytes_billed` de `executar`, aplicado pelo próprio BigQuery.
        """
        job = self._cliente.query(
            sql,
            job_config=bigquery.QueryJobConfig(
                dry_run=True, use_query_cache=False, default_dataset=self._dataset
            ),
        )
        estimado = job.total_bytes_processed
        return None if estimado is None else int(estimado)

    def executar(self, sql: str, teto_bytes: int) -> Sequence[Linha]:
        job = self._cliente.query(
            sql,
            job_config=bigquery.QueryJobConfig(
                maximum_bytes_billed=teto_bytes, default_dataset=self._dataset
            ),
        )
        return [dict(linha.items()) for linha in job.result()]
