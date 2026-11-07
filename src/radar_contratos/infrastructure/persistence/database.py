"""Conexões, versão do esquema e backup consistente."""

import sqlite3
from contextlib import closing
from pathlib import Path
from time import monotonic

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import URL, Engine, create_engine, event
from sqlalchemy.exc import DBAPIError

from radar_contratos.errors import DatabaseNotReadyError
from radar_contratos.infrastructure.persistence.read_errors import read_error


def make_engine(path: Path, *, create_if_missing: bool = True) -> Engine:
    if create_if_missing:
        path.parent.mkdir(parents=True, exist_ok=True)
        url = URL.create("sqlite", database=str(path.resolve()))
    else:
        # A aplicação abre um arquivo preparado; só init-db pode criar o banco.
        url = URL.create(
            "sqlite", database=path.resolve().as_uri(), query={"mode": "rw", "uri": "true"}
        )
    engine = create_engine(
        url,
        connect_args={"autocommit": False, "timeout": 5.0},
        hide_parameters=True,
    )

    @event.listens_for(engine, "connect")
    def set_integrity(connection, _record) -> None:
        previous = connection.autocommit
        connection.autocommit = True
        try:
            connection.execute("PRAGMA foreign_keys = ON")
        finally:
            connection.autocommit = previous

    return engine


def migration_config() -> Config:
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parent / "migrations"))
    return config


def initialize_database(engine: Engine) -> None:
    config = migration_config()
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")


def require_current_schema(engine: Engine) -> None:
    expected = ScriptDirectory.from_config(migration_config()).get_current_head()
    try:
        with engine.connect() as connection:
            actual = MigrationContext.configure(connection).get_current_revision()
    except DBAPIError as exc:
        raise read_error(
            exc,
            operation="database_open",
            message="Não foi possível abrir o banco local. Verifique o acesso e a preparação "
            "do ambiente antes de tentar novamente. Preserve o arquivo e seus backups.",
        ) from exc
    if actual != expected:
        raise DatabaseNotReadyError("Prepare ou atualize o ambiente antes de abrir o Radar.")


def backup_database(source: Path, destination: Path, *, timeout_seconds: float = 10.0) -> Path:
    if not source.is_file():
        raise DatabaseNotReadyError("Não há banco de dados para copiar.")
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb"):
        pass
    started = monotonic()

    def check_timeout(_status: int, _remaining: int, _total: int) -> None:
        if monotonic() - started > timeout_seconds:
            raise TimeoutError("O backup excedeu o tempo permitido.")

    try:
        with (
            closing(sqlite3.connect(source, autocommit=True, timeout=5)) as original,
            closing(sqlite3.connect(destination, autocommit=True, timeout=5)) as copy,
        ):
            original.backup(copy, pages=100, progress=check_timeout, sleep=0.1)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return destination
