import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from alembic import command
from sqlalchemy import event, func, select, text
from sqlalchemy.orm import Session

from radar_contratos.application.contracts import ContractService
from radar_contratos.application.documents import DocumentService
from radar_contratos.domain.documents import DocumentInput, DocumentRole
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
    migration_config,
    require_current_schema,
)
from radar_contratos.infrastructure.persistence.documents import SqliteDocumentStore
from radar_contratos.infrastructure.persistence.models import (
    AuditRow,
    DocumentRevisionRow,
    DocumentUploadRow,
    OperationRow,
)


@pytest.fixture
def documents(engine):
    return DocumentService(SqliteDocumentStore(engine))


@pytest.fixture
def contract(service):
    return service.register(title="Contrato sintético", actor="Rafael", request_id=str(uuid4()))


def source(
    content=b"Texto sint\xc3\xa9tico\r\nsegunda linha", name="base.txt", role=DocumentRole.BASE
):
    return DocumentInput(name, content, role)


def send(documents, contract, *, items=None, version=0, request_id=None, **kwargs):
    return documents.submit(
        contract_id=contract.id,
        documents=items if items is not None else (source(),),
        expected_version=version,
        actor="Rafael",
        request_id=request_id or str(uuid4()),
        synthetic=True,
        **kwargs,
    )


def counts(engine):
    with Session(engine) as session:
        return tuple(
            session.scalar(select(func.count()).select_from(model))
            for model in (
                DocumentRevisionRow,
                DocumentUploadRow,
                OperationRow,
                AuditRow,
            )
        )


def test_original_bytes_and_reference_survive_reopening(documents, contract, engine, tmp_path):
    receipt = send(documents, contract)
    engine.dispose()
    reopened = make_engine(tmp_path / "radar.sqlite3")
    try:
        read = DocumentService(SqliteDocumentStore(reopened))
        (stored,) = read.get_documents(contract.id, receipt.revision_id, receipt.request_id)
        assert stored.original_bytes == source().content
        assert stored.reference_text == "Texto sintético\nsegunda linha"
        assert read.list_revisions(contract.id)[0].number == 1
        assert read.current_states()[contract.id] == "Aguardando análise"
    finally:
        reopened.dispose()


def test_same_request_replays_once_even_after_newer_revision(documents, contract, engine, service):
    request_id = str(uuid4())
    first = send(documents, contract, request_id=request_id)
    assert send(documents, contract, request_id=request_id) == first
    assert counts(engine) == (1, 1, 2, 2)
    send(documents, contract, items=(source(b"Outro texto"),), version=1)
    assert send(documents, contract, request_id=request_id) == first
    assert service.list_contracts()[0].document_version == 2
    assert counts(engine) == (2, 2, 3, 3)


def test_request_id_cannot_change_payload_or_operation(documents, contract, service):
    request_id = str(uuid4())
    send(documents, contract, request_id=request_id)
    with pytest.raises(IdempotencyConflictError):
        send(documents, contract, request_id=request_id, items=(source(b"Mudou"),))
    with pytest.raises(IdempotencyConflictError):
        service.rename(
            contract_id=contract.id,
            title="Novo nome",
            expected_version=1,
            actor="Rafael",
            request_id=request_id,
        )


def test_equivalent_set_keeps_revision_but_preserves_every_received_variant(
    documents,
    contract,
    engine,
):
    first = send(documents, contract, items=(source(b"A\nB"), source(b"C", "anexo.txt")))
    second = send(
        documents,
        contract,
        version=1,
        items=(
            source(b"C", "renomeado.txt"),
            source(b"\xef\xbb\xbfA\r\nB"),
        ),
    )
    assert not second.created_revision
    assert second.revision_id == first.revision_id
    assert counts(engine) == (1, 4, 3, 2)
    received = documents.get_documents(contract.id, second.revision_id, second.request_id)
    assert received[1].original_bytes == b"\xef\xbb\xbfA\r\nB"
    original = documents.get_documents(contract.id, first.revision_id, first.request_id)
    assert original[0].original_bytes == b"A\nB"
    assert len(documents.list_submissions(contract.id, first.revision_id)) == 2


def test_text_changes_role_changes_and_return_to_old_text_are_new_revisions(documents, contract):
    receipts = [send(documents, contract, items=(source(b"A"),))]
    receipts.append(send(documents, contract, version=1, items=(source(b"B"),)))
    receipts.append(send(documents, contract, version=2, items=(source(b"A"),)))
    receipts.append(
        send(documents, contract, version=3, items=(source(b"A", role=DocumentRole.UNKNOWN),))
    )
    assert [receipt.revision_number for receipt in receipts] == [1, 2, 3, 4]
    assert all(receipt.created_revision for receipt in receipts)
    assert len({receipt.revision_id for receipt in receipts}) == 4


def test_same_file_in_another_contract_is_separate_and_receipts_cannot_cross(
    documents,
    contract,
    service,
):
    another = service.register(title="Outro case", actor="Marina", request_id=str(uuid4()))
    first, second = send(documents, contract), send(documents, another)
    assert first.revision_id != second.revision_id
    with pytest.raises(ValidationError):
        documents.get_documents(another.id, first.revision_id, first.request_id)
    with pytest.raises(ValidationError):
        documents.get_documents(contract.id, first.revision_id, second.request_id)
    with pytest.raises(ValidationError):
        documents.list_submissions(another.id, first.revision_id)


