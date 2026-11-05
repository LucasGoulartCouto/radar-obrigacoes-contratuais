from datetime import date
from pathlib import Path
from uuid import uuid4

from streamlit.testing.v1 import AppTest

from radar_contratos.application.documents import DocumentService
from radar_contratos.bootstrap import build_review_service
from radar_contratos.domain.dates import TemporalStatus
from radar_contratos.domain.documents import DocumentInput, DocumentRole
from radar_contratos.domain.reviews import EvidenceInput, ManualDraft
from radar_contratos.infrastructure.persistence.documents import SqliteDocumentStore

APP = Path(__file__).parents[2] / "src/radar_contratos/ui/app.py"
SOURCE = b"Termino: 30/06/2027.\nAviso: 30 dias corridos antes do termino."


def seed(service, engine):
    contract = service.register(
        title="Conferido para agenda", actor="Rafael", request_id=str(uuid4())
    )
    service.register(title="Pendente sem documentos", actor="Rafael", request_id=str(uuid4()))
    documents = DocumentService(SqliteDocumentStore(engine))
    documents.submit(
        contract_id=contract.id,
        documents=(DocumentInput("base.txt", SOURCE, DocumentRole.BASE),),
        expected_version=0,
        actor="Rafael",
        request_id=str(uuid4()),
        synthetic=True,
    )
    reviews = build_review_service(engine)
    analysis = reviews.register(
        contract_id=contract.id,
        expected_document_version=1,
        expected_analysis_version=0,
        draft=ManualDraft(
            end_date=date(2027, 6, 30),
            end_evidence=EvidenceInput(0, 1, 1, SOURCE.decode().splitlines()[0]),
            notice_days=30,
            notice_evidence=EvidenceInput(0, 2, 2, SOURCE.decode().splitlines()[1]),
        ),
        actor="Rafael",
        request_id=str(uuid4()),
        synthetic=True,
    )
    reviews.confirm(
        contract_id=contract.id,
        analysis_id=analysis["analysis_id"],
        expected_document_version=1,
        expected_analysis_version=1,
        expected_rule_version="AVISO_CORRIDOS_V1",
        actor="Marina (simulação)",
        request_id=str(uuid4()),
        acknowledged=True,
    )
    return contract, documents, reviews


def widget(elements, label):
    return next(item for item in elements if item.label == label)


def table(app, column):
    return next(item.value for item in app.dataframe if column in item.value.columns)


def test_agenda_shows_current_notice_evidence_and_all_pending_contracts(
    engine, service, tmp_path, monkeypatch
):
    monkeypatch.setenv("RADAR_DATA_DIR", str(tmp_path))
    seed(service, engine)
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    events = table(app, "Dias até a data")
    assert events["Evento"].tolist() == ["Aviso de não renovação"]
    assert events["Situação"].tolist() == ["Próximos 30 dias"]
    assert events["Dias até a data"].tolist() == [30]
    assert len(table(app, "Próximo passo")) == 2
    assert widget(app.metric, "Aguardando documentos").value == "1"
    assert widget(app.metric, "Conferido com eventos").value == "1"
    assert any("carteira não está totalmente conferida" in item.value for item in app.warning)
    assert any("Aviso: 30 dias" in item.value for item in app.code)
    assert any("menos 30 dias corridos = 31/05/2027" in item.value for item in app.text)


def test_kind_and_temporal_filters_change_view_but_reference_never_changes_confirmation(
    engine, service, tmp_path, monkeypatch
):
    monkeypatch.setenv("RADAR_DATA_DIR", str(tmp_path))
    contract, _, reviews = seed(service, engine)
    before = reviews.get_analysis(contract.id)
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    widget(app.multiselect, "Situações de prazo").set_value(list(TemporalStatus)).run()
    widget(app.selectbox, "Tipo de evento na agenda").set_value("termination").run()
    assert not app.exception
    assert table(app, "Dias até a data")["Situação"].tolist() == ["Depois do horizonte"]
    widget(app.date_input, "Data de referência da simulação").set_value(date(2027, 6, 30)).run()
    assert not app.exception
    assert table(app, "Dias até a data")["Situação"].tolist() == ["Hoje"]
    assert reviews.get_analysis(contract.id) == before
    reopened = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not reopened.exception
    assert widget(reopened.date_input, "Data de referência da simulação").value == date(2027, 5, 1)
    assert reviews.get_analysis(contract.id) == before


