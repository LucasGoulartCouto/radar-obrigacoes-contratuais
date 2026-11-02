import sqlite3
from dataclasses import replace
from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from radar_contratos.application.documents import DocumentService
from radar_contratos.bootstrap import build_agenda_service, build_review_service
from radar_contratos.domain.agenda import CoverageState
from radar_contratos.domain.dates import TemporalStatus
from radar_contratos.domain.documents import DocumentInput, DocumentRole
from radar_contratos.domain.reviews import EvidenceInput, ManualDraft
from radar_contratos.errors import RadarError, StorageBusyError
from radar_contratos.infrastructure.persistence.documents import SqliteDocumentStore
from radar_contratos.infrastructure.persistence.models import Base, ConfirmedEventRow


def seed(
    service,
    engine,
    title="Contrato",
    end=date(2027, 6, 30),
    *,
    days=30,
    mode="events",
    unit="calendar_days",
):
    contract = service.register(title=title, actor="Rafael", request_id=str(uuid4()))
    raw = f"Termino: {end.isoformat()}.\nAviso: {days} dias corridos.".encode()
    documents = DocumentService(SqliteDocumentStore(engine))
    documents.submit(
        contract_id=contract.id,
        documents=(DocumentInput("base.txt", raw, DocumentRole.BASE),),
        expected_version=0,
        actor="Rafael",
        request_id=str(uuid4()),
        synthetic=True,
    )
    lines = raw.decode().splitlines()
    value = (
        ManualDraft(
            end_date=end,
            end_evidence=EvidenceInput(0, 1, 1, lines[0]),
            notice_days=days,
            notice_evidence=EvidenceInput(0, 2, 2, lines[1]),
            notice_unit=unit,
        )
        if mode == "events"
        else ManualDraft(mode=mode)
    )
    reviews = build_review_service(engine)
    analysis = reviews.register(
        contract_id=contract.id,
        expected_document_version=1,
        expected_analysis_version=0,
        draft=value,
        actor="Rafael",
        request_id=str(uuid4()),
        synthetic=True,
    )
    return contract, documents, reviews, analysis, value


def confirm(case, *, request=None):
    contract, _, reviews, analysis, _ = case
    return reviews.confirm(
        contract_id=contract.id,
        analysis_id=analysis["analysis_id"],
        expected_document_version=1,
        expected_analysis_version=1,
        expected_rule_version="AVISO_CORRIDOS_V1",
        actor="Marina (simulação)",
        request_id=request or str(uuid4()),
        acknowledged=True,
        empty_acknowledged=True,
    )


def test_mixed_portfolio_counts_every_contract_once_and_only_emits_current_reviewed_events(
    service, engine, extractions, classifier
):
    service.register(title="Sem documentos", actor="Rafael", request_id=str(uuid4()))
    document_only = service.register(
        title="Sem levantamento", actor="Rafael", request_id=str(uuid4())
    )
    DocumentService(SqliteDocumentStore(engine)).submit(
        contract_id=document_only.id,
        documents=(DocumentInput("base.txt", b"Documento", DocumentRole.BASE),),
        expected_version=0,
        actor="Rafael",
        request_id=str(uuid4()),
        synthetic=True,
    )
    classifier.failure = True
    attempt = extractions.request(
        contract_id=document_only.id,
        expected_document_version=1,
        expected_analysis_version=0,
        actor="Rafael",
        operation_id=str(uuid4()),
        synthetic=True,
    )
    extractions.execute(document_only.id, attempt["run_id"])
    seed(service, engine, "Pendente")
    seed(service, engine, "Bloqueado", unit="undefined")
    reviewed = seed(service, engine, "Com eventos")
    confirm(reviewed)
    empty = seed(service, engine, "Vazio conferido", mode="empty")
    confirm(empty)
    view = build_agenda_service(engine).read(date(2027, 5, 1))
    assert dict(view.coverage) == dict.fromkeys(CoverageState, 1)
    assert len(view.portfolio.contracts) == sum(count for _, count in view.coverage) == 6
    assert len(view.items) == 2
    assert {item.event.contract_id for item in view.items} == {reviewed[0].id}
    assert all(item.event.reviewer == "Marina (simulação)" for item in view.items)


def test_confirmed_notices_reach_all_four_temporal_groups_and_keep_equal_dates_separate(
    service, engine
):
    for title, end in [
        ("Ultrapassada", date(2027, 5, 30)),
        ("Hoje", date(2027, 5, 31)),
        ("Trinta dias", date(2027, 6, 30)),
        ("Depois", date(2027, 7, 1)),
    ]:
        confirm(seed(service, engine, title, end))
    same_date = seed(service, engine, "Prazo zero", date(2027, 5, 1), days=0)
    confirm(same_date)
    agenda = build_agenda_service(engine)
    view = agenda.read(date(2027, 5, 1), kinds=("non_renewal_notice",))
    assert {item.event.contract_title: item.temporal_status for item in view.items} == {
        "Ultrapassada": TemporalStatus.PAST,
        "Hoje": TemporalStatus.TODAY,
        "Trinta dias": TemporalStatus.SOON,
        "Depois": TemporalStatus.LATER,
        "Prazo zero": TemporalStatus.TODAY,
    }
    both = [
        item
        for item in agenda.read(date(2027, 5, 1)).items
        if item.event.contract_title == "Prazo zero"
    ]
    assert len(both) == 2
    assert {item.event.kind for item in both} == {"termination", "non_renewal_notice"}