def test_audit_failure_rolls_back_everything_and_same_request_can_recover(
    documents,
    contract,
    engine,
    service,
):
    request_id = str(uuid4())

    def fail(_mapper, _connection, _target):
        raise RuntimeError("Falha simulada")

    event.listen(AuditRow, "before_insert", fail)
    try:
        with pytest.raises(RuntimeError):
            send(documents, contract, request_id=request_id)
    finally:
        event.remove(AuditRow, "before_insert", fail)
    assert counts(engine) == (0, 0, 1, 1)
    assert service.list_contracts()[0].document_version == 0
    assert send(documents, contract, request_id=request_id).revision_number == 1


def test_competing_submissions_cannot_both_replace_the_same_base(documents, contract, service):
    def submit(value):
        try:
            return send(documents, contract, items=(source(value),))
        except (StaleRecordError, StorageBusyError) as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, [b"A", b"B"]))
    assert sum(not isinstance(result, Exception) for result in results) == 1
    assert service.list_contracts()[0].document_version == 1
    assert len(documents.list_revisions(contract.id)) == 1


def test_invalid_member_rejects_whole_set_and_keeps_current_base(documents, contract, engine):
    first = send(documents, contract)
    before = counts(engine)
    with pytest.raises(ValidationError):
        send(documents, contract, version=1, items=(source(b"Novo"), source(b"\xff", "ruim.txt")))
    assert counts(engine) == before
    assert documents.list_revisions(contract.id)[0].id == first.revision_id


def test_removal_creates_empty_revision_without_becoming_analysis_without_events(
    documents, contract
):
    send(documents, contract)
    with pytest.raises(ValidationError):
        send(documents, contract, version=1, items=())
    empty = send(documents, contract, version=1, items=(), allow_empty=True)
    assert empty.revision_number == 2
    assert documents.current_states()[contract.id] == "Aguardando documentos"
    assert documents.get_documents(contract.id, empty.revision_id, empty.request_id) == ()
    assert not send(documents, contract, version=2, items=(), allow_empty=True).created_revision
    assert len(documents.list_revisions(contract.id)) == 2


def test_known_amendment_cannot_be_ignored_by_removing_or_relabeling_file(documents, contract):
    send(documents, contract, items=(source(role=DocumentRole.AMENDMENT),))
    send(documents, contract, version=1, items=(source(role=DocumentRole.BASE),))
    assert documents.current_states()[contract.id] == "Bloqueado: aditivo declarado"
    send(documents, contract, version=2, items=(), allow_empty=True)
    assert documents.current_states()[contract.id] == "Bloqueado: aditivo declarado"


def test_backup_restores_documents_and_history(documents, contract, engine, tmp_path):
    receipt = send(documents, contract)
    backup = backup_database(tmp_path / "radar.sqlite3", tmp_path / "document-backup.sqlite3")
    restored = make_engine(backup)
    try:
        restored_documents = DocumentService(SqliteDocumentStore(restored))
        assert (
            restored_documents.get_documents(contract.id, receipt.revision_id, receipt.request_id)[
                0
            ].original_bytes
            == source().content
        )
        assert counts(restored) == counts(engine)
        assert restored.hide_parameters
    finally:
        restored.dispose()


def test_concurrent_identical_request_can_be_replayed_without_extra_receipt(
    documents,
    contract,
    engine,
):
    request_id = str(uuid4())

    def submit(_index):
        try:
            return send(documents, contract, request_id=request_id)
        except StorageBusyError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, range(2)))
    assert any(result is not None for result in results)
    receipt = send(documents, contract, request_id=request_id)
    assert all(result is None or result == receipt for result in results)
    assert counts(engine) == (1, 1, 2, 2)


def test_upgrade_from_foundation_preserves_existing_rows_and_accepts_documents(tmp_path):
    engine = make_engine(tmp_path / "old.sqlite3")
    contract_id, request_id, audit_id = (str(uuid4()) for _ in range(3))
    try:
        config = migration_config()
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "0001_foundation")
            connection.execute(
                text("INSERT INTO contracts VALUES (:id, :title, 3, :at, :at)"),
                {"id": contract_id, "title": "Case preservado", "at": "2026-11-01"},
            )
            connection.execute(
                text("INSERT INTO operations VALUES (:id, :fp, :contract, :response)"),
                {
                    "id": request_id,
                    "fp": "0" * 64,
                    "contract": contract_id,
                    "response": json.dumps({"original": True}),
                },
            )
            connection.execute(
                text(
                    "INSERT INTO audit_events VALUES "
                    "(:id, :request, :contract, :action, :actor, :at, :details)"
                ),
                {
                    "id": audit_id,
                    "request": request_id,
                    "contract": contract_id,
                    "action": "contract_registered",
                    "actor": "Rafael",
                    "at": "2026-11-01",
                    "details": "{}",
                },
            )
        with pytest.raises(DatabaseNotReadyError):
            require_current_schema(engine)
        backup_database(tmp_path / "old.sqlite3", tmp_path / "before-upgrade.sqlite3")
        initialize_database(engine)
        initialize_database(engine)
        require_current_schema(engine)
        contracts = ContractService(SqliteContractStore(engine)).list_contracts()
        assert contracts[0].title == "Case preservado"
        assert contracts[0].record_version == 3
        assert contracts[0].document_version == 0
        assert counts(engine) == (0, 0, 1, 1)
        with Session(engine) as session:
            assert session.get(OperationRow, request_id).response == {"original": True}
            assert session.get(AuditRow, audit_id).actor == "Rafael"
        assert send(DocumentService(SqliteDocumentStore(engine)), contracts[0]).revision_number == 1
        with sqlite3.connect(tmp_path / "old.sqlite3") as raw:
            assert raw.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        engine.dispose()
