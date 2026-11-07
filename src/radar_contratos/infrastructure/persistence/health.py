"""Diagnóstico técnico em uma fotografia somente de leitura, sem dados de negócio."""

import math
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from time import monotonic

from alembic.script import ScriptDirectory
from sqlalchemy import CheckConstraint

from radar_contratos.errors import ValidationError
from radar_contratos.infrastructure.persistence.database import migration_config
from radar_contratos.infrastructure.persistence.models import Base
from radar_contratos.infrastructure.persistence.read_errors import read_error


@dataclass(frozen=True, slots=True)
class DatabaseHealth:
    schema_ok: bool
    integrity_ok: bool
    foreign_keys_ok: bool
    checks_ok: bool | None

    @property
    def ok(self) -> bool:
        return (
            self.schema_ok and self.integrity_ok and self.foreign_keys_ok and self.checks_ok is True
        )


def _schema_matches(connection: sqlite3.Connection, expected: str) -> bool:
    tables = {
        row[0] for row in connection.execute("SELECT name FROM sqlite_schema WHERE type='table'")
    }
    if "alembic_version" not in tables:
        return False
    if connection.execute("SELECT version_num FROM alembic_version LIMIT 2").fetchall() != [
        (expected,)
    ]:
        return False
    for table in Base.metadata.sorted_tables:
        if table.name not in tables:
            return False
        columns = {
            row[0]
            for row in connection.execute("SELECT name FROM pragma_table_info(?)", (table.name,))
        }
        if not set(table.columns.keys()) <= columns:
            return False
    return True


def _checks_hold(connection: sqlite3.Connection) -> bool:
    # SQL e nomes vêm do modelo versionado, nunca do texto do banco/documentos.
    for table in Base.metadata.sorted_tables:
        for constraint in table.constraints:
            if isinstance(constraint, CheckConstraint):
                query = f'SELECT 1 FROM "{table.name}" WHERE NOT ({constraint.sqltext}) LIMIT 1'
                if connection.execute(query).fetchone() is not None:
                    return False
    return True


def check_database(path: Path, *, timeout_seconds: float = 10.0) -> DatabaseHealth:
    if (
        type(timeout_seconds) not in (int, float)
        or not math.isfinite(timeout_seconds)
        or timeout_seconds <= 0
    ):
        raise ValidationError("O tempo limite da verificação deve ser um número positivo e finito.")
    deadline = monotonic() + timeout_seconds

    def expired() -> bool:
        return monotonic() >= deadline

    def require_time() -> None:
        if expired():
            raise TimeoutError(
                "A verificação excedeu o tempo limite. Nenhuma correção foi executada."
            )

    try:
        expected = ScriptDirectory.from_config(migration_config()).get_current_head()
        with closing(
            sqlite3.connect(
                path.resolve().as_uri() + "?mode=ro",
                uri=True,
                autocommit=False,
                timeout=min(5.0, timeout_seconds),
            )
        ) as connection:
            # Um BEGIN do driver preserva o mesmo snapshot entre as verificações.
            connection.set_progress_handler(expired, 1000)
            require_time()
            schema_ok = _schema_matches(connection, expected)
            require_time()
            integrity_ok = connection.execute("PRAGMA quick_check(1)").fetchone() == ("ok",)
            require_time()
            foreign_keys_ok = connection.execute("PRAGMA foreign_key_check").fetchone() is None
            require_time()
            checks_ok = _checks_hold(connection) if schema_ok else None
            require_time()
            return DatabaseHealth(schema_ok, integrity_ok, foreign_keys_ok, checks_ok)
    except sqlite3.Error as exc:
        if expired():
            raise TimeoutError(
                "A verificação excedeu o tempo limite. Nenhuma correção foi executada."
            ) from None
        raise read_error(
            exc,
            operation="database_check",
            message="Não foi possível verificar o banco local. Confira o acesso e preserve "
            "o arquivo e seus backups antes de tentar novamente.",
        ) from exc
    except TimeoutError:
        # TimeoutError também é OSError; não converter orçamento excedido em falha de acesso.
        raise
    except OSError as exc:
        raise read_error(
            exc,
            operation="database_check",
            message="Não foi possível acessar o banco para verificação. Confira o diretório "
            "de dados e preserve os arquivos existentes.",
        ) from exc
