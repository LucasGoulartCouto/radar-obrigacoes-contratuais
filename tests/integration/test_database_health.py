import hashlib
import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest

from radar_contratos.errors import RadarError, StorageBusyError, ValidationError
from radar_contratos.infrastructure.persistence.health import check_database


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_prepared_database_is_verified_without_modifying_it(engine):
    path = Path(engine.url.database)
    before = digest(path)
    health = check_database(path)
    assert health.ok
    assert digest(path) == before


def test_missing_database_does_not_create_file_or_directory(tmp_path):
    folder = tmp_path / "not-prepared"
    with pytest.raises(RadarError):
        check_database(folder / "radar.sqlite3")
    assert not folder.exists()


def test_invalid_file_is_preserved_and_error_is_sanitized(tmp_path, caplog):
    path = tmp_path / "private-location.sqlite3"
    original = b"Invalid synthetic fixture. " * 20
    path.write_bytes(original)
    with pytest.raises(RadarError) as caught:
        check_database(path)
    assert path.read_bytes() == original
    assert str(path) not in str(caught.value) + caplog.text


def test_forged_version_without_required_tables_is_not_healthy(engine):
    path = Path(engine.url.database)
    with sqlite3.connect(path) as connection:
        connection.execute("DROP TABLE confirmed_events")
    before = digest(path)
    health = check_database(path)
    assert not health.schema_ok and not health.ok
    assert digest(path) == before


def test_missing_required_column_is_not_healthy(engine):
    path = Path(engine.url.database)
    with sqlite3.connect(path) as connection:
        connection.execute("ALTER TABLE contracts DROP COLUMN title")
    assert not check_database(path).schema_ok


def test_foreign_key_violation_is_detected_without_repair(engine):
    path = Path(engine.url.database)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute(
            "INSERT INTO operations VALUES (?, ?, ?, ?)",
            ("orphan", "0" * 64, "MISSING_PRIVATE_CONTRACT", "{}"),
        )
    before = digest(path)
    health = check_database(path)
    assert health.schema_ok and health.integrity_ok
    assert not health.foreign_keys_ok and not health.ok
    assert digest(path) == before


def test_check_constraint_failure_is_detected_without_repair(service, engine):
    path = Path(engine.url.database)
    service.register(title="Sintético", actor="Operador", request_id=str(uuid4()))
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute("UPDATE contracts SET record_version=0")
    before = digest(path)
    health = check_database(path)
    assert health.checks_ok is False and not health.ok
    assert digest(path) == before


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf"), True])
def test_invalid_budget_is_rejected_before_opening_database(tmp_path, timeout):
    path = tmp_path / "missing" / "radar.sqlite3"
    with pytest.raises(ValidationError):
        check_database(path, timeout_seconds=timeout)
    assert not path.parent.exists()


def test_deadline_interrupts_check_without_changing_file(engine, monkeypatch):
    path = Path(engine.url.database)
    before = digest(path)
    times = iter([0.0, 0.0, 11.0])
    monkeypatch.setattr(
        "radar_contratos.infrastructure.persistence.health.monotonic", lambda: next(times, 11.0)
    )
    with pytest.raises(TimeoutError):
        check_database(path, timeout_seconds=10)
    assert digest(path) == before


def test_connection_rejects_writes_and_keeps_snapshot_transaction(engine, monkeypatch):
    from radar_contratos.infrastructure.persistence import health as module

    path = Path(engine.url.database)
    before = digest(path)
    original = module._schema_matches

    def verify(connection, expected):
        assert connection.in_transaction
        with pytest.raises(sqlite3.OperationalError) as caught:
            connection.execute("CREATE TABLE forbidden_write (id INTEGER)")
        assert caught.value.sqlite_errorcode & 0xFF == sqlite3.SQLITE_READONLY
        return original(connection, expected)

    monkeypatch.setattr(module, "_schema_matches", verify)
    assert check_database(path).ok
    assert digest(path) == before


def test_progress_handler_aborts_long_query_before_it_completes(engine, monkeypatch):
    path = Path(engine.url.database)
    before = digest(path)
    times = iter([0.0, 0.0, 11.0])
    completed = []

    def expensive(connection, _expected):
        connection.execute(
            "WITH RECURSIVE n(x) AS (VALUES(1) UNION ALL SELECT x+1 FROM n WHERE x<1000000) "
            "SELECT sum(x) FROM n"
        ).fetchone()
        completed.append(True)
        return True

    monkeypatch.setattr(
        "radar_contratos.infrastructure.persistence.health.monotonic", lambda: next(times, 11.0)
    )
    monkeypatch.setattr(
        "radar_contratos.infrastructure.persistence.health._schema_matches", expensive
    )
    with pytest.raises(TimeoutError):
        check_database(path)
    assert not completed
    assert digest(path) == before


def test_locked_database_is_reported_as_busy_without_retry(engine, monkeypatch):
    path = Path(engine.url.database)
    before = digest(path)
    native_connect = sqlite3.connect
    blocker = native_connect(path, autocommit=True, timeout=0)
    blocker.execute("BEGIN EXCLUSIVE")

    def immediate(*args, **kwargs):
        kwargs["timeout"] = 0
        return native_connect(*args, **kwargs)

    monkeypatch.setattr(
        "radar_contratos.infrastructure.persistence.health.sqlite3.connect", immediate
    )
    try:
        with pytest.raises(StorageBusyError):
            check_database(path)
    finally:
        blocker.execute("ROLLBACK")
        blocker.close()
    assert digest(path) == before
