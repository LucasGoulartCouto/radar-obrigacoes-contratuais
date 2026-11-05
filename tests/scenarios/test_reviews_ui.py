from datetime import date
from pathlib import Path
from uuid import uuid4

from streamlit.testing.v1 import AppTest

from radar_contratos.application.documents import DocumentService
from radar_contratos.application.reviews import ReviewService
from radar_contratos.domain.documents import DocumentInput, DocumentRole
from radar_contratos.infrastructure.persistence.documents import SqliteDocumentStore
from radar_contratos.infrastructure.persistence.reviews import SqliteReviewStore

APP = Path(__file__).parents[2] / "src/radar_contratos/ui/app.py"
SOURCE = b"Termino: 30/06/2027.\nAviso: 30 dias corridos antes do termino."


def seed(service, engine):
    contract = service.register(
        title="Case da conferência", actor="Rafael", request_id=str(uuid4())
    )
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


def widget(elements, label):
    return next(item for item in elements if item.label == label)


def save_valid(app):
    widget(app.date_input, "Término explícito do ciclo").set_value(date(2027, 6, 30))
    widget(app.checkbox, "Há aviso de não renovação vinculado ao ciclo informado.").check().run()
    widget(app.number_input, "Antecedência informada").set_value(30)
    widget(app.slider, "Linhas — Trecho do aviso").set_value((2, 2))
    widget(app.checkbox, "Este levantamento usa apenas os documentos sintéticos do case.").check()
    widget(app.button, "Salvar levantamento (não confirma)").click().run()


def test_manual_candidates_require_separate_review_and_survive_reload(
    engine, service, tmp_path, monkeypatch
):
    monkeypatch.setenv("RADAR_DATA_DIR", str(tmp_path))
    contract, _, reviews = seed(service, engine)
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    save_valid(app)
    assert not app.exception
    assert reviews.current_events(contract.id) == []
    widget(app.button, "Confirmar conferência").click().run()
    assert app.error
    widget(app.checkbox, "Conferi os campos, as evidências e a cobertura desta revisão.").check()
    widget(app.button, "Confirmar conferência").click().run()
    assert not app.exception
    assert len(reviews.current_events(contract.id)) == 2
    reopened = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not reopened.exception
    assert any("Conferência registrada para esta base" in item.value for item in reopened.success)


def test_changed_document_requires_refresh_and_preserves_visible_history(
    engine, service, tmp_path, monkeypatch
):
    monkeypatch.setenv("RADAR_DATA_DIR", str(tmp_path))
    contract, documents, reviews = seed(service, engine)
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    save_valid(app)
    widget(app.checkbox, "Conferi os campos, as evidências e a cobertura desta revisão.").check()
    widget(app.button, "Confirmar conferência").click().run()
    documents.submit(
        contract_id=contract.id,
        documents=(DocumentInput("base.txt", SOURCE + b"\nMudanca.", DocumentRole.BASE),),
        expected_version=1,
        actor="Marina",
        request_id=str(uuid4()),
        synthetic=True,
    )
    app.run()
    assert app.error
    widget(app.button, "Atualizar documentos").click().run()
    assert not app.exception
    assert not app.error
    assert reviews.current_events(contract.id) == []
    assert any("Registro histórico" in item.value for item in app.warning)
    assert any("Nenhum evento confirmado válido" in item.value for item in app.info)


def test_empty_result_needs_explicit_empty_review(engine, service, tmp_path, monkeypatch):
    monkeypatch.setenv("RADAR_DATA_DIR", str(tmp_path))
    contract, _, reviews = seed(service, engine)
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    widget(app.radio, "Resultado do levantamento").set_value("empty").run()
    widget(app.checkbox, "Este levantamento usa apenas os documentos sintéticos do case.").check()
    widget(app.button, "Salvar levantamento (não confirma)").click().run()
    assert not app.exception
    widget(app.checkbox, "Conferi os campos, as evidências e a cobertura desta revisão.").check()
    widget(app.button, "Confirmar conferência").click().run()
    assert app.error
    widget(
        app.checkbox, "Conferi explicitamente que não há eventos deste recorte no texto completo."
    ).check()
    widget(app.button, "Confirmar conferência").click().run()
    assert not app.exception
    assert reviews.current_states()[contract.id] == "Conferido sem eventos no recorte"
    assert any(item.value == "Conferido sem eventos no recorte." for item in app.info)
