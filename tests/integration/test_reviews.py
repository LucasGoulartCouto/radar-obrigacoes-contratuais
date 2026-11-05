from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.orm import Session

from radar_contratos.application.documents import DocumentService
from radar_contratos.application.reviews import ReviewService
from radar_contratos.domain.documents import DocumentInput, DocumentRole
from radar_contratos.domain.reviews import EvidenceInput, ManualDraft
from radar_contratos.errors import (
    IdempotencyConflictError,
    StaleRecordError,
    StorageBusyError,
    ValidationError,
)
from radar_contratos.infrastructure.persistence.documents import SqliteDocumentStore
from radar_contratos.infrastructure.persistence.models import (
    AnalysisRow,
    AuditRow,
    ConfirmedEventRow,
    OperationRow,
    ReviewRow,
)
from radar_contratos.infrastructure.persistence.reviews import SqliteReviewStore

SOURCE = b"Termino: 30/06/2027.\nAviso: 30 dias corridos antes do termino."


@pytest.fixture
def setup_case(service, engine):
    contract = service.register(title="Case conferência", actor="Rafael", request_id=str(uuid4()))
    documents = DocumentService(SqliteDocumentStore(engine))
    documents.submit(
        contract_id=contract.id,
        documents=(DocumentInput("base.txt", SOURCE, DocumentRole.BASE),),
        expected_version=0,
        actor="Rafael",
        request_id=str(uuid4()),
        synthetic=True,
    )
    return contract, documents, ReviewService(SqliteReviewStore(engine))


def draft():
    lines = SOURCE.decode().split("\n")
    return ManualDraft(
        end_date=date(2027, 6, 30),
        end_evidence=EvidenceInput(0, 1, 1, lines[0]),
        notice_days=30,
        notice_evidence=EvidenceInput(0, 2, 2, lines[1]),
    )


def register(case, *, version=0, document_version=1, value=None, request_id=None, reason=""):
    contract, _, reviews = case
    return reviews.register(
        contract_id=contract.id,
        expected_document_version=document_version,
        expected_analysis_version=version,
        draft=value or draft(),
        change_reason=reason,
        actor="Rafael",
        request_id=request_id or str(uuid4()),
        synthetic=True,
    )


def confirm(case, analysis, *, request_id=None, **kwargs):
    contract, _, reviews = case
    return reviews.confirm(
        contract_id=contract.id,
        analysis_id=analysis["analysis_id"],
        expected_document_version=analysis["document_version"],
        expected_analysis_version=analysis["analysis_version"],
        expected_rule_version="AVISO_CORRIDOS_V1",
        actor="Marina",
        request_id=request_id or str(uuid4()),
        acknowledged=True,
        **kwargs,
    )


def counts(engine):
    with Session(engine) as session:
        return tuple(
            session.scalar(select(func.count()).select_from(model))
            for model in (
                AnalysisRow,
                ReviewRow,
                ConfirmedEventRow,
                OperationRow,
                AuditRow,
            )
        )


def test_candidates_stay_unconfirmed_until_explicit_review(setup_case):
    contract, _, reviews = setup_case
    analysis = register(setup_case)
    assert reviews.current_events(contract.id) == []
    assert reviews.current_states()[contract.id] == "Revisão pendente"
    confirm(setup_case, analysis)
    assert {item["date"] for item in reviews.current_events(contract.id)} == {
        "2027-06-30",
        "2027-05-31",
    }
    assert reviews.current_states()[contract.id] == "Conferido com eventos"


def test_repeated_requests_and_equivalent_result_do_not_duplicate_or_invalidate(setup_case, engine):
    contract, _, reviews = setup_case
    request = str(uuid4())
    first = register(setup_case, request_id=request)
    assert register(setup_case, request_id=request) == first
    confirmation_request = str(uuid4())
    review = confirm(setup_case, first, request_id=confirmation_request)
    assert confirm(setup_case, first, request_id=confirmation_request) == review
    equivalent = register(setup_case, version=1)
    assert not equivalent["created"]
    assert equivalent["analysis_id"] == first["analysis_id"]
    assert len(reviews.current_events(contract.id)) == 2
    assert counts(engine)[:3] == (1, 1, 2)


def test_same_request_cannot_change_fields(setup_case):
    request = str(uuid4())
    register(setup_case, request_id=request)
    with pytest.raises(IdempotencyConflictError):
        register(setup_case, request_id=request, value=replace(draft(), notice_days=10))


