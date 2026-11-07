import hashlib
import logging
import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.exc import DatabaseError

from radar_contratos.bootstrap import build_service
from radar_contratos.config import Settings
from radar_contratos.errors import RadarError, StorageBusyError
from radar_contratos.infrastructure.persistence.database import (
    initialize_database,
    make_engine,
    require_current_schema,
)


def test_opening_unprepared_app_does_not_create_directory_or_database(tmp_path):
    data_dir = tmp_path / "not-prepared"
    with pytest.raises(RadarError):
        build_service(Settings(data_dir))
    assert not data_dir.exists()


def test_invalid_database_is_preserved_and_reported_without_driver_details(tmp_path, caplog):
    path = tmp_path / "radar.sqlite3"
    original = b"Invalid synthetic database fixture. " * 20
    path.write_bytes(original)
    with caplog.at_level(logging.WARNING), pytest.raises(RadarError) as caught:
        build_service(Settings(tmp_path))
    assert path.read_bytes() == original
    assert "sqlite" not in str(caught.value).lower()
    assert str(path) not in str(caught.value) + caplog.text
    assert not caught.value.__class__.__module__.startswith("sqlalchemy")


def test_existing_database_with_uri_characters_remains_writable(tmp_path):
    data_dir = tmp_path / "dados com espaço # 100% &"
    engine = make_engine(data_dir / "radar.sqlite3")
    initialize_database(engine)
    engine.dispose()
    service, opened = build_service(Settings(data_dir))
    try:
        contract = service.register(title="Case sintético", actor="Rafael", request_id=str(uuid4()))
        assert service.list_contracts() == [contract]
        with opened.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
    finally:
        opened.dispose()
    assert len(list(data_dir.iterdir())) == 1


def test_database_moved_after_engine_creation_is_not_recreated(tmp_path):
    path = tmp_path / "radar.sqlite3"
    preparing = make_engine(path)
    initialize_database(preparing)
    preparing.dispose()
    before = path.read_bytes()
    engine = make_engine(path, create_if_missing=False)
    moved = tmp_path / "preserved.sqlite3"
    path.rename(moved)
    try:
        with pytest.raises(RadarError):
            require_current_schema(engine)
    finally:
        engine.dispose()
    assert not path.exists()
    assert moved.read_bytes() == before


def test_path_failure_before_engine_creation_does_not_expose_details(tmp_path, monkeypatch, caplog):
    marker = "PRIVATE_LOCAL_PATH_91"

    def fail(*_args, **_kwargs):
        raise PermissionError(marker)

    monkeypatch.setattr("radar_contratos.bootstrap.make_engine", fail)
    with caplog.at_level(logging.WARNING), pytest.raises(RadarError) as caught:
        build_service(Settings(tmp_path))
    assert marker not in str(caught.value) + caplog.text
    assert "operation=database_open" in caplog.text


@pytest.mark.parametrize(
    "code",
    [
        sqlite3.SQLITE_BUSY,
        sqlite3.SQLITE_LOCKED,
        sqlite3.SQLITE_BUSY | (2 << 8),
        sqlite3.SQLITE_IOERR,
        sqlite3.SQLITE_NOTADB,
    ],
)
def test_catalog_failures_are_sanitized_not_empty_and_recoverable(service, engine, caplog, code):
    contract = service.register(title="Case sintético", actor="Rafael", request_id=str(uuid4()))
    path = Path(engine.url.database)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    marker = "PRIVATE_DRIVER_DETAILS_71"
    cause = sqlite3.DatabaseError(marker)
    cause.sqlite_errorcode = code

    def fail(_conn, _cursor, _statement, _params, _context, _many):
        raise DatabaseError("PRIVATE_SQL", {"payload": marker}, cause)

    event.listen(engine, "before_cursor_execute", fail)
    try:
        with caplog.at_level(logging.WARNING), pytest.raises(RadarError) as caught:
            service.list_contracts()
    finally:
        event.remove(engine, "before_cursor_execute", fail)
    if code & 0xFF in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
        assert isinstance(caught.value, StorageBusyError)
    assert marker not in str(caught.value) + caplog.text
    assert "PRIVATE_SQL" not in str(caught.value) + caplog.text
    assert "operation=contract_list" in caplog.text
    assert service.list_contracts() == [contract]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