@pytest.mark.parametrize("change", ["documents", "rule", "result", "remove"])
def test_changed_base_disappears_from_agenda_without_hiding_contract_or_deleting_history(
    service, engine, monkeypatch, change
):
    case = seed(service, engine)
    contract, documents, reviews, analysis, draft = case
    request = str(uuid4())
    receipt = confirm(case, request=request)
    if change in {"documents", "remove"}:
        documents.submit(
            contract_id=contract.id,
            documents=()
            if change == "remove"
            else (DocumentInput("nova.txt", b"Nova base", DocumentRole.BASE),),
            expected_version=1,
            actor="Rafael",
            request_id=str(uuid4()),
            synthetic=True,
            allow_empty=change == "remove",
        )
    elif change == "rule":
        monkeypatch.setattr("radar_contratos.domain.reviews.RULE_VERSION", "AVISO_CORRIDOS_V2")
    else:
        reviews.register(
            contract_id=contract.id,
            expected_document_version=1,
            expected_analysis_version=1,
            draft=replace(draft, notice_days=10),
            change_reason="Correção de exercício",
            actor="Rafael",
            request_id=str(uuid4()),
            synthetic=True,
        )
    assert confirm(case, request=request) == receipt
    view = build_agenda_service(engine).read(date(2027, 5, 1))
    assert not view.items
    assert len(view.portfolio.contracts) == 1
    assert view.portfolio.contracts[0].state not in {
        CoverageState.WITH_EVENTS,
        CoverageState.WITHOUT_EVENTS,
    }
    assert (
        reviews.get_analysis(contract.id, analysis["analysis_id"]).review_id == receipt["review_id"]
    )
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(ConfirmedEventRow)) == 2


def test_known_amendment_stays_blocked_after_removal(service, engine):
    contract, documents, _, _, _ = seed(service, engine)
    for version, role in [(1, DocumentRole.AMENDMENT), (2, DocumentRole.BASE)]:
        documents.submit(
            contract_id=contract.id,
            documents=(DocumentInput("base.txt", b"Base", role),),
            expected_version=version,
            actor="Rafael",
            request_id=str(uuid4()),
            synthetic=True,
        )
    view = build_agenda_service(engine).read(date(2027, 5, 1))
    assert view.portfolio.contracts[0].state is CoverageState.BLOCKED
    assert "Aditivo" in view.portfolio.contracts[0].detail
    assert not view.items


def test_read_is_single_metadata_select_and_reference_filters_never_write(service, engine):
    confirm(seed(service, engine))
    with Session(engine) as session:
        before = {
            table.name: session.scalar(select(func.count()).select_from(table))
            for table in Base.metadata.sorted_tables
        }
    statements = []

    def capture(_conn, _cursor, statement, _params, _context, _many):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", capture)
    try:
        view = build_agenda_service(engine).read(date(2027, 5, 1), statuses=())
    finally:
        event.remove(engine, "before_cursor_execute", capture)
    assert len(statements) == 1
    assert statements[0].lstrip().upper().startswith("SELECT")
    assert all(
        column not in statements[0] for column in ("original_bytes", "reference_text", "payload")
    )
    assert view.items == () and len(view.portfolio.events) == 2
    build_agenda_service(engine).read(date(2028, 1, 1))
    with Session(engine) as session:
        after = {
            table.name: session.scalar(select(func.count()).select_from(table))
            for table in Base.metadata.sorted_tables
        }
    assert before == after


def test_partial_confirmation_is_pending_and_no_partial_event_is_published(service, engine):
    confirm(seed(service, engine))
    with Session(engine) as session, session.begin():
        session.delete(session.scalars(select(ConfirmedEventRow)).first())
    view = build_agenda_service(engine).read(date(2027, 5, 1))
    assert view.portfolio.contracts[0].state is CoverageState.PENDING_REVIEW
    assert "inconsistente" in view.portfolio.contracts[0].detail
    assert not view.items


@pytest.mark.parametrize("code", [sqlite3.SQLITE_BUSY, sqlite3.SQLITE_ERROR])
def test_failed_read_reports_unavailable_instead_of_empty_or_reviewed_portfolio(engine, code):
    cause = sqlite3.OperationalError("Falha simulada com detalhe interno")
    cause.sqlite_errorcode = code

    def fail(_conn, _cursor, _statement, _params, _context, _many):
        raise OperationalError("SELECT", {}, cause)

    event.listen(engine, "before_cursor_execute", fail)
    try:
        expected = StorageBusyError if code == sqlite3.SQLITE_BUSY else RadarError
        with pytest.raises(expected) as captured:
            build_agenda_service(engine).read(date(2027, 5, 1))
        assert "detalhe interno" not in str(captured.value)
    finally:
        event.remove(engine, "before_cursor_execute", fail)