def test_new_result_invalidates_current_events_but_preserves_history(setup_case):
    contract, _, reviews = setup_case
    first = register(setup_case)
    confirm(setup_case, first)
    with pytest.raises(ValidationError, match="motivo da correção"):
        register(setup_case, version=1, value=replace(draft(), notice_days=10))
    second = register(
        setup_case,
        version=1,
        value=replace(draft(), notice_days=10),
        reason="Correção manual para exercício de reconferência",
    )
    assert reviews.current_events(contract.id) == []
    assert reviews.get_analysis(contract.id, first["analysis_id"]).review_id is not None
    assert not reviews.get_analysis(contract.id, first["analysis_id"]).is_current
    with pytest.raises(StaleRecordError):
        confirm(setup_case, first)
    confirm(setup_case, second)
    assert len(reviews.list_history(contract.id)) == 2


def test_document_change_invalidates_and_cannot_be_confirmed_from_old_screen(setup_case):
    contract, documents, reviews = setup_case
    analysis = register(setup_case)
    original_request = str(uuid4())
    original_receipt = confirm(setup_case, analysis, request_id=original_request)
    documents.submit(
        contract_id=contract.id,
        documents=(DocumentInput("base.txt", SOURCE + b"\nNova linha.", DocumentRole.BASE),),
        expected_version=1,
        actor="Rafael",
        request_id=str(uuid4()),
        synthetic=True,
    )
    assert reviews.current_events(contract.id) == []
    assert reviews.get_analysis(contract.id) is None
    assert reviews.get_analysis(contract.id, analysis["analysis_id"]).review_id
    assert confirm(setup_case, analysis, request_id=original_request) == original_receipt
    assert reviews.current_events(contract.id) == []
    with pytest.raises(StaleRecordError):
        confirm(setup_case, analysis)


def test_changed_rule_invalidates_existing_review(setup_case, monkeypatch):
    from radar_contratos.domain import reviews as rules

    contract, _, reviews = setup_case
    analysis = register(setup_case)
    confirm(setup_case, analysis)
    monkeypatch.setattr(rules, "RULE_VERSION", "AVISO_CORRIDOS_V2")
    assert reviews.current_events(contract.id) == []
    assert not reviews.get_analysis(contract.id).is_current
    with pytest.raises(StaleRecordError):
        confirm(setup_case, analysis)


@pytest.mark.parametrize(
    "value",
    [
        replace(draft(), notice_unit="undefined"),
        ManualDraft(
            mode="blocked",
            blocker_reason="Conflito de datas",
            blocker_evidence=EvidenceInput(0, 1, 1, SOURCE.decode().split("\n")[0]),
        ),
    ],
)
def test_blocked_result_cannot_be_confirmed(setup_case, value):
    analysis = register(setup_case, value=value)
    with pytest.raises(ValidationError):
        confirm(setup_case, analysis)
    assert setup_case[2].current_events(setup_case[0].id) == []


def test_empty_requires_separate_declaration_and_is_not_a_failure(setup_case):
    analysis = register(setup_case, value=ManualDraft(mode="empty"))
    with pytest.raises(ValidationError):
        confirm(setup_case, analysis)
    confirm(setup_case, analysis, empty_acknowledged=True)
    assert setup_case[2].current_states()[setup_case[0].id] == "Conferido sem eventos no recorte"
    assert setup_case[2].current_events(setup_case[0].id) == []


def test_confirmation_failure_rolls_back_review_events_receipt_and_audit(setup_case, engine):
    analysis = register(setup_case)
    before = counts(engine)
    request = str(uuid4())

    def fail(_mapper, _connection, _target):
        raise RuntimeError("Falha simulada de histórico")

    event.listen(AuditRow, "before_insert", fail)
    try:
        with pytest.raises(RuntimeError):
            confirm(setup_case, analysis, request_id=request)
    finally:
        event.remove(AuditRow, "before_insert", fail)
    assert counts(engine) == before
    assert setup_case[2].current_events(setup_case[0].id) == []
    confirm(setup_case, analysis, request_id=request)
    assert counts(engine)[:3] == (1, 1, 2)


def test_competing_confirmations_create_one_review_and_two_events(setup_case, engine):
    analysis = register(setup_case)

    def attempt(_index):
        try:
            return confirm(setup_case, analysis)
        except StorageBusyError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, range(2)))
    assert any(result is not None for result in results)
    assert counts(engine)[:3] == (1, 1, 2)


def test_evidence_must_match_and_confirmation_cannot_cross_contracts(setup_case, service, engine):
    with pytest.raises(ValidationError):
        register(
            setup_case, value=replace(draft(), end_evidence=EvidenceInput(0, 1, 1, "Inventada"))
        )
    assert counts(engine)[:3] == (0, 0, 0)
    analysis = register(setup_case)
    other = service.register(title="Outro case", actor="Rafael", request_id=str(uuid4()))
    DocumentService(SqliteDocumentStore(engine)).submit(
        contract_id=other.id,
        documents=(DocumentInput("base.txt", SOURCE, DocumentRole.BASE),),
        expected_version=0,
        actor="Rafael",
        request_id=str(uuid4()),
        synthetic=True,
    )
    foreign_case = (other, setup_case[1], setup_case[2])
    with pytest.raises(StaleRecordError):
        confirm(foreign_case, analysis)