def test_empty_filters_do_not_remove_coverage_or_hide_pending_warning(
    engine, service, tmp_path, monkeypatch
):
    monkeypatch.setenv("RADAR_DATA_DIR", str(tmp_path))
    seed(service, engine)
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    widget(app.multiselect, "Situações de prazo").set_value([]).run()
    assert not app.exception
    assert not any("Dias até a data" in item.value.columns for item in app.dataframe)
    assert len(table(app, "Próximo passo")) == 2
    assert any("Nenhum evento nos filtros" in item.value for item in app.info)
    assert widget(app.metric, "Aguardando documentos").value == "1"


def test_missing_reference_keeps_portfolio_visible_without_inventing_a_date(
    engine, service, tmp_path, monkeypatch
):
    monkeypatch.setenv("RADAR_DATA_DIR", str(tmp_path))
    seed(service, engine)
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    widget(app.date_input, "Data de referência da simulação").set_value(None).run()
    assert not app.exception
    assert len(table(app, "Próximo passo")) == 2
    assert any("Informe a data de referência" in item.value for item in app.warning)
    assert not any("Dias até a data" in item.value.columns for item in app.dataframe)


def test_refresh_removes_stale_event_keeps_contract_and_previous_review_visible(
    engine, service, tmp_path, monkeypatch
):
    monkeypatch.setenv("RADAR_DATA_DIR", str(tmp_path))
    contract, documents, reviews = seed(service, engine)
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    old = reviews.get_analysis(contract.id)
    documents.submit(
        contract_id=contract.id,
        documents=(DocumentInput("nova.txt", SOURCE + b"\nNova base.", DocumentRole.BASE),),
        expected_version=1,
        actor="Rafael",
        request_id=str(uuid4()),
        synthetic=True,
    )
    widget(app.button, "Atualizar agenda").click().run()
    assert not app.exception
    assert not any("Dias até a data" in item.value.columns for item in app.dataframe)
    coverage = table(app, "Próximo passo")
    assert coverage.loc[coverage["Contrato"] == contract.title, "Situação"].tolist() == [
        "Aguardando análise"
    ]
    assert reviews.get_analysis(contract.id, old.id).review_id == old.review_id


def test_source_warns_if_base_changes_after_portfolio_read(engine, service, tmp_path, monkeypatch):
    from radar_contratos.application.reviews import ReviewService

    monkeypatch.setenv("RADAR_DATA_DIR", str(tmp_path))
    contract, documents, _ = seed(service, engine)
    original = ReviewService.get_analysis
    changed = False

    def change_before_source(self, contract_id, analysis_id=None):
        nonlocal changed
        if analysis_id is not None and not changed:
            changed = True
            documents.submit(
                contract_id=contract.id,
                documents=(DocumentInput("nova.txt", b"Nova base", DocumentRole.BASE),),
                expected_version=1,
                actor="Rafael",
                request_id=str(uuid4()),
                synthetic=True,
            )
        return original(self, contract_id, analysis_id)

    monkeypatch.setattr(ReviewService, "get_analysis", change_before_source)
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    assert any("A base deste evento mudou" in item.value for item in app.warning)


def test_failed_portfolio_read_shows_error_without_zero_coverage(
    engine, service, tmp_path, monkeypatch
):
    from radar_contratos.errors import RadarError
    from radar_contratos.infrastructure.persistence.agenda import SqliteAgendaStore

    monkeypatch.setenv("RADAR_DATA_DIR", str(tmp_path))
    seed(service, engine)

    def fail(_self):
        raise RadarError("Não foi possível consultar a carteira. Nenhuma cobertura foi calculada.")

    monkeypatch.setattr(SqliteAgendaStore, "read_portfolio", fail)
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    assert any("Nenhuma cobertura foi calculada" in item.value for item in app.error)
    assert not app.metric
    assert any(item.label == "Contrato para editar o nome" for item in app.selectbox)
