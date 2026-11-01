import sqlite3
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from radar_contratos.application.contracts import ContractService
from radar_contratos.errors import (
    DatabaseNotReadyError,
    IdempotencyConflictError,
    StaleRecordError,
    StorageBusyError,
    ValidationError,
)
from radar_contratos.infrastructure.persistence.contracts import SqliteContractStore
from radar_contratos.infrastructure.persistence.database import (
    backup_database,
    initialize_database,
    make_engine,
    require_current_schema,
)
from radar_contratos.infrastructure.persistence.models import AuditRow, ContractRow, OperationRow


def register(service, request_id=None, title="Serviço fictício de hospedagem"):
    return service.register(
        title=title, actor="Rafael (simulação)", request_id=request_id or str(uuid4())
    )


def count(engine, model):
    with Session(engine) as session:
        return session.scalar(select(func.count()).select_from(model))


def test_same_request_is_replayed_without_duplicate_or_extra_audit(service, engine):
    request_id = str(uuid4())
    original = register(service, request_id)
    assert register(service, request_id) == original
    assert count(engine, ContractRow) == count(engine, AuditRow) == count(engine, OperationRow) == 1


def test_request_cannot_be_reused_with_different_payload(service, engine):
    request_id = str(uuid4())
    register(service, request_id)
    with pytest.raises(IdempotencyConflictError):
        register(service, request_id, title="Outro serviço fictício")
    assert count(engine, ContractRow) == count(engine, AuditRow) == 1


def test_stale_edit_cannot_overwrite_a_newer_name(service, engine):
    original = register(service)
    updated = service.rename(
        contract_id=original.id,
        title="Nome conferido",
        expected_version=1,
        actor="Rafael",
        request_id=str(uuid4()),
    )
    with pytest.raises(StaleRecordError):
        service.rename(
            contract_id=original.id,
            title="Nome desatualizado",
            expected_version=1,
            actor="Marina",
            request_id=str(uuid4()),
        )
    assert service.list_contracts() == [updated]
    assert updated.record_version == 2
    assert count(engine, AuditRow) == 2


def test_replay_returns_original_receipt_without_undoing_later_changes(service):
    request_id = str(uuid4())
    original = register(service, request_id)
    updated = service.rename(
        contract_id=original.id,
        title="Nome novo",
        expected_version=1,
        actor="Rafael",
        request_id=str(uuid4()),
    )
    assert register(service, request_id) == original
    assert service.list_contracts() == [updated]


def test_audit_failure_rolls_back_contract_and_receipt(service, engine):
    def fail_audit(_mapper, _connection, _target):
        raise RuntimeError("Falha simulada no histórico")

    event.listen(AuditRow, "before_insert", fail_audit)
    try:
        with pytest.raises(RuntimeError, match="Falha simulada"):
            register(service)
    finally:
        event.remove(AuditRow, "before_insert", fail_audit)
    assert count(engine, ContractRow) == count(engine, AuditRow) == count(engine, OperationRow) == 0


def test_foreign_keys_prevent_orphan_receipts(engine):
    with pytest.raises(IntegrityError), Session(engine) as session, session.begin():
        session.add(
            OperationRow(
                request_id=str(uuid4()),
                fingerprint="0" * 64,
                contract_id="contrato-inexistente",
                response={},
            )
        )


def test_migration_reexecution_preserves_data_and_schema(service, engine):
    original = register(service)
    initialize_database(engine)
    require_current_schema(engine)
    assert service.list_contracts() == [original]


def test_file_database_survives_reopening(service, engine, tmp_path):
    original = register(service)
    engine.dispose()
    reopened = make_engine(tmp_path / "radar.sqlite3")
    try:
        require_current_schema(reopened)
        assert ContractService(SqliteContractStore(reopened)).list_contracts() == [original]
    finally:
        reopened.dispose()


def test_backup_can_be_restored_to_a_new_database(service, tmp_path):
    original = register(service)
    backup_path = backup_database(tmp_path / "radar.sqlite3", tmp_path / "backup.sqlite3")
    restored_path = tmp_path / "restored.sqlite3"
    with sqlite3.connect(backup_path) as source, sqlite3.connect(restored_path) as destination:
        source.backup(destination)
    source.close()
    destination.close()
    restored = make_engine(restored_path)
    try:
        require_current_schema(restored)
        assert ContractService(SqliteContractStore(restored)).list_contracts() == [original]
    finally:
        restored.dispose()


def test_backup_never_overwrites_an_existing_destination(service, tmp_path):
    register(service)
    destination = tmp_path / "existing.sqlite3"
    destination.write_bytes(b"preservar")
    with pytest.raises(FileExistsError):
        backup_database(tmp_path / "radar.sqlite3", destination)
    assert destination.read_bytes() == b"preservar"


def test_schema_must_be_initialized_before_use(tmp_path):
    empty = make_engine(tmp_path / "empty.sqlite3")
    try:
        with pytest.raises(DatabaseNotReadyError):
            require_current_schema(empty)
    finally:
        empty.dispose()


@pytest.mark.parametrize("title", ["", "\n", "a" * 201, "linha\nquebrada"])
def test_invalid_input_does_not_persist_anything(service, engine, title):
    with pytest.raises(ValidationError):
        register(service, title=title)
    assert count(engine, ContractRow) == 0


def test_two_competing_edits_cannot_both_replace_the_same_version(service, engine):
    original = register(service)

    def rename(title):
        try:
            return service.rename(
                contract_id=original.id,
                title=title,
                expected_version=1,
                actor="Rafael",
                request_id=str(uuid4()),
            )
        except (StaleRecordError, StorageBusyError) as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(rename, ["Edição A", "Edição B"]))
    assert sum(not isinstance(result, Exception) for result in results) == 1
    assert service.list_contracts()[0].record_version == 2
    assert count(engine, AuditRow) == 2