def test_known_amendment_blocks_even_after_its_removal(setup_case):
    contract, documents, reviews = setup_case
    documents.submit(
        contract_id=contract.id,
        documents=(DocumentInput("base.txt", SOURCE, DocumentRole.AMENDMENT),),
        expected_version=1,
        actor="Rafael",
        request_id=str(uuid4()),
        synthetic=True,
    )
    documents.submit(
        contract_id=contract.id,
        documents=(DocumentInput("base.txt", SOURCE, DocumentRole.BASE),),
        expected_version=2,
        actor="Rafael",
        request_id=str(uuid4()),
        synthetic=True,
    )
    analysis = register(setup_case, document_version=3)
    with pytest.raises(ValidationError):
        confirm(setup_case, analysis)
    assert reviews.current_states()[contract.id] == "Bloqueado: aditivo declarado"


def test_empty_document_revision_cannot_be_treated_as_analysis_without_events(setup_case):
    contract, documents, _reviews = setup_case
    documents.submit(
        contract_id=contract.id,
        documents=(),
        expected_version=1,
        actor="Rafael",
        request_id=str(uuid4()),
        synthetic=True,
        allow_empty=True,
    )
    with pytest.raises(ValidationError, match="Receba documentos"):
        register(setup_case, document_version=2, value=ManualDraft(mode="empty"))


def test_upgrade_from_documents_preserves_bytes_receipts_and_accepts_review(tmp_path):
    import hashlib
    import json

    from alembic import command
    from sqlalchemy import text

    from radar_contratos.application.contracts import ContractService
    from radar_contratos.infrastructure.persistence.contracts import SqliteContractStore
    from radar_contratos.infrastructure.persistence.database import (
        backup_database,
        initialize_database,
        make_engine,
        migration_config,
        require_current_schema,
    )

    engine = make_engine(tmp_path / "previous.sqlite3")
    cid, rid, request, upload = (str(uuid4()) for _ in range(4))
    reference = SOURCE.decode()
    receipt = {
        "request_id": request,
        "revision_id": rid,
        "revision_number": 1,
        "created_revision": True,
        "actor": "Rafael",
        "received_at_utc": "2026-11-01",
    }
    try:
        config = migration_config()
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "0002_documents")
            connection.execute(
                text(
                    "INSERT INTO contracts (id,title,record_version,document_version,"
                    "created_at_utc,updated_at_utc) VALUES "
                    "(:id,'Case preservado',1,1,'2026-11-01','2026-11-01')"
                ),
                {"id": cid},
            )
            connection.execute(
                text("INSERT INTO operations VALUES (:id,:fp,:cid,:response)"),
                {"id": request, "fp": "0" * 64, "cid": cid, "response": json.dumps(receipt)},
            )
            connection.execute(
                text(
                    "INSERT INTO document_revisions VALUES "
                    "(:id,:cid,1,:fp,:request,1,:size,'Rafael','2026-11-01')"
                ),
                {"id": rid, "cid": cid, "fp": "0" * 64, "request": request, "size": len(SOURCE)},
            )
            connection.execute(
                text(
                    "INSERT INTO document_uploads VALUES "
                    "(:id,:rid,:request,0,'base.txt','base',:raw,:sha,:ref,:sha,'TEXT_REFERENCE_V1')"
                ),
                {
                    "id": upload,
                    "rid": rid,
                    "request": request,
                    "raw": SOURCE,
                    "sha": hashlib.sha256(SOURCE).hexdigest(),
                    "ref": reference,
                },
            )
        backup_database(tmp_path / "previous.sqlite3", tmp_path / "before-review-upgrade.sqlite3")
        initialize_database(engine)
        initialize_database(engine)
        require_current_schema(engine)
        contract = ContractService(SqliteContractStore(engine)).list_contracts()[0]
        assert contract.analysis_version == 0
        documents = DocumentService(SqliteDocumentStore(engine))
        assert documents.get_documents(cid, rid, request)[0].original_bytes == SOURCE
        reviews = ReviewService(SqliteReviewStore(engine))
        case = (contract, documents, reviews)
        analysis = register(case)
        confirm(case, analysis)
        assert len(reviews.current_events(cid)) == 2
        restored_path = backup_database(
            tmp_path / "previous.sqlite3", tmp_path / "review-restored.sqlite3"
        )
        restored = make_engine(restored_path)
        try:
            assert len(ReviewService(SqliteReviewStore(restored)).current_events(cid)) == 2
            with Session(restored) as session:
                assert session.get(OperationRow, request).response == receipt
        finally:
            restored.dispose()
    finally:
        engine.dispose()
